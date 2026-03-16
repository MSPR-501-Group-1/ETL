from pyspark.sql.functions import (
    col, trim, upper, when, lit, udf, current_date, current_timestamp,
    round as spark_round, concat, md5, concat_ws
)
from pyspark.sql.types import StringType, DateType
from datetime import datetime
from utils.transform import load_raw_data
from utils.uuid_utils import user_uuid_udf, metric_uuid_udf, DEFAULT_FREEMIUM_ROLE_ID

def generate_first_name(gender, key):
    """Generate deterministic first name from gender and row-key hash."""
    male_names = ["John", "Michael", "David", "James", "Robert", "William", "Richard", "Thomas", "Charles", "Daniel"]
    female_names = ["Mary", "Jennifer", "Linda", "Patricia", "Elizabeth", "Susan", "Jessica", "Sarah", "Karen", "Nancy"]
    seed = int(key[:8], 16) if key else 0
    if gender and gender.upper() == 'M':
        return male_names[seed % len(male_names)]
    else:
        return female_names[seed % len(female_names)]

def generate_last_name(key):
    """Generate deterministic last name from row-key hash."""
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                  "Wilson", "Anderson", "Taylor", "Thomas", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White"]
    seed = int(key[:8], 16) if key else 0
    return last_names[seed % len(last_names)]

first_name_udf = udf(generate_first_name, StringType())
last_name_udf = udf(generate_last_name, StringType())

def transform_body_performance(spark, csv_path: str):
    """Transform body performance raw data to a single DataFrame matching DB columns (no IDs)."""
    from pathlib import Path
    if not Path(csv_path).exists():
        print(f"❌ FAILED: File not found - {csv_path}")
        raise FileNotFoundError(f"Raw data file not found: {csv_path}")

    df_raw = load_raw_data(spark, csv_path)

    # Compute a stable row key from all source columns so that user_id (UUID v5
    # of the email) is identical across re-runs for the same source row.
    _key_cols = [
        col("age"), col("gender"), col("height_cm"), col("weight_kg"),
        col("body fat_%"), col("diastolic"), col("systolic"), col("gripForce"),
        col("sit and bend forward_cm"), col("sit-ups counts"),
        col("broad jump_cm"), col("class"),
    ]
    df_raw = df_raw.withColumn("row_key", md5(concat_ws("|", *_key_cols)))

    df = df_raw.withColumn(
        "first_name", first_name_udf(col("gender"), col("row_key"))
    ).withColumn(
        "last_name", last_name_udf(col("row_key"))
    ).withColumn(
        "birth_date", lit(None).cast(DateType())
    ).withColumn(
        # gender_code is INT in the new schema: 1=M, 2=F, 0=other
        "gender_code",
        when(upper(trim(col("gender"))) == "M", lit(1))
        .when(upper(trim(col("gender"))) == "F", lit(2))
        .otherwise(lit(0))
    ).withColumn(
        "created_at", current_timestamp()
    ).withColumn(
        "is_active", lit(True)
    ).withColumn(
        "role_code", lit("FREEMIUM")
    ).withColumn(
        "role_id", lit(DEFAULT_FREEMIUM_ROLE_ID)
    ).withColumn(
        "height_cm", spark_round(col("height_cm")).cast("integer")
    ).withColumn(
        "current_weight_kg", spark_round(col("weight_kg"), 2)
    ).withColumn(
        "activity_level_ref", lit(None).cast("string")
    ).withColumn(
        "allergies", lit("NONE")
    ).withColumn(
        "diet_type", lit("NONE")
    ).withColumn(
        "goal_id", lit(None).cast("string")
    ).withColumn(
        "updated_at", current_timestamp()
    ).withColumn(
        "recorded_date", current_date()
    ).withColumn(
        "weight_kg", spark_round(col("weight_kg"), 2)
    ).withColumn(
        "body_fat_pourcentage", spark_round(col("body fat_%"), 2)
    ).withColumn(
        "steps", lit(None).cast("integer")
    ).withColumn(
        "calories_burned", lit(None).cast("double")
    ).withColumn(
        "heart_rate_avg", lit(None).cast("integer")
    ).withColumn(
        "heart_rate_max", lit(None).cast("integer")
    ).withColumn(
        "sleep_hours", lit(None).cast("integer")
    )

    # Synthetic email — body performance has no real identity data, so we
    # generate a deterministic address that will never collide with gym_members
    # (different prefix). This lets us derive stable UUID v5 PKs/FKs.
    df = df.withColumn(
        "email", concat(lit("bp_"), col("row_key"), lit("@healthai.com"))
    ).withColumn(
        "password_hash", lit("hashed_password_placeholder")
    ).withColumn(
        "user_id", user_uuid_udf(col("email"))
    ).withColumn(
        "metric_id", metric_uuid_udf(col("user_id"), col("recorded_date").cast("string"))
    )

    output_cols = [
        # user_ table
        "user_id", "email", "password_hash", "first_name", "last_name", "birth_date",
        "gender_code", "created_at", "is_active", "role_code", "role_id",
        # user_profile table (user_id is PK — no separate profile_id)
        "height_cm", "current_weight_kg", "activity_level_ref",
        "allergies", "diet_type", "updated_at", "goal_id",
        # user_metrics table (no user_id — linked via gets junction)
        "metric_id", "recorded_date", "weight_kg", "body_fat_pourcentage",
        "steps", "calories_burned", "heart_rate_avg", "heart_rate_max", "sleep_hours",
        # Raw performance fields (kept for potential downstream use)
        "diastolic", "systolic", "gripForce", "sit and bend forward_cm", "sit-ups counts", "broad jump_cm", "class"
    ]
    df_final = df.select(*output_cols)

    # Clean: remove rows with nulls in critical fields
    df_final = df_final.filter(
        col("first_name").isNotNull() &
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
