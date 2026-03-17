import traceback
from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, trim, when, lit, udf, round as spark_round,
    coalesce, least, substring, regexp_extract
)
from pyspark.sql.types import StringType, DoubleType
from utils.transform import load_raw_data, ensure_columns
from utils.uuid_utils import food_uuid_udf

# All numeric columns are DECIMAL(4,1) → max 999.9
_MAX_DECIMAL_4_1 = 999.9


def _tc(c_name: str):
    """
    Extract the leading number from a value that may have an embedded unit
    (e.g. "72g", "9.00 mg") and cast to double.  Returns NULL on empty/null.
    """
    extracted = regexp_extract(col(c_name), r'(-?\d+\.?\d*)', 1)
    return spark_round(
        when(extracted != lit(""), extracted.cast(DoubleType())).otherwise(lit(None)),
        2
    )


def _cap(expr):
    """Clamp value to DECIMAL(4,1) max (999.9)."""
    return least(expr, lit(_MAX_DECIMAL_4_1))

# Maps raw category strings to category_enum values
def _map_category(raw_cat):
    if not raw_cat:
        return "OTHER"
    c = raw_cat.lower().strip()
    if any(k in c for k in ("vegetable", "veggie", "veg")):
        return "VEGETABLE"
    if any(k in c for k in ("fruit",)):
        return "FRUIT"
    if any(k in c for k in ("meat", "beef", "pork", "chicken", "poultry", "lamb", "fish", "seafood")):
        return "MEAT"
    if any(k in c for k in ("dairy", "milk", "cheese", "yogurt", "cream")):
        return "DAIRY"
    if any(k in c for k in ("grain", "bread", "pasta", "rice", "cereal", "flour")):
        return "GRAIN"
    if any(k in c for k in ("beverage", "drink", "juice", "water", "alcohol", "soda")):
        return "BEVERAGE"
    if any(k in c for k in ("snack", "candy", "chocolate", "chip", "dessert", "sweet", "biscuit")):
        return "SNACK"
    return "OTHER"

_map_category_udf = udf(_map_category, StringType())

def map_to_mcd_schema(df: DataFrame) -> DataFrame:
    """
    Map source columns to MCD INGREDIENTS schema

    Schema: ingredients_id, name, calories_g, protein_g, carbs_g,
            fat_g, nutriscore, category, fiber_g, sugar_g,
            sodium_mg, cholesterol_mg
    """
    # Normalize column names (lowercase, remove spaces/parentheses)
    for old_col in df.columns:
        new_col = old_col.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
        df = df.withColumnRenamed(old_col, new_col)
    
    # Map to MCD schema with flexible column matching
    # First create name and brand columns, then use them for deterministic UUID
    df_with_name = df.withColumn(
        "name",
        when(col("name").isNotNull(), trim(col("name")))
        .otherwise(lit("Unknown"))
    )

    # Ensure all fallback column names referenced in WHEN chains exist.
    # PySpark 4.x validates every col() reference at plan-compilation time,
    # even inside unreachable WHEN branches — missing columns cause AnalysisException.
    df_with_name = ensure_columns(df_with_name, [
        "calories", "energy_kcal", "energy", "calorie",
        "protein_g", "protein", "proteins",
        "carbohydrate_g", "carbs_g", "carbohydrates", "carbs", "total_carbohydrate",
        "fat_g", "total_fat", "fat", "lipid",
        "category", "food_category", "food_group", "group",
        "fiber_g", "dietary_fiber", "fiber", "fibre",
        "sugar_g", "sugars", "sugar", "total_sugars",
        "sodium_mg", "sodium", "salt",
        "cholesterol_mg", "cholesterol",
    ])

    df_mapped = df_with_name.select(
        food_uuid_udf(substring(col("name"), 1, 50), lit(None)).alias("ingredients_id"),
        substring(col("name"), 1, 50).alias("name"),

        # Calories
        _cap(coalesce(
            _tc("calories"), _tc("energy_kcal"), _tc("energy"), _tc("calorie"), lit(0.0)
        )).alias("calories_g"),

        # Protein
        _cap(coalesce(
            _tc("protein_g"), _tc("protein"), _tc("proteins"), lit(0.0)
        )).alias("protein_g"),

        # Carbohydrates
        _cap(coalesce(
            _tc("carbohydrate_g"), _tc("carbs_g"), _tc("carbohydrates"),
            _tc("carbs"), _tc("total_carbohydrate"), lit(0.0)
        )).alias("carbs_g"),

        # Fat
        _cap(coalesce(
            _tc("fat_g"), _tc("total_fat"), _tc("fat"), _tc("lipid"), lit(0.0)
        )).alias("fat_g"),

        # nutriscore: NULL (nutriscore_enum: A-E)
        lit(None).cast(StringType()).alias("nutriscore"),

        # category mapped to category_enum
        _map_category_udf(
            when(col("category").isNotNull(), col("category"))
            .when(col("food_category").isNotNull(), col("food_category"))
            .when(col("food_group").isNotNull(), col("food_group"))
            .when(col("group").isNotNull(), col("group"))
            .otherwise(lit(None))
        ).alias("category"),

        # Fiber
        _cap(coalesce(
            _tc("fiber_g"), _tc("dietary_fiber"), _tc("fiber"), _tc("fibre"), lit(0.0)
        )).alias("fiber_g"),

        # Sugar
        _cap(coalesce(
            _tc("sugar_g"), _tc("sugars"), _tc("sugar"), _tc("total_sugars"), lit(0.0)
        )).alias("sugar_g"),

        # Sodium — convert salt (g) → sodium (mg) by × 400 if needed
        _cap(coalesce(
            _tc("sodium_mg"), _tc("sodium"),
            when(_tc("salt").isNotNull(),
                 spark_round(_tc("salt") * lit(400.0), 2)),
            lit(0.0)
        )).alias("sodium_mg"),

        # Cholesterol
        _cap(coalesce(
            _tc("cholesterol_mg"), _tc("cholesterol"), lit(0.0)
        )).alias("cholesterol_mg"),
    )

    return df_mapped

def clean_data(df: DataFrame) -> DataFrame:
    """Clean and validate transformed data"""
    df = df.filter(
        (col("name").isNotNull()) &
        (trim(col("name")) != "") &
        (col("name") != "Unknown")
    )
    df = df.dropDuplicates(["name"])
    return df

def transform_nutrition_values(spark, csv_path: str) -> DataFrame:
    """
    Complete transformation pipeline for nutritional values
    
    Args:
        spark: SparkSession
        csv_path: Path to raw CSV file
        
    Returns:
        Transformed DataFrame matching MCD FOOD schema
    """
    print("⏳ Transforming nutrition values data...")
    
    try:
        # 1. Load raw data
        df_raw = load_raw_data(spark, csv_path)
        
        # 2. Map to MCD schema
        df_mapped = map_to_mcd_schema(df_raw)
        
        # 3. Clean data
        df_clean = clean_data(df_mapped)
        
        print("✅ Transform completed")
        return df_clean
        
    except Exception as e:
        from utils.logger import get_logger as _gl
        _gl("processors.nutrition_values.pipeline").error(f"transform_nutrition_values failed: {e}\n{traceback.format_exc()}")
        print(f"❌ FAILED: Transformation error - {e}")
        return None

if __name__ == "__main__":
    from spark.session import get_spark, stop_spark
    from processors.nutrition_values.config import LOCAL_FILE
    
    spark = get_spark("Transform_Nutrition_Values")
    
    try:
        df_transformed = transform_nutrition_values(spark, str(LOCAL_FILE))
        
        if df_transformed:
            print("\n" + "=" * 60)
            print("🎉 TRANSFORMATION COMPLETED")
            print("=" * 60)
            
            # Show schema
            print("\n📋 Schema:")
            df_transformed.printSchema()
            
            # Show stats
            print("\n📈 Statistics:")
            df_transformed.select("calories_g", "protein_g", "carbs_g", "fat_g").describe().show()
    
    finally:
        stop_spark()
