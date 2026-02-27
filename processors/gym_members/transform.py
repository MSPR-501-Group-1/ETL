from pyspark.sql.functions import (
    col, trim, upper, when, lit, udf, 
    current_date, current_timestamp,
    round as spark_round
)
from pyspark.sql.types import StringType, DateType
from datetime import datetime
from utils.transform import load_raw_data

def generate_email(row_idx):
    """Generate synthetic email"""
    return f"user{row_idx}@healthai.com"

def generate_first_name(gender, row_idx):
    """Generate synthetic first name based on gender"""
    male_names = ["John", "Michael", "David", "James", "Robert", "William", "Richard", "Thomas", "Charles", "Daniel"]
    female_names = ["Mary", "Jennifer", "Linda", "Patricia", "Elizabeth", "Susan", "Jessica", "Sarah", "Karen", "Nancy"]
    
    if gender and gender.upper() == 'MALE':
        return male_names[hash(f"first{row_idx}") % len(male_names)]
    else:
        return female_names[hash(f"first{row_idx}") % len(female_names)]

def generate_last_name(row_idx):
    """Generate synthetic last name"""
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                  "Wilson", "Anderson", "Taylor", "Thomas", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White"]
    return last_names[hash(f"last{row_idx}") % len(last_names)]

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
email_udf = udf(generate_email, StringType())
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

    # Add synthetic fields (email, names, birth_date, gender_code)
    from pyspark.sql.window import Window
    from pyspark.sql.functions import row_number, monotonically_increasing_id
    window = Window.orderBy(monotonically_increasing_id())
    df_with_rownum = df_raw.withColumn("row_num", row_number().over(window))

    df = df_with_rownum.withColumn(
        "email", email_udf(col("row_num").cast("string"))
    ).withColumn(
        "password_hash", lit("hashed_password_placeholder")
    ).withColumn(
        "first_name", first_name_udf(col("Gender"), col("row_num").cast("string"))
    ).withColumn(
        "last_name", last_name_udf(col("row_num").cast("string"))
    ).withColumn(
        "birth_date", birth_date_udf(col("Age"))
    ).withColumn(
        "gender_code",
        when(upper(trim(col("Gender"))) == "MALE", lit("M"))
        .when(upper(trim(col("Gender"))) == "FEMALE", lit("F"))
        .otherwise(lit("O"))
    ).withColumn(
        "created_at", current_timestamp()
    ).withColumn(
        "is_active", lit(True)
    ).withColumn(
        "role_code", lit("USER")
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
        "allergies_json", lit(None).cast("string")
    ).withColumn(
        "preferences_json", lit(None).cast("string")
    ).withColumn(
        "profile_updated_at", current_timestamp()
    ).withColumn(
        "recorded_date", current_date()
    ).withColumn(
        "weight_kg", spark_round(col("Weight (kg)"), 2)
    ).withColumn(
        "body_fat_percentage", spark_round(col("Fat_Percentage"), 2)
    ).withColumn(
        "steps", lit(None).cast("integer")
    ).withColumn(
        "calories_burned", spark_round(col("Calories_Burned"), 2)
    ).withColumn(
        "heart_rate_avg", col("Avg_BPM").cast("integer")
    ).withColumn(
        "heart_rate_max", col("Max_BPM").cast("integer")
    ).withColumn(
        "sleep_hours", lit(None).cast("double")
    ).withColumn(
        "metrics_created_at", current_timestamp()
    )

    # Select and order columns for clarity (all relevant fields, no IDs)
    output_cols = [
        # User table fields
        "email", "password_hash", "first_name", "last_name", "birth_date", "gender_code", "created_at", "is_active", "role_code",
        # User profile fields
        "height_cm", "current_weight_kg", "activity_level_ref", "allergies_json", "preferences_json", "profile_updated_at",
        # User metrics fields
        "recorded_date", "weight_kg", "body_fat_percentage", "steps", "calories_burned", "heart_rate_avg", "heart_rate_max", "sleep_hours", "metrics_created_at"
    ]
    df_final = df.select(*output_cols)

    # Clean: remove rows with nulls in critical fields
    df_final = df_final.filter(
        col("email").isNotNull() &
        col("first_name").isNotNull() &
        col("gender_code").isNotNull() &
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
