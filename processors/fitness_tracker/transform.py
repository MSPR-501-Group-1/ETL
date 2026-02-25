"""
Transform fitness tracker data with PySpark to match MCD schema
Maps to: ACTIVITY_TYPE, WORKOUT_SESSION tables
"""
from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, trim, lower, upper, when, lit, udf, 
    current_date, current_timestamp, to_timestamp,
    regexp_replace, round as spark_round, monotonically_increasing_id, row_number
)
from pyspark.sql.types import StringType
from pyspark.sql.window import Window
import uuid
from utils.uuid_utils import activity_uuid_udf, session_uuid_udf, user_uuid_udf, generate_user_uuid

def load_raw_data(spark, csv_path: str) -> DataFrame:
    """Load raw CSV data with Spark"""
    df = spark.read.csv(csv_path, header=True, inferSchema=True)
    return df

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
    Transform to WORKOUT_SESSION table schema
    
    MCD Schema: session_id, user_id, activity_id, start_time, duration_minutes,
                calories_burned, distance_km, notes
    
    Dataset columns: typically include User_ID, Date, Activity_Type, Duration,
                     Calories_Burned, Distance, Steps, etc.
    """
    # Add row numbers for joining
    window = Window.orderBy(monotonically_increasing_id())
    df_with_row = df.withColumn("row_num", row_number().over(window))
    
    # Get random user_ids (cycling through existing users)
    df_users_list = df_users.select("user_id").collect()
    user_ids = [row.user_id for row in df_users_list]
    
    # Get activity mapping
    df_activities_map = df_activities.select("activity_id", "name").collect()
    activity_map = {row.name.lower(): row.activity_id for row in df_activities_map}
    
    # Select user_id based on row number - use deterministic UUID generation for users
    def get_user_id(row_num):
        if user_ids:
            return user_ids[int(row_num) % len(user_ids)]
        # Fallback: generate deterministic user ID from row number
        return generate_user_uuid(f"user{row_num}@healthai.com")
    
    def get_activity_id(activity_name):
        """Map activity name to activity_id"""
        if not activity_name:
            return activity_map.get("gym workout")
        activity_lower = activity_name.lower()
        
        # Try exact match first
        if activity_lower in activity_map:
            return activity_map[activity_lower]
        
        # Try partial matches
        for key in activity_map:
            if key in activity_lower or activity_lower in key:
                return activity_map[key]
        
        # Default to Gym Workout
        return activity_map.get("gym workout")
    
    get_user_id_udf = udf(lambda x: get_user_id(x) if user_ids else None, StringType())
    get_activity_id_udf = udf(get_activity_id, StringType())
    
    # Build workout sessions
    # Note: Column names may vary based on actual dataset structure
    # This is a generic transformation that will need adjustment based on actual columns
    
    # First create user_id, activity_id, and timestamp columns
    df_with_ids = df_with_row.select(
        col("row_num"),
        get_user_id_udf(col("row_num")).alias("user_id"),
        get_activity_id_udf(lit("Gym Workout")).alias("activity_id"),
        current_timestamp().alias("start_time"),
        lit(60).cast("integer").alias("duration_minutes"),
        lit(300.0).cast("decimal(8,2)").alias("calories_burned"),
        lit(None).cast("decimal(6,2)").alias("distance_km"),
        lit("Fitness tracker activity").alias("notes")
    )
    
    # Add deterministic session_id based on user_id, timestamp, activity_id, and source
    df_sessions = df_with_ids.withColumn(
        "session_id",
        session_uuid_udf(col("user_id"), col("start_time").cast("string"), col("activity_id"), lit("fitness_tracker"))
    ).select(
        "session_id", "user_id", "activity_id", "start_time",
        "duration_minutes", "calories_burned", "distance_km", "notes"
    )
    
    # Filter out null user_ids
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
    
    # Get existing users from database (orchestrator ensures gym_members runs first)
    from utils.db_utils import read_table_with_retry
    from utils.logger import get_logger
    
    logger = get_logger(__name__)
    df_users = read_table_with_retry(spark, '"user"')
    
    if df_users is None:
        logger.error("No users found in database. Run gym_members pipeline first!")
        raise ValueError("Users table is empty or doesn't exist. Run gym_members pipeline first.")
    
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
