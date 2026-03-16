"""
Transform fitness tracker data with PySpark to match MCD schema
Maps to: ACTIVITY_TYPE, WORKOUT_SESSION tables
"""
from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, trim, lower, upper, when, lit, udf,
    current_date, current_timestamp,
    round as spark_round
)
from pyspark.sql.types import StringType
import uuid
from utils.uuid_utils import session_uuid_udf, user_uuid_udf, generate_user_uuid
from utils.transform import load_raw_data

def transform_to_workout_session(df: DataFrame, df_users: DataFrame) -> DataFrame:
    """
    Transform to WORKOUT_SESSION table schema.

    Schema: session_id, start_time, duration_time, calories_burned, notes, user_id

    Source columns used:
      Session_Duration (hours) → duration_time (× 60, rounded, SMALLINT)
      Calories_Burned          → calories_burned
    """
    from pyspark.sql.functions import md5, concat_ws

    # Stable row key from all source columns — makes session_id deterministic
    # across re-runs so UPSERT / re-import never creates phantom duplicates.
    _key_cols = [
        col("Age"), col("Gender"), col("Weight (kg)"), col("Height (m)"),
        col("Max_BPM"), col("Avg_BPM"), col("Resting_BPM"),
        col("Session_Duration (hours)"), col("Calories_Burned"), col("Workout_Type"),
        col("Fat_Percentage"), col("Water_Intake (liters)"),
        col("Workout_Frequency (days/week)"), col("Experience_Level"), col("BMI"),
    ]
    df = df.withColumn("row_key", md5(concat_ws("|", *_key_cols)))

    # Materialise user list (already loaded from gym_members processed CSV)
    df_users_list = df_users.select("user_id").collect()
    user_ids = [row.user_id for row in df_users_list]

    def get_user_id(row_key):
        """Pick a gym_members user deterministically via row_key hash."""
        if not user_ids:
            return generate_user_uuid("user0@healthai.com")
        seed = int(row_key[:8], 16) if row_key else 0
        return user_ids[seed % len(user_ids)]

    get_user_id_udf = udf(get_user_id, StringType())

    # Map source columns to the workout_session schema (no activity_id in new schema)
    df_with_ids = df.select(
        get_user_id_udf(col("row_key")).alias("user_id"),
        col("row_key").alias("_session_key"),
        spark_round(col("Session_Duration (hours)") * 60).cast("integer").alias("duration_time"),
        spark_round(col("Calories_Burned"), 2).cast("decimal(7,2)").alias("calories_burned"),
        lit("Fitness tracker activity").alias("notes"),
    )

    # session_id is fully deterministic: derived from user_id + row_key
    df_sessions = df_with_ids.withColumn(
        "session_id",
        session_uuid_udf(col("user_id"), col("_session_key"), lit(None).cast("string"), lit("fitness_tracker"))
    ).withColumn(
        "start_time", current_timestamp()
    ).select(
        "session_id", "start_time", "duration_time", "calories_burned", "notes", "user_id"
    )

    df_sessions = df_sessions.filter(col("user_id").isNotNull())
    return df_sessions

def clean_and_validate(df_sessions: DataFrame) -> DataFrame:
    """Clean and validate workout sessions"""
    return df_sessions.filter(
        col("user_id").isNotNull() &
        col("calories_burned").isNotNull()
    )

def transform_fitness_tracker(spark, csv_path: str):
    """Complete transformation pipeline to MCD schema"""
    print("⏳ Transforming data...")
    
    # Check if file exists
    from pathlib import Path
    if not Path(csv_path).exists():
        print(f"❌ FAILED: File not found: {csv_path}")
        raise FileNotFoundError(f"Raw data file not found: {csv_path}")
    
    df_raw = load_raw_data(spark, csv_path)

    from utils.logger import get_logger
    from utils.uuid_utils import user_uuid_udf as _user_uuid_udf

    logger = get_logger(__name__)

   
    from processors.gym_members.config import PROCESSED_DIR as GM_PROCESSED_DIR
    user_csv_path = GM_PROCESSED_DIR / "user_"
    if not user_csv_path.exists():
        raise ValueError(
            f"Gym members user CSV not found at {user_csv_path}. "
            "Run gym_members pipeline first."
        )
    df_users_raw = spark.read.option("header", "true").csv(str(user_csv_path))
    # Derive user_id deterministically from email (UUID v5, same namespace as gym_members)
    df_users = df_users_raw.withColumn("user_id", _user_uuid_udf(col("email")))
    user_count = df_users.count()
    if user_count == 0:
        raise ValueError(
            f"Gym members user CSV at {user_csv_path} is empty. "
            "Run gym_members pipeline first."
        )
    logger.info(f"✅ Loaded {user_count:,} users from gym_members processed CSV")
    
    # Transform to workout sessions
    df_sessions = transform_to_workout_session(df_raw, df_users)

    # Clean and validate
    df_sessions = clean_and_validate(df_sessions)

    logger.info("✅ Transform completed")
    return df_sessions

if __name__ == "__main__":
    from spark.session import get_spark, stop_spark
    from processors.fitness_tracker.config import LOCAL_FILE
    
    spark = get_spark("Transform_Fitness_Tracker")
    
    try:
        df_sessions = transform_fitness_tracker(spark, str(LOCAL_FILE))

        print("\n" + "=" * 60)
        print("📋 TRANSFORMED DATA PREVIEW")
        print("=" * 60)

        print("\n💪 WORKOUT SESSIONS:")
        df_sessions.show(10, truncate=False)

        print(f"\n📊 Statistics:")
        print(f"Workout sessions: {df_sessions.count()}")
        
    finally:
        stop_spark()
