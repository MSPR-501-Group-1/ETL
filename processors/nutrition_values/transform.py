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
    
    Expected columns in nutritional-values dataset may vary, handling common variations
    """
    print("🔄 Mapping to MCD schema...")
    
    # Show original columns for debugging
    print(f"   Original columns: {df.columns}")
    
    # Normalize column names (lowercase, remove spaces/parentheses)
    for old_col in df.columns:
        new_col = old_col.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
        df = df.withColumnRenamed(old_col, new_col)
    
    print(f"   Normalized columns: {df.columns}")
    
    # Map to MCD schema with flexible column matching
    df_mapped = df.select(
        uuid_udf().alias("food_id"),
        
        # Name - try common variations
        when(col("food").isNotNull(), trim(col("food")))
        .when(col("name").isNotNull(), trim(col("name")))
        .when(col("description").isNotNull(), trim(col("description")))
        .otherwise(lit("Unknown"))
        .alias("name"),
        
        # Brand (often not available in nutritional datasets)
        lit(None).cast(StringType()).alias("brand"),
        
        # Calories per 100g - try variations
        when(col("calories").isNotNull(), spark_round(col("calories"), 2))
        .when(col("energy_kcal").isNotNull(), spark_round(col("energy_kcal"), 2))
        .when(col("energy").isNotNull(), spark_round(col("energy"), 2))
        .when(col("calorie").isNotNull(), spark_round(col("calorie"), 2))
        .otherwise(lit(0.0))
        .alias("calories_100g"),
        
        # Protein per 100g - try variations
        when(col("protein_g").isNotNull(), spark_round(col("protein_g"), 2))
        .when(col("protein").isNotNull(), spark_round(col("protein"), 2))
        .when(col("proteins").isNotNull(), spark_round(col("proteins"), 2))
        .otherwise(lit(0.0))
        .alias("protein_100g"),
        
        # Carbohydrates per 100g - try variations
        when(col("carbohydrate_g").isNotNull(), spark_round(col("carbohydrate_g"), 2))
        .when(col("carbs_g").isNotNull(), spark_round(col("carbs_g"), 2))
        .when(col("carbohydrates").isNotNull(), spark_round(col("carbohydrates"), 2))
        .when(col("carbs").isNotNull(), spark_round(col("carbs"), 2))
        .when(col("total_carbohydrate").isNotNull(), spark_round(col("total_carbohydrate"), 2))
        .otherwise(lit(0.0))
        .alias("carbs_100g"),
        
        # Fat per 100g - try variations
        when(col("fat_g").isNotNull(), spark_round(col("fat_g"), 2))
        .when(col("total_fat").isNotNull(), spark_round(col("total_fat"), 2))
        .when(col("fat").isNotNull(), spark_round(col("fat"), 2))
        .when(col("lipid").isNotNull(), spark_round(col("lipid"), 2))
        .otherwise(lit(0.0))
        .alias("fat_100g"),
        
        # Nutriscore (rarely available)
        lit(None).cast(StringType()).alias("nutriscore"),
        
        # Category - try variations
        when(col("category").isNotNull(), lower(trim(col("category"))))
        .when(col("food_category").isNotNull(), lower(trim(col("food_category"))))
        .when(col("food_group").isNotNull(), lower(trim(col("food_group"))))
        .when(col("group").isNotNull(), lower(trim(col("group"))))
        .otherwise(lit("general"))
        .alias("category_ref"),
        
        # Fiber - try variations
        when(col("fiber_g").isNotNull(), spark_round(col("fiber_g"), 2))
        .when(col("dietary_fiber").isNotNull(), spark_round(col("dietary_fiber"), 2))
        .when(col("fiber").isNotNull(), spark_round(col("fiber"), 2))
        .when(col("fibre").isNotNull(), spark_round(col("fibre"), 2))
        .otherwise(lit(0.0))
        .alias("fiber_g"),
        
        # Sugar - try variations
        when(col("sugar_g").isNotNull(), spark_round(col("sugar_g"), 2))
        .when(col("sugars").isNotNull(), spark_round(col("sugars"), 2))
        .when(col("sugar").isNotNull(), spark_round(col("sugar"), 2))
        .when(col("total_sugars").isNotNull(), spark_round(col("total_sugars"), 2))
        .otherwise(lit(0.0))
        .alias("sugar_g"),
        
        # Sodium - try variations
        when(col("sodium_mg").isNotNull(), spark_round(col("sodium_mg"), 2))
        .when(col("sodium").isNotNull(), spark_round(col("sodium"), 2))
        .when(col("salt").isNotNull(), spark_round(col("salt") * 400, 2))  # Salt to sodium conversion
        .otherwise(lit(0.0))
        .alias("sodium_mg"),
        
        # Cholesterol - try variations
        when(col("cholesterol_mg").isNotNull(), spark_round(col("cholesterol_mg"), 2))
        .when(col("cholesterol").isNotNull(), spark_round(col("cholesterol"), 2))
        .otherwise(lit(0.0))
        .alias("cholesterol_mg")
    )
    
    return df_mapped

def clean_data(df: DataFrame) -> DataFrame:
    """Clean and validate transformed data"""
    print("🧹 Cleaning data...")
    
    initial_count = df.count()
    
    # Remove rows with null/empty names
    df = df.filter(
        (col("name").isNotNull()) & 
        (trim(col("name")) != "") &
        (col("name") != "Unknown")
    )
    
    # Remove duplicates based on name
    df = df.dropDuplicates(["name"])
    
    # Validate numeric ranges (calories should be reasonable)
    df = df.filter(
        (col("calories_100g") >= 0) & (col("calories_100g") <= 900)
    )
    
    final_count = df.count()
    removed = initial_count - final_count
    
    print(f"   Initial rows: {initial_count}")
    print(f"   Final rows: {final_count}")
    print(f"   Removed: {removed} ({(removed/initial_count*100):.1f}%)")
    
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
    print("=" * 60)
    print("🔄 TRANSFORM NUTRITION VALUES DATA")
    print("=" * 60)
    
    try:
        # 1. Load raw data
        df_raw = load_raw_data(spark, csv_path)
        
        # 2. Map to MCD schema
        df_mapped = map_to_mcd_schema(df_raw)
        
        # 3. Clean data
        df_clean = clean_data(df_mapped)
        
        # 4. Show sample
        print("\n📊 Sample transformed data:")
        df_clean.select("name", "calories_100g", "protein_100g", "carbs_100g", "fat_100g").show(5, truncate=False)
        
        print(f"\n✅ Transformation completed: {df_clean.count()} foods ready")
        return df_clean
        
    except Exception as e:
        print(f"\n❌ Transformation error: {e}")
        import traceback
        traceback.print_exc()
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
