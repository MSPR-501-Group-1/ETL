"""
Transform exercises data with PySpark to match MCD schema
"""
from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, trim, lower, upper, when, lit, udf,
    get_json_object, concat_ws, element_at, split, substring
)
from pyspark.sql.types import StringType
import uuid
from utils.transform import load_raw_data
from utils.uuid_utils import exercise_uuid_udf

def load_raw_data(spark, json_path: str) -> DataFrame:
    """Load raw JSON data with Spark"""
    # Use multiLine=True for formatted JSON arrays
    df = spark.read.option("multiLine", "true").json(json_path)
    return df

def map_to_mcd_schema(df: DataFrame) -> DataFrame:
    """
    Map source columns to MCD EXERCISE schema

    MCD Schema: exercise_id, name, body_part_target, video_url,
                description, difficulty_level, equipment_required, category
    All enum columns must use exact PostgreSQL enum label strings.
    """
    # Map raw primaryMuscles[0] → body_part_enum
    raw_bp = when(col("primaryMuscles").isNotNull(),
                  lower(trim(element_at(col("primaryMuscles"), 1))))\
             .otherwise(lit("other"))

    body_part_mapped = (
        when(raw_bp.isin("chest"), lit("CHEST"))
        .when(raw_bp.isin("shoulders", "middle shoulders", "traps"), lit("SHOULDERS"))
        .when(raw_bp.isin("middle back", "lower back", "lats", "back"), lit("BACK"))
        .when(raw_bp.isin("biceps", "triceps", "forearms"), lit("ARMS"))
        .when(raw_bp.isin("quadriceps", "hamstrings", "calves", "glutes",
                           "adductors", "abductors"), lit("LEGS"))
        .when(raw_bp.isin("abdominals", "abs"), lit("CORE"))
        .otherwise(lit("FULL_BODY"))
    )

    # Map raw level → exercise_difficulty_enum
    raw_lvl = lower(trim(col("level")))
    difficulty_mapped = (
        when(raw_lvl == lit("beginner"), lit("BEGINNER"))
        .when(raw_lvl == lit("intermediate"), lit("INTERMEDIATE"))
        .when(raw_lvl.isin("advanced", "expert"), lit("ADVANCED"))
        .otherwise(lit("BEGINNER"))
    )

    # Map raw category → exercise_category_enum
    raw_cat = lower(trim(col("category")))
    category_mapped = (
        when(raw_cat.isin("strength", "powerlifting", "strongman",
                           "olympic weightlifting"), lit("STRENGTH"))
        .when(raw_cat.isin("cardio", "crossfit", "plyometrics"), lit("CARDIO"))
        .when(raw_cat.isin("stretching", "flexibility"), lit("FLEXIBILITY"))
        .when(raw_cat == lit("balance"), lit("BALANCE"))
        .otherwise(lit("OTHER"))
    )

    df_mapped = df.select(
        trim(col("name")).alias("name"),

        body_part_mapped.alias("body_part_target"),

        when(col("images").isNotNull(),
             element_at(col("images"), 1))
        .otherwise(lit(None))
        .alias("video_url"),

        # description is VARCHAR(50) — truncate
        substring(
            when(col("instructions").isNotNull(),
                 concat_ws(" ", col("instructions")))
            .otherwise(lit("No description available")),
            1, 50
        ).alias("description"),

        difficulty_mapped.alias("difficulty_level"),

        when(col("equipment").isNotNull(), trim(col("equipment")))
        .otherwise(lit("body only"))
        .alias("equipment_required"),

        category_mapped.alias("category")
    )

    # Add deterministic UUID based on exercise name
    df_mapped = df_mapped.withColumn(
        "exercise_id",
        exercise_uuid_udf(col("name"))
    ).select(
        "exercise_id", "name", "body_part_target", "video_url",
        "description", "difficulty_level", "equipment_required", "category"
    )

    return df_mapped

def clean_and_validate(df: DataFrame) -> DataFrame:
    """Clean and validate data"""
    df_clean = df.dropDuplicates(["name"])

    df_clean = df_clean.filter(
        (col("name").isNotNull()) & (trim(col("name")) != "")
    )

    # Enum columns are already uppercase — no lowercasing here

    return df_clean

def transform_exercises(spark, json_path: str) -> DataFrame:
    """Complete transformation pipeline to MCD schema"""
    print("⏳ Transforming exercises data...")
    
    # Check if file exists
    from pathlib import Path
    if not Path(json_path).exists():
        print(f"❌ FAILED: File not found - {json_path}")
        raise FileNotFoundError(f"Raw data file not found: {json_path}")
    
    df_raw = load_raw_data(spark, json_path)
    
    # Validate data was loaded correctly
    if "_corrupt_record" in df_raw.columns:
        print("❌ FAILED: JSON file is corrupt or empty")
        raise ValueError("Corrupt JSON data detected")
    
    df_mapped = map_to_mcd_schema(df_raw)
    df_clean = clean_and_validate(df_mapped)
    
    print("✅ Transform completed")
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
