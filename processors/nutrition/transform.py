"""
Transform nutrition data with PySpark to match MCD schema
"""
from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, trim, lower, when, lit, udf, regexp_replace, round as spark_round,
    coalesce, least, substring
)
from pyspark.sql.types import StringType, DoubleType

# Numeric pattern: optional leading minus, digits, optional decimal part
_NUM_RE = r'^-?\d+(\.\d+)?$'
# All numeric columns are DECIMAL(4,1) → max 999.9
_MAX_DECIMAL_4_1 = 999.9


def _tc(c_name: str):
    """Safe cast to double, rounded to 2 dp; returns NULL when value is non-numeric."""
    return spark_round(
        when(col(c_name).rlike(_NUM_RE), col(c_name).cast(DoubleType())).otherwise(lit(None)),
        2
    )


def _cap(expr):
    """Clamp value to DECIMAL(4,1) max (999.9)."""
    return least(expr, lit(_MAX_DECIMAL_4_1))
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
_map_category_udf = _udf(_map_category, _ST())


def map_to_mcd_schema(df: DataFrame) -> DataFrame:
    """
    Map source columns to MCD INGREDIENTS schema

    Schema: ingredients_id, name, calories_g, protein_g, carbs_g,
            fat_g, nutriscore, category, fiber_g, sugar_g,
            sodium_mg, cholesterol_mg
    """
    # Normalize column names (lowercase, remove spaces)
    for old_col in df.columns:
        new_col = old_col.lower().replace(" ", "_").replace("(", "").replace(")", "")
        df = df.withColumnRenamed(old_col, new_col)
    
    # Map to MCD schema (adjust based on actual CSV columns)
    # First create name and brand columns, then use them for deterministic UUID
    df_with_name = df.withColumn(
        "name",
        when(col("food_item").isNotNull(), trim(col("food_item")))
        .otherwise(lit("Unknown"))
    )

    # Ensure all fallback column names referenced in WHEN chains exist.
    # PySpark 4.x validates every col() reference at plan-compilation time,
    # even inside unreachable WHEN branches — missing columns cause AnalysisException.
    df_with_name = ensure_columns(df_with_name, [
        "protein", "carbohydrate_g", "carbs_g", "carbohydrates",
        "total_fat", "dietary_fiber", "sugar_g", "sugars",
        "sodium", "cholesterol", "food_category",
    ])

    df_mapped = df_with_name.select(
        food_uuid_udf(substring(col("name"), 1, 50), lit(None)).alias("ingredients_id"),
        substring(col("name"), 1, 50).alias("name"),

        _cap(coalesce(_tc("calories_kcal"), lit(0.0))).alias("calories_g"),

        _cap(coalesce(_tc("protein_g"), _tc("protein"), lit(0.0))).alias("protein_g"),

        _cap(coalesce(
            _tc("carbohydrates_g"), _tc("carbohydrate_g"),
            _tc("carbs_g"), _tc("carbohydrates"), lit(0.0)
        )).alias("carbs_g"),

        _cap(coalesce(_tc("fat_g"), _tc("total_fat"), lit(0.0))).alias("fat_g"),

        lit(None).cast(StringType()).alias("nutriscore"),

        _map_category_udf(
            when(col("category").isNotNull(), col("category"))
            .when(col("food_category").isNotNull(), col("food_category"))
            .otherwise(lit(None))
        ).alias("category"),

        _cap(coalesce(_tc("fiber_g"), _tc("dietary_fiber"), lit(0.0))).alias("fiber_g"),

        _cap(coalesce(_tc("sugars_g"), _tc("sugar_g"), _tc("sugars"), lit(0.0))).alias("sugar_g"),

        _cap(coalesce(_tc("sodium_mg"), _tc("sodium"), lit(0.0))).alias("sodium_mg"),

        _cap(coalesce(_tc("cholesterol_mg"), _tc("cholesterol"), lit(0.0))).alias("cholesterol_mg"),
    )

    return df_mapped

def clean_and_validate(df: DataFrame) -> DataFrame:
    """Clean and validate data"""
    df_clean = df.dropDuplicates(["name"])
    df_clean = df_clean.filter(
        (col("name").isNotNull()) &
        (trim(col("name")) != "") &
        (lower(col("name")) != "unknown")
    )
    df_clean = df_clean.filter(
        (col("calories_g") >= 0) &
        (col("protein_g") >= 0) &
        (col("carbs_g") >= 0) &
        (col("fat_g") >= 0)
    )
    return df_clean

def transform_nutrition(spark, csv_path: str) -> DataFrame:
    """Complete transformation pipeline to MCD schema"""
    print("⏳ Transforming nutrition data...")
    
    # Check if file exists
    from pathlib import Path
    if not Path(csv_path).exists():
        print(f"❌ FAILED: File not found - {csv_path}")
        raise FileNotFoundError(f"Raw data file not found: {csv_path}")
    
    df_raw = load_raw_data(spark, csv_path)
    df_mapped = map_to_mcd_schema(df_raw)
    df_clean = clean_and_validate(df_mapped)
    
    print("✅ Transform completed")
    return df_clean

if __name__ == "__main__":
    from spark.session import get_spark, stop_spark
    from processors.nutrition.config import LOCAL_FILE
    
    spark = get_spark("Transform_Nutrition")
    
    try:
        df_transformed = transform_nutrition(spark, str(LOCAL_FILE))
        
        print("\n" + "="*60)
        print("📋 TRANSFORMED DATA PREVIEW")
        print("="*60)
        df_transformed.show(5, truncate=False)
        
        print(f"\n📈 Statistics:")
        print(f"Total: {df_transformed.count()} foods")
        print(f"\nCategories:")
        df_transformed.groupBy("category_ref").count().show()
        
    finally:
        stop_spark()
