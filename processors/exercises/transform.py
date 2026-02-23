"""
Transform exercises data with PySpark to match MCD schema
"""
from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, trim, lower, when, lit, udf, 
    get_json_object, concat_ws, element_at, split
)
from pyspark.sql.types import StringType
import uuid

def generate_uuid():
    """Generate UUID v4"""
    return str(uuid.uuid4())

uuid_udf = udf(generate_uuid, StringType())

def load_raw_data(spark, json_path: str) -> DataFrame:
    """Load raw JSON data with Spark"""
    print(f"📖 Loading data from: {json_path}")
    # Use multiLine=True for formatted JSON arrays
    df = spark.read.option("multiLine", "true").json(json_path)
    print(f"✅ {df.count()} rows loaded")
    return df

def map_to_mcd_schema(df: DataFrame) -> DataFrame:
    """
    Map source columns to MCD EXERCISE schema
    
    MCD Schema: exercise_id, name, body_part_target, video_url, 
                description, difficulty_level, equipment_required, category
    """
    print("🔄 Mapping to MCD schema...")
    
    df_mapped = df.select(
        uuid_udf().alias("exercise_id"),
        trim(col("name")).alias("name"),
        
        when(col("primaryMuscles").isNotNull(), 
             element_at(col("primaryMuscles"), 1))
        .otherwise(lit("unknown"))
        .alias("body_part_target"),
        
        when(col("images").isNotNull(), 
             element_at(col("images"), 1))
        .otherwise(lit(None))
        .alias("video_url"),
        
        when(col("instructions").isNotNull(),
             concat_ws(" ", col("instructions")))
        .otherwise(lit("No description available"))
        .alias("description"),
        
        when(col("level").isNotNull(), lower(trim(col("level"))))
        .otherwise(lit("beginner"))
        .alias("difficulty_level"),
        
        when(col("equipment").isNotNull(), trim(col("equipment")))
        .otherwise(lit("body only"))
        .alias("equipment_required"),
        
        when(col("category").isNotNull(), trim(col("category")))
        .otherwise(lit("general"))
        .alias("category")
    )
    
    print(f"✅ {df_mapped.count()} rows mapped")
    return df_mapped

def clean_and_validate(df: DataFrame) -> DataFrame:
    """Clean and validate data"""
    print("🧹 Cleaning and validating...")
    
    initial_count = df.count()
    
    df_clean = df.dropDuplicates(["name"])
    
    df_clean = df_clean.filter(
        (col("name").isNotNull()) & (trim(col("name")) != "")
    )
    
    df_clean = df_clean.withColumn(
        "difficulty_level",
        lower(col("difficulty_level"))
    )
    
    df_clean = df_clean.withColumn(
        "category",
        lower(col("category"))
    )
    
    final_count = df_clean.count()
    removed = initial_count - final_count
    
    print(f"✅ Cleaned: {final_count} rows")
    if removed > 0:
        print(f"⚠️  Removed: {removed} ({removed/initial_count*100:.1f}%)")
    
    return df_clean

def transform_exercises(spark, json_path: str) -> DataFrame:
    """Complete transformation pipeline to MCD schema"""
    print("="*60)
    print("🏋️  TRANSFORM EXERCISES → MCD SCHEMA")
    print("="*60)
    
    # Check if file exists
    from pathlib import Path
    if not Path(json_path).exists():
        print(f"❌ File not found: {json_path}")
        print("💡 Run extract first: python3 -m processors.exercises.extract")
        raise FileNotFoundError(f"Raw data file not found: {json_path}")
    
    df_raw = load_raw_data(spark, json_path)
    
    # Validate data was loaded correctly
    if "_corrupt_record" in df_raw.columns:
        print("❌ JSON file is corrupt or empty!")
        print("💡 Delete the file and run extract again")
        raise ValueError("Corrupt JSON data detected")
    
    df_mapped = map_to_mcd_schema(df_raw)
    df_clean = clean_and_validate(df_mapped)
    
    print("\n📊 Final schema:")
    df_clean.printSchema()
    
    return df_clean

if __name__ == "__main__":
    from spark.session import get_spark, stop_spark
    from processors.exercises.config import LOCAL_FILE
    
    spark = get_spark("Transform_Exercises")
    
    try:
        df_transformed = transform_exercises(spark, str(LOCAL_FILE))
        
        print("\n" + "="*60)
        print("📋 TRANSFORMED DATA PREVIEW")
        print("="*60)
        df_transformed.show(5, truncate=False)
        
        print(f"\n📈 Statistics:")
        print(f"Total: {df_transformed.count()} exercises")
        print(f"\nDifficulty levels:")
        df_transformed.groupBy("difficulty_level").count().show()
        print(f"\nEquipment:")
        df_transformed.groupBy("equipment_required").count().show()
        
    finally:
        stop_spark()
