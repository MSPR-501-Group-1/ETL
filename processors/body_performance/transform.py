from pyspark.sql.functions import (
    col, trim, upper, when, lit, udf, current_date, current_timestamp, round as spark_round
)
from pyspark.sql.types import StringType, DateType
from datetime import datetime
from utils.transform import load_raw_data

def generate_first_name(gender, row_idx):
    male_names = ["John", "Michael", "David", "James", "Robert", "William", "Richard", "Thomas", "Charles", "Daniel"]
    female_names = ["Mary", "Jennifer", "Linda", "Patricia", "Elizabeth", "Susan", "Jessica", "Sarah", "Karen", "Nancy"]
    if gender and gender.upper() == 'M':
        return male_names[hash(f"first{row_idx}") % len(male_names)]
    else:
        return female_names[hash(f"first{row_idx}") % len(female_names)]

def generate_last_name(row_idx):
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                  "Wilson", "Anderson", "Taylor", "Thomas", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White"]
    return last_names[hash(f"last{row_idx}") % len(last_names)]

first_name_udf = udf(generate_first_name, StringType())
last_name_udf = udf(generate_last_name, StringType())

def transform_body_performance(spark, csv_path: str):
    """Transform body performance raw data to a single DataFrame matching DB columns (no IDs)."""
    from pathlib import Path
    if not Path(csv_path).exists():
        print(f"❌ FAILED: File not found - {csv_path}")
        raise FileNotFoundError(f"Raw data file not found: {csv_path}")

    df_raw = load_raw_data(spark, csv_path)

    # Add synthetic fields (first_name, last_name)
    from pyspark.sql.window import Window
    from pyspark.sql.functions import row_number, monotonically_increasing_id
    window = Window.orderBy(monotonically_increasing_id())
    df_with_rownum = df_raw.withColumn("row_num", row_number().over(window))

    df = df_with_rownum.withColumn(
        "first_name", first_name_udf(col("gender"), col("row_num").cast("string"))
    ).withColumn(
        "last_name", last_name_udf(col("row_num").cast("string"))
    ).withColumn(
        "birth_date", lit(None).cast(DateType())
    ).withColumn(
        "gender_code",
        when(upper(trim(col("gender"))) == "M", lit("M"))
        .when(upper(trim(col("gender"))) == "F", lit("F"))
        .otherwise(lit("O"))
    ).withColumn(
        "created_at", current_timestamp()
    ).withColumn(
        "is_active", lit(True)
    ).withColumn(
        "role_code", lit("USER")
    ).withColumn(
        "height_cm", spark_round(col("height_cm")).cast("integer")
    ).withColumn(
        "current_weight_kg", spark_round(col("weight_kg"), 2)
    ).withColumn(
        "activity_level_ref", lit(None).cast("string")
    ).withColumn(
        "allergies_json", lit(None).cast("string")
    ).withColumn(
        "preferences_json", lit(None).cast("string")
    ).withColumn(
        "profile_updated_at", current_timestamp()
    ).withColumn(
        "recorded_date", current_date()
    ).withColumn(
        "weight_kg", spark_round(col("weight_kg"), 2)
    ).withColumn(
        "body_fat_percentage", spark_round(col("body fat_%"), 2)
    ).withColumn(
        "steps", lit(None).cast("integer")
    ).withColumn(
        "calories_burned", lit(None).cast("double")
    ).withColumn(
        "heart_rate_avg", lit(None).cast("integer")
    ).withColumn(
        "heart_rate_max", lit(None).cast("integer")
    ).withColumn(
        "sleep_hours", lit(None).cast("double")
    ).withColumn(
        "metrics_created_at", current_timestamp()
    )

    # Select and order columns for clarity (all relevant fields, no IDs)
    output_cols = [
        # User table fields
        "first_name", "last_name", "birth_date", "gender_code", "created_at", "is_active", "role_code",
        # User profile fields
        "height_cm", "current_weight_kg", "activity_level_ref", "allergies_json", "preferences_json", "profile_updated_at",
        # User metrics fields
        "recorded_date", "weight_kg", "body_fat_percentage", "steps", "calories_burned", "heart_rate_avg", "heart_rate_max", "sleep_hours", "metrics_created_at",
        # Raw performance fields
        "diastolic", "systolic", "gripForce", "sit and bend forward_cm", "sit-ups counts", "broad jump_cm", "class"
    ]
    df_final = df.select(*output_cols)

    # Clean: remove rows with nulls in critical fields
    df_final = df_final.filter(
        col("first_name").isNotNull() &
        col("gender_code").isNotNull() &
        col("height_cm").isNotNull() &
        col("current_weight_kg").isNotNull() &
        col("weight_kg").isNotNull()
    )

    print("✅ Single-table transform completed (body performance)")
    return df_final

if __name__ == "__main__":
    from spark.session import get_spark, stop_spark
    from processors.body_performance.config import LOCAL_FILE

    spark = get_spark("Transform_Body_Performance_Single")

    try:
        df_final = transform_body_performance(spark, str(LOCAL_FILE))

        print("\n" + "=" * 60)
        print("📋 TRANSFORMED DATA PREVIEW (BODY PERFORMANCE)")
        print("=" * 60)
        df_final.show(10, truncate=False)

        # Save to CSV (single file)
        output_path = "data/processed/_aligned/body_performance_processed.csv"
        df_final.coalesce(1).write.mode("overwrite").option("header", True).csv(output_path)
        print(f"\n✅ Processed data saved to: {output_path}")

    finally:
        stop_spark()
