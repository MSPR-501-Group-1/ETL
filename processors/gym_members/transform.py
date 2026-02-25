"""
Transform gym members data with PySpark to match MCD schema
Maps to: USER, USER_PROFILE, USER_METRICS tables
"""
from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, trim, lower, upper, when, lit, udf, 
    year, current_date, current_timestamp,
    regexp_replace, round as spark_round
)
from pyspark.sql.types import StringType, DateType
import uuid
from datetime import datetime, timedelta
import random

# UDF generators
def generate_uuid():
    """Generate UUID v4"""
    return str(uuid.uuid4())

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
uuid_udf = udf(generate_uuid, StringType())
email_udf = udf(generate_email, StringType())
first_name_udf = udf(generate_first_name, StringType())
last_name_udf = udf(generate_last_name, StringType())
birth_date_udf = udf(calculate_birth_date, DateType())

def load_raw_data(spark, csv_path: str) -> DataFrame:
    """Load raw CSV data with Spark"""
    df = spark.read.csv(csv_path, header=True, inferSchema=True)
    return df

def transform_to_user_table(df: DataFrame) -> DataFrame:
    """
    Transform to USER table schema
    
    MCD Schema: user_id, email, password_hash, first_name, last_name, 
                birth_date, gender_code, created_at, is_active, role_code
    """
    df_user = df.select(
        uuid_udf().alias("user_id"),
        email_udf(col("Age").cast("string")).alias("email"),
        lit("hashed_password_placeholder").alias("password_hash"),
        first_name_udf(col("Gender"), col("Age").cast("string")).alias("first_name"),
        last_name_udf(col("Age").cast("string")).alias("last_name"),
        birth_date_udf(col("Age")).alias("birth_date"),
        
        when(upper(trim(col("Gender"))) == "MALE", lit("M"))
        .when(upper(trim(col("Gender"))) == "FEMALE", lit("F"))
        .otherwise(lit("O"))
        .alias("gender_code"),
        
        current_timestamp().alias("created_at"),
        lit(True).alias("is_active"),
        lit("USER").alias("role_code")
    )
    
    return df_user

def transform_to_user_profile(df: DataFrame, df_user: DataFrame) -> DataFrame:
    """
    Transform to USER_PROFILE table schema
    
    MCD Schema: profile_id, user_id, height_cm, current_weight_kg, 
                activity_level_ref, health_goal_id (nullable), 
                allergies_json (nullable), preferences_json (nullable), updated_at
    """
    print("⏳ Transforming gym members data...")
    
    # Join with user to get user_id (using row number match)
    from pyspark.sql.window import Window
    from pyspark.sql.functions import row_number, monotonically_increasing_id
    
    # Add row numbers to both dataframes
    window = Window.orderBy(monotonically_increasing_id())
    df_with_row = df.withColumn("row_num", row_number().over(window))
    df_user_with_row = df_user.withColumn("row_num", row_number().over(window))
    
    # Join on row number
    df_joined = df_with_row.join(df_user_with_row.select("row_num", "user_id"), "row_num")
    
    df_profile = df_joined.select(
        uuid_udf().alias("profile_id"),
        col("user_id"),
        
        # Height: convert meters to cm
        spark_round(col("Height (m)") * 100).cast("integer").alias("height_cm"),
        
        # Weight in kg
        spark_round(col("Weight (kg)"), 2).alias("current_weight_kg"),
        
        # Map Experience_Level to activity_level_ref
        when(col("Experience_Level") == 1, lit("beginner"))
        .when(col("Experience_Level") == 2, lit("intermediate"))
        .when(col("Experience_Level") == 3, lit("advanced"))
        .otherwise(lit("beginner"))
        .alias("activity_level_ref"),
        
        lit(None).cast("string").alias("health_goal_id"),
        lit(None).cast("string").alias("allergies_json"),
        lit(None).cast("string").alias("preferences_json"),
        current_timestamp().alias("updated_at")
    )
    

    return df_profile

def transform_to_user_metrics(df: DataFrame, df_user: DataFrame) -> DataFrame:
    """
    Transform to USER_METRICS table schema
    
    MCD Schema: metric_id, user_id, recorded_date, weight_kg, body_fat_percentage,
                steps (nullable), calories_burned, heart_rate_avg, heart_rate_max,
                sleep_hours (nullable), created_at
    """
    # Join with user to get user_id
    from pyspark.sql.window import Window
    from pyspark.sql.functions import row_number, monotonically_increasing_id
    
    window = Window.orderBy(monotonically_increasing_id())
    df_with_row = df.withColumn("row_num", row_number().over(window))
    df_user_with_row = df_user.withColumn("row_num", row_number().over(window))
    
    df_joined = df_with_row.join(df_user_with_row.select("row_num", "user_id"), "row_num")
    
    df_metrics = df_joined.select(
        uuid_udf().alias("metric_id"),
        col("user_id"),
        current_date().alias("recorded_date"),
        spark_round(col("Weight (kg)"), 2).alias("weight_kg"),
        spark_round(col("Fat_Percentage"), 2).alias("body_fat_percentage"),
        
        lit(None).cast("integer").alias("steps"),
        
        spark_round(col("Calories_Burned"), 2).alias("calories_burned"),
        col("Avg_BPM").cast("integer").alias("heart_rate_avg"),
        col("Max_BPM").cast("integer").alias("heart_rate_max"),
        
        lit(None).cast("double").alias("sleep_hours"),
        
        current_timestamp().alias("created_at")
    )
    
    return df_metrics

def clean_and_validate(df_user: DataFrame, df_profile: DataFrame, df_metrics: DataFrame):
    """Clean and validate all dataframes"""
    # Remove nulls in critical fields
    df_user_clean = df_user.filter(
        col("email").isNotNull() & 
        col("first_name").isNotNull() &
        col("gender_code").isNotNull()
    )
    
    df_profile_clean = df_profile.filter(
        col("user_id").isNotNull() &
        col("height_cm").isNotNull() &
        col("current_weight_kg").isNotNull()
    )
    
    df_metrics_clean = df_metrics.filter(
        col("user_id").isNotNull() &
        col("weight_kg").isNotNull()
    )
    
    return df_user_clean, df_profile_clean, df_metrics_clean

def transform_gym_members(spark, csv_path: str):
    """Complete transformation pipeline to MCD schema"""
    # Check if file exists
    from pathlib import Path
    if not Path(csv_path).exists():
        print(f"❌ FAILED: File not found - {csv_path}")
        raise FileNotFoundError(f"Raw data file not found: {csv_path}")
    
    df_raw = load_raw_data(spark, csv_path)
    
    # Transform to 3 tables
    df_user = transform_to_user_table(df_raw)
    df_profile = transform_to_user_profile(df_raw, df_user)
    df_metrics = transform_to_user_metrics(df_raw, df_user)
    
    # Clean and validate
    df_user, df_profile, df_metrics = clean_and_validate(df_user, df_profile, df_metrics)
    
    print("✅ Transform completed")
    return df_user, df_profile, df_metrics

if __name__ == "__main__":
    from spark.session import get_spark, stop_spark
    from processors.gym_members.config import LOCAL_FILE
    
    spark = get_spark("Transform_Gym_Members")
    
    try:
        df_user, df_profile, df_metrics = transform_gym_members(spark, str(LOCAL_FILE))
        
        print("\n" + "=" * 60)
        print("📋 TRANSFORMED DATA PREVIEW")
        print("=" * 60)
        
        print("\n👤 USERS:")
        df_user.show(5, truncate=False)
        
        print("\n📊 USER PROFILES:")
        df_profile.show(5, truncate=False)
        
        print("\n📈 USER METRICS:")
        df_metrics.show(5, truncate=False)
        
        print(f"\n📊 Statistics:")
        print(f"Total users: {df_user.count()}")
        print(f"\nGender distribution:")
        df_user.groupBy("gender_code").count().show()
        print(f"\nActivity levels:")
        df_profile.groupBy("activity_level_ref").count().show()
        
    finally:
        stop_spark()
