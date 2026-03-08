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
from utils.uuid_utils import activity_uuid_udf, session_uuid_udf, user_uuid_udf, generate_user_uuid
from utils.transform import load_raw_data

def create_activity_types(spark) -> DataFrame:
    """
    Create ACTIVITY_TYPE reference table
    
    MCD Schema: activity_id, name, met_value, icon_url
    """
    # Common fitness activities with MET values
    activities = [
        ("Running", 8.0, "https://icon.com/running.png"),
        ("Walking", 3.5, "https://icon.com/walking.png"),
        ("Cycling", 7.0, "https://icon.com/cycling.png"),
        ("Swimming", 6.0, "https://icon.com/swimming.png"),
        ("Gym Workout", 5.0, "https://icon.com/gym.png"),
        ("Yoga", 2.5, "https://icon.com/yoga.png"),
        ("HIIT", 8.0, "https://icon.com/hiit.png"),
        ("Sports", 6.5, "https://icon.com/sports.png")
    ]
    
    df_activities = spark.createDataFrame(activities, ["name", "met_value", "icon_url"])
    
    # Use deterministic UUID based on activity name
    df_activities = df_activities.withColumn("activity_id", activity_uuid_udf(col("name")))
    
    df_activities = df_activities.select(
        "activity_id",
        "name",
        col("met_value").cast("decimal(4,2)"),
        "icon_url"
    )
    
    return df_activities

def transform_to_workout_session(df: DataFrame, df_users: DataFrame, df_activities: DataFrame) -> DataFrame:
    """
    Transform to WORKOUT_SESSION table schema.

    MCD Schema: session_id, user_id, activity_id, start_time, duration_minutes,
                calories_burned, distance_km, notes

    Source columns used:
      Workout_Type            → activity_id  (mapped to activity reference table)
      Session_Duration (hours)→ duration_minutes  (× 60, rounded to integer)
      Calories_Burned         → calories_burned
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

    # Activity lookup map  {lowercase name → activity_id}
    df_activities_map = df_activities.select("activity_id", "name").collect()
    activity_map = {row.name.lower(): row.activity_id for row in df_activities_map}

    def get_user_id(row_key):
        """Pick a gym_members user deterministically via row_key hash."""
        if not user_ids:
            return generate_user_uuid("user0@healthai.com")
        seed = int(row_key[:8], 16) if row_key else 0
        return user_ids[seed % len(user_ids)]

    def get_activity_id(activity_name):
        """Map Workout_Type string to the activity reference UUID."""
        if not activity_name:
            return activity_map.get("gym workout")
        activity_lower = activity_name.lower().strip()
        if activity_lower in activity_map:
            return activity_map[activity_lower]
        for key in activity_map:
            if key in activity_lower or activity_lower in key:
                return activity_map[key]
        return activity_map.get("gym workout")

    get_user_id_udf      = udf(get_user_id, StringType())
    get_activity_id_udf  = udf(get_activity_id, StringType())

    # Map real source columns to the workout_session schema
    df_with_ids = df.select(
        get_user_id_udf(col("row_key")).alias("user_id"),
        get_activity_id_udf(col("Workout_Type")).alias("activity_id"),
        col("row_key").alias("_session_key"),
        spark_round(col("Session_Duration (hours)") * 60).cast("integer").alias("duration_minutes"),
        spark_round(col("Calories_Burned"), 2).cast("decimal(8,2)").alias("calories_burned"),
        lit(None).cast("decimal(6,2)").alias("distance_km"),
        lit("Fitness tracker activity").alias("notes"),
    )

    # session_id is fully deterministic: derived from user_id + row_key + activity_id
    # (not from start_time, which would shift every run)
    df_sessions = df_with_ids.withColumn(
        "session_id",
        session_uuid_udf(col("user_id"), col("_session_key"), col("activity_id"), lit("fitness_tracker"))
    ).withColumn(
        "start_time", current_timestamp()
    ).select(
        "session_id", "user_id", "activity_id", "start_time",
        "duration_minutes", "calories_burned", "distance_km", "notes"
    )

    df_sessions = df_sessions.filter(col("user_id").isNotNull())
    return df_sessions

def clean_and_validate(df_activities: DataFrame, df_sessions: DataFrame):
    """Clean and validate all dataframes"""
    # Remove nulls in critical fields
    df_sessions_clean = df_sessions.filter(
        col("user_id").isNotNull() & 
        col("activity_id").isNotNull() &
        col("calories_burned").isNotNull()
    )
    
    df_activities_clean = df_activities.dropDuplicates(["name"])
    
    return df_activities_clean, df_sessions_clean

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
    user_csv_path = GM_PROCESSED_DIR / "user"
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
    
    # Create reference tables
    df_activities = create_activity_types(spark)
    # Cache and materialize to ensure consistent UUIDs
    df_activities = df_activities.cache()
    df_activities.count()  # Force materialization
    
    # Transform to workout sessions
    df_sessions = transform_to_workout_session(df_raw, df_users, df_activities)
    
    # Clean and validate
    df_activities, df_sessions = clean_and_validate(df_activities, df_sessions)
    
    logger.info("✅ Transform completed")
    return df_activities, df_sessions

if __name__ == "__main__":
    from spark.session import get_spark, stop_spark
    from processors.fitness_tracker.config import LOCAL_FILE
    
    spark = get_spark("Transform_Fitness_Tracker")
    
    try:
        df_activities, df_sessions = transform_fitness_tracker(spark, str(LOCAL_FILE))
        
        print("\n" + "=" * 60)
        print("📋 TRANSFORMED DATA PREVIEW")
        print("=" * 60)
        
        print("\n🏃 ACTIVITY TYPES:")
        df_activities.show(10, truncate=False)
        
        print("\n💪 WORKOUT SESSIONS:")
        df_sessions.show(10, truncate=False)
        
        print(f"\n📊 Statistics:")
        print(f"Activity types: {df_activities.count()}")
        print(f"Workout sessions: {df_sessions.count()}")
        
    finally:
        stop_spark()
