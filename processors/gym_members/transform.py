from pyspark.sql.functions import (
    col, trim, upper, when, lit, udf,
    current_date, current_timestamp,
    round as spark_round, md5, concat_ws, concat
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
    if gender and gender.upper() == 'MALE':
        return male_names[seed % len(male_names)]
    else:
        return female_names[seed % len(female_names)]

def generate_last_name(key):
    """Generate deterministic last name from row-key hash."""
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                  "Wilson", "Anderson", "Taylor", "Thomas", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White"]
    seed = int(key[:8], 16) if key else 0
    return last_names[seed % len(last_names)]

def calculate_birth_date(age):
    """Calculate birth date from age"""
    if not age:
        return None
    try:
        current_year = datetime.now().year
        birth_year = current_year - int(age)
        # Random month and day
        month = (hash(str(age)) % 12) + 1
        day = (hash(str(age) + "day") % 28) + 1
        return datetime(birth_year, month, day).date()
    except:
        return None

# Register UDFs
first_name_udf = udf(generate_first_name, StringType())
last_name_udf = udf(generate_last_name, StringType())
birth_date_udf = udf(calculate_birth_date, DateType())

def transform_gym_members(spark, csv_path: str):
    """Transform gym members raw data to a single DataFrame matching DB columns (no IDs)."""
    from pathlib import Path
    if not Path(csv_path).exists():
        print(f"❌ FAILED: File not found - {csv_path}")
        raise FileNotFoundError(f"Raw data file not found: {csv_path}")

    df_raw = load_raw_data(spark, csv_path)

    # Compute a stable row key from all source columns so that user_id (UUID v5
    # of the email) is identical across re-runs for the same source row.
    _key_cols = [
        col("Age"), col("Gender"), col("Weight (kg)"), col("Height (m)"),
        col("Max_BPM"), col("Avg_BPM"), col("Resting_BPM"),
        col("Session_Duration (hours)"), col("Calories_Burned"), col("Workout_Type"),
        col("Fat_Percentage"), col("Water_Intake (liters)"),
        col("Workout_Frequency (days/week)"), col("Experience_Level"), col("BMI"),
    ]
    df_raw = df_raw.withColumn("row_key", md5(concat_ws("|", *_key_cols)))

    df = df_raw.withColumn(
        "email", concat(lit("gm_"), col("row_key"), lit("@healthai.com"))
    ).withColumn(
        "password_hash", lit("hashed_password_placeholder")
    ).withColumn(
        "first_name", first_name_udf(col("Gender"), col("row_key"))
    ).withColumn(
        "last_name", last_name_udf(col("row_key"))
    ).withColumn(
        "birth_date", birth_date_udf(col("Age"))
    ).withColumn(
        # gender_code is INT in the new schema: 1=M, 2=F, 0=O
        "gender_code",
        when(upper(trim(col("Gender"))) == "MALE", lit(1))
        .when(upper(trim(col("Gender"))) == "FEMALE", lit(2))
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
        # Height: meters to cm
        "height_cm", spark_round(col("Height (m)") * 100).cast("integer")
    ).withColumn(
        "current_weight_kg", spark_round(col("Weight (kg)"), 2)
    ).withColumn(
        "activity_level_ref",
        when(col("Experience_Level") == 1, lit("beginner"))
        .when(col("Experience_Level") == 2, lit("intermediate"))
        .when(col("Experience_Level") == 3, lit("advanced"))
        .otherwise(lit("beginner"))
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
        "weight_kg", spark_round(col("Weight (kg)"), 2)
    ).withColumn(
        # Renamed to match DB column (note the typo is in the schema)
        "body_fat_pourcentage", spark_round(col("Fat_Percentage"), 2)
    ).withColumn(
        "steps", lit(None).cast("integer")
    ).withColumn(
        "calories_burned", spark_round(col("Calories_Burned"), 2)
    ).withColumn(
        "heart_rate_avg", col("Avg_BPM").cast("integer")
    ).withColumn(
        "heart_rate_max", col("Max_BPM").cast("integer")
    ).withColumn(
        "sleep_hours", lit(None).cast("integer")
    )

    # Generate deterministic UUID v5 PKs.
    # user_id is derived from email — stable across re-runs.
    # user_id_1 is an alias of user_id satisfying user_.user_id_1 → user_profile.user_id FK.
    # metric_id is derived from user_id + recorded_date.
    df = df.withColumn("user_id", user_uuid_udf(col("email"))) \
           .withColumn("user_id_1", col("user_id")) \
           .withColumn("metric_id", metric_uuid_udf(col("user_id"), col("recorded_date").cast("string")))

    output_cols = [
        # user_ table
        "user_id", "email", "password_hash", "first_name", "last_name", "birth_date",
        "gender_code", "created_at", "is_active", "role_code", "role_id", "user_id_1",
        # user_profile table (user_id shared as PK — no separate profile_id)
        "height_cm", "current_weight_kg", "activity_level_ref",
        "allergies", "diet_type", "updated_at", "goal_id",
        # user_metrics table (no user_id — linked via gets junction)
        "metric_id", "recorded_date", "weight_kg", "body_fat_pourcentage",
        "steps", "calories_burned", "heart_rate_avg", "heart_rate_max", "sleep_hours",
    ]
    df_final = df.select(*output_cols)

    # Clean: remove rows with nulls in critical fields
    df_final = df_final.filter(
        col("email").isNotNull() &
        col("first_name").isNotNull() &
        col("height_cm").isNotNull() &
        col("current_weight_kg").isNotNull() &
        col("weight_kg").isNotNull()
    )

    print("✅ Single-table transform completed")
    return df_final

if __name__ == "__main__":
    from spark.session import get_spark, stop_spark
    from processors.gym_members.config import LOCAL_FILE

    spark = get_spark("Transform_Gym_Members_Single")

    try:
        df_final = transform_gym_members(spark, str(LOCAL_FILE))

        print("\n" + "=" * 60)
        print("📋 TRANSFORMED DATA PREVIEW (SINGLE TABLE)")
        print("=" * 60)
        df_final.show(10, truncate=False)

        # Save to CSV (single file)
        output_path = "data/processed/_aligned/gym_members_processed.csv"
        df_final.coalesce(1).write.mode("overwrite").option("header", True).csv(output_path)
        print(f"\n✅ Processed data saved to: {output_path}")

    finally:
        stop_spark()
