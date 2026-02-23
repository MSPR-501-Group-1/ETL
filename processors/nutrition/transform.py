"""
Transform nutrition data with PySpark to match MCD schema
"""
from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, trim, lower, when, lit, udf, regexp_replace, round as spark_round
)
from pyspark.sql.types import StringType
import uuid

def generate_uuid():
    """Generate UUID v4"""
    return str(uuid.uuid4())

uuid_udf = udf(generate_uuid, StringType())

def load_raw_data(spark, csv_path: str) -> DataFrame:
    """Load raw CSV data with Spark"""
    print(f"📖 Loading data from: {csv_path}")
    df = spark.read.csv(csv_path, header=True, inferSchema=True)
    print(f"✅ {df.count()} rows loaded")
    return df

def map_to_mcd_schema(df: DataFrame) -> DataFrame:
    """
    Map source columns to MCD FOOD schema
    
    MCD Schema: food_id, name, brand, calories_100g, protein_100g, carbs_100g,
                fat_100g, nutriscore, category_ref, fiber_g, sugar_g, 
                sodium_mg, cholesterol_mg
    """
    print("🔄 Mapping to MCD schema...")
    
    # Show original columns for debugging
    print(f"   Original columns: {df.columns}")
    
    # Normalize column names (lowercase, remove spaces)
    for old_col in df.columns:
        new_col = old_col.lower().replace(" ", "_").replace("(", "").replace(")", "")
        df = df.withColumnRenamed(old_col, new_col)
    
    # Map to MCD schema (adjust based on actual CSV columns)
    df_mapped = df.select(
        uuid_udf().alias("food_id"),
        
        # Name (usually 'food' or 'name' column)
        when(col("food").isNotNull(), trim(col("food")))
        .when(col("name").isNotNull(), trim(col("name")))
        .otherwise(lit("Unknown"))
        .alias("name"),
        
        # Brand (often not in dataset)
        lit(None).cast(StringType()).alias("brand"),
        
        # Nutritional values per 100g
        when(col("calories").isNotNull(), spark_round(col("calories"), 2))
        .otherwise(lit(0.0))
        .alias("calories_100g"),
        
        when(col("protein_g").isNotNull(), spark_round(col("protein_g"), 2))
        .when(col("protein").isNotNull(), spark_round(col("protein"), 2))
        .otherwise(lit(0.0))
        .alias("protein_100g"),
        
        when(col("carbohydrate_g").isNotNull(), spark_round(col("carbohydrate_g"), 2))
        .when(col("carbs_g").isNotNull(), spark_round(col("carbs_g"), 2))
        .when(col("carbohydrates").isNotNull(), spark_round(col("carbohydrates"), 2))
        .otherwise(lit(0.0))
        .alias("carbs_100g"),
        
        when(col("fat_g").isNotNull(), spark_round(col("fat_g"), 2))
        .when(col("total_fat").isNotNull(), spark_round(col("total_fat"), 2))
        .otherwise(lit(0.0))
        .alias("fat_100g"),
        
        # Nutriscore (not in most datasets)
        lit(None).cast(StringType()).alias("nutriscore"),
        
        # Category
        when(col("category").isNotNull(), lower(trim(col("category"))))
        .when(col("food_category").isNotNull(), lower(trim(col("food_category"))))
        .otherwise(lit("general"))
        .alias("category_ref"),
        
        # Additional nutrients
        when(col("fiber_g").isNotNull(), spark_round(col("fiber_g"), 2))
        .when(col("dietary_fiber").isNotNull(), spark_round(col("dietary_fiber"), 2))
        .otherwise(lit(0.0))
        .alias("fiber_g"),
        
        when(col("sugar_g").isNotNull(), spark_round(col("sugar_g"), 2))
        .when(col("sugars").isNotNull(), spark_round(col("sugars"), 2))
        .otherwise(lit(0.0))
        .alias("sugar_g"),
        
        when(col("sodium_mg").isNotNull(), spark_round(col("sodium_mg"), 2))
        .when(col("sodium").isNotNull(), spark_round(col("sodium"), 2))
        .otherwise(lit(0.0))
        .alias("sodium_mg"),
        
        when(col("cholesterol_mg").isNotNull(), spark_round(col("cholesterol_mg"), 2))
        .when(col("cholesterol").isNotNull(), spark_round(col("cholesterol"), 2))
        .otherwise(lit(0.0))
        .alias("cholesterol_mg")
    )
    
    print(f"✅ {df_mapped.count()} rows mapped")
    return df_mapped

def clean_and_validate(df: DataFrame) -> DataFrame:
    """Clean and validate data"""
    print("🧹 Cleaning and validating...")
    
    initial_count = df.count()
    
    # Remove duplicates on name
    df_clean = df.dropDuplicates(["name"])
    
    # Remove rows with invalid name
    df_clean = df_clean.filter(
        (col("name").isNotNull()) & 
        (trim(col("name")) != "") &
        (lower(col("name")) != "unknown")
    )
    
    # Ensure non-negative values
    df_clean = df_clean.filter(
        (col("calories_100g") >= 0) &
        (col("protein_100g") >= 0) &
        (col("carbs_100g") >= 0) &
        (col("fat_100g") >= 0)
    )
    
    final_count = df_clean.count()
    removed = initial_count - final_count
    
    print(f"✅ Cleaned: {final_count} rows")
    if removed > 0:
        print(f"⚠️  Removed: {removed} ({removed/initial_count*100:.1f}%)")
    
    return df_clean

def transform_nutrition(spark, csv_path: str) -> DataFrame:
    """Complete transformation pipeline to MCD schema"""
    print("="*60)
    print("🍎 TRANSFORM NUTRITION → MCD SCHEMA")
    print("="*60)
    
    # Check if file exists
    from pathlib import Path
    if not Path(csv_path).exists():
        print(f"❌ File not found: {csv_path}")
        print("💡 Run extract first: python3 -m processors.nutrition.extract")
        raise FileNotFoundError(f"Raw data file not found: {csv_path}")
    
    df_raw = load_raw_data(spark, csv_path)
    df_mapped = map_to_mcd_schema(df_raw)
    df_clean = clean_and_validate(df_mapped)
    
    print("\n📊 Final schema:")
    df_clean.printSchema()
    
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
