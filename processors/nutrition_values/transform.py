"""
Transform nutrition values data with PySpark to match MCD schema
Source: nutritional-values-for-common-foods-and-products
"""
from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, trim, lower, when, lit, udf, regexp_replace, round as spark_round
)
from pyspark.sql.types import StringType
import uuid
from utils.transform import load_raw_data, ensure_columns
from utils.uuid_utils import food_uuid_udf

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

from pyspark.sql.types import StringType as _ST
from pyspark.sql.functions import udf as _udf
_map_category_udf = _udf(_map_category, _ST())(df: DataFrame) -> DataFrame:
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
        "food_category", "food_group", "group",
        "fiber_g", "dietary_fiber", "fiber", "fibre",
        "sugar_g", "sugars", "sugar", "total_sugars",
        "sodium_mg", "sodium", "salt",
        "cholesterol_mg", "cholesterol",
    ])

    df_mapped = df_with_name.select(
        food_uuid_udf(col("name"), lit(None)).alias("ingredients_id"),
        col("name"),

        # Calories
        when(col("calories").isNotNull(), spark_round(col("calories"), 2))
        .when(col("energy_kcal").isNotNull(), spark_round(col("energy_kcal"), 2))
        .when(col("energy").isNotNull(), spark_round(col("energy"), 2))
        .when(col("calorie").isNotNull(), spark_round(col("calorie"), 2))
        .otherwise(lit(0.0))
        .alias("calories_g"),

        # Protein
        when(col("protein_g").isNotNull(), spark_round(col("protein_g"), 2))
        .when(col("protein").isNotNull(), spark_round(col("protein"), 2))
        .when(col("proteins").isNotNull(), spark_round(col("proteins"), 2))
        .otherwise(lit(0.0))
        .alias("protein_g"),

        # Carbohydrates
        when(col("carbohydrate_g").isNotNull(), spark_round(col("carbohydrate_g"), 2))
        .when(col("carbs_g").isNotNull(), spark_round(col("carbs_g"), 2))
        .when(col("carbohydrates").isNotNull(), spark_round(col("carbohydrates"), 2))
        .when(col("carbs").isNotNull(), spark_round(col("carbs"), 2))
        .when(col("total_carbohydrate").isNotNull(), spark_round(col("total_carbohydrate"), 2))
        .otherwise(lit(0.0))
        .alias("carbs_g"),

        # Fat
        when(col("fat_g").isNotNull(), spark_round(col("fat_g"), 2))
        .when(col("total_fat").isNotNull(), spark_round(col("total_fat"), 2))
        .when(col("fat").isNotNull(), spark_round(col("fat"), 2))
        .when(col("lipid").isNotNull(), spark_round(col("lipid"), 2))
        .otherwise(lit(0.0))
        .alias("fat_g"),

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
        when(col("fiber_g").isNotNull(), spark_round(col("fiber_g"), 2))
        .when(col("dietary_fiber").isNotNull(), spark_round(col("dietary_fiber"), 2))
        .when(col("fiber").isNotNull(), spark_round(col("fiber"), 2))
        .when(col("fibre").isNotNull(), spark_round(col("fibre"), 2))
        .otherwise(lit(0.0))
        .alias("fiber_g"),

        # Sugar
        when(col("sugar_g").isNotNull(), spark_round(col("sugar_g"), 2))
        .when(col("sugars").isNotNull(), spark_round(col("sugars"), 2))
        .when(col("sugar").isNotNull(), spark_round(col("sugar"), 2))
        .when(col("total_sugars").isNotNull(), spark_round(col("total_sugars"), 2))
        .otherwise(lit(0.0))
        .alias("sugar_g"),

        # Sodium
        when(col("sodium_mg").isNotNull(), spark_round(col("sodium_mg"), 2))
        .when(col("sodium").isNotNull(), spark_round(col("sodium"), 2))
        .when(col("salt").isNotNull(), spark_round(col("salt") * 400, 2))
        .otherwise(lit(0.0))
        .alias("sodium_mg"),

        # Cholesterol
        when(col("cholesterol_mg").isNotNull(), spark_round(col("cholesterol_mg"), 2))
        .when(col("cholesterol").isNotNull(), spark_round(col("cholesterol"), 2))
        .otherwise(lit(0.0))
        .alias("cholesterol_mg")
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
    df = df.filter(
        (col("calories_g") >= 0) & (col("calories_g") <= 900)
    )
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
            df_transformed.select("calories_100g", "protein_100g", "carbs_100g", "fat_100g").describe().show()
    
    finally:
        stop_spark()
