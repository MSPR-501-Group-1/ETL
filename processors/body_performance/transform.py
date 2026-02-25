"""
Transform body performance data with PySpark to match MCD schema
Maps to: WORKOUT_SESSION, SESSION_DETAIL tables
"""
from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, trim, lower, upper, when, lit, udf, concat,
    current_date, current_timestamp,
    regexp_replace, round as spark_round, monotonically_increasing_id, row_number
)
from pyspark.sql.types import StringType
from pyspark.sql.window import Window
import uuid

def generate_uuid():
    """Generate UUID v4"""
    return str(uuid.uuid4())

uuid_udf = udf(generate_uuid, StringType())

def load_raw_data(spark, csv_path: str) -> DataFrame:
    """Load raw CSV data with Spark"""
    df = spark.read.csv(csv_path, header=True, inferSchema=True)
    return df

def transform_to_workout_session_performance(df: DataFrame, df_users: DataFrame, df_activities: DataFrame) -> DataFrame:
    """
    Transform to WORKOUT_SESSION table schema with performance metrics
    
    MCD Schema: session_id, user_id, activity_id, start_time, duration_minutes,
                calories_burned, distance_km, notes
    
    Body Performance columns: age, gender, height_cm, weight_kg, body fat_%,
                             diastolic, systolic, gripForce, sit and bend forward_cm,
                             sit-ups counts, broad jump_cm, class (performance level A-D)
    """
    # Add row numbers for joining
    window = Window.orderBy(monotonically_increasing_id())
    df_with_row = df.withColumn("row_num", row_number().over(window))
    
    # Get random user_ids (cycling through existing users)
    df_users_list = df_users.select("user_id").collect()
    user_ids = [row.user_id for row in df_users_list]
    
    # Get Gym Workout activity_id
    gym_activity_id = df_activities.filter(col("name") == "Gym Workout") \
        .select("activity_id").first()
    
    if gym_activity_id:
        gym_activity_id = gym_activity_id.activity_id
    else:
        gym_activity_id = str(uuid.uuid4())  # fallback
    
    # Function to get user_id based on row number
    def get_user_id(row_num):
        if user_ids:
            return user_ids[int(row_num) % len(user_ids)]
        return None
    
    get_user_id_udf = udf(lambda x: get_user_id(x) if user_ids else None, StringType())
    
    # Calculate estimated calories burned from performance metrics
    # Formula approximation based on body composition and activity
    df_sessions = df_with_row.select(
        uuid_udf().alias("session_id"),
        get_user_id_udf(col("row_num")).alias("user_id"),
        lit(gym_activity_id).alias("activity_id"),
        current_timestamp().alias("start_time"),
        lit(45).cast("integer").alias("duration_minutes"),  # Standard 45min workout
        
        # Estimate calories from body metrics and performance class
        when(col("class") == "A", lit(450.0))
        .when(col("class") == "B", lit(400.0))
        .when(col("class") == "C", lit(350.0))
        .otherwise(lit(300.0))
        .cast("decimal(8,2)")
        .alias("calories_burned"),
        
        lit(None).cast("decimal(6,2)").alias("distance_km"),
        
        # Create notes with performance class
        when(col("class").isNotNull(), 
             concat(lit("Performance level: "), col("class")))
        .otherwise(lit("Gym workout session"))
        .alias("notes")
    )
    
    # Store row_num for session_detail mapping
    df_sessions = df_sessions.withColumn("source_row", col("row_num"))
    
    # Filter out null user_ids
    df_sessions = df_sessions.filter(col("user_id").isNotNull())
    
    return df_sessions

def transform_to_session_detail(df: DataFrame, df_sessions: DataFrame, df_exercises: DataFrame) -> DataFrame:
    """
    Transform to SESSION_DETAIL table schema
    
    MCD Schema: detail_id, session_id, exercise_id, sets, reps, weight_kg
    
    Maps performance metrics to exercise details
    """
    # Get sample exercises for different body parts
    exercises_list = df_exercises.select("exercise_id", "name", "body_part_target").collect()
    
    if not exercises_list:
        return None
    
    # Create exercise mapping
    core_exercises = [ex for ex in exercises_list if ex.body_part_target and "core" in ex.body_part_target.lower()]
    leg_exercises = [ex for ex in exercises_list if ex.body_part_target and "leg" in ex.body_part_target.lower()]
    upper_exercises = [ex for ex in exercises_list if ex.body_part_target and any(x in ex.body_part_target.lower() for x in ["chest", "back", "shoulder"])]
    
    # Use first available exercise from each category, or fallback to any
    core_ex = core_exercises[0].exercise_id if core_exercises else exercises_list[0].exercise_id
    leg_ex = leg_exercises[0].exercise_id if leg_exercises else exercises_list[1 % len(exercises_list)].exercise_id
    upper_ex = upper_exercises[0].exercise_id if upper_exercises else exercises_list[2 % len(exercises_list)].exercise_id
    
    # Add row number to original data
    window = Window.orderBy(monotonically_increasing_id())
    df_with_row = df.withColumn("row_num", row_number().over(window))
    
    # Join with sessions to get session_id
    df_joined = df_with_row.join(
        df_sessions.select("session_id", "source_row"),
        df_with_row.row_num == df_sessions.source_row,
        "inner"
    )
    
    # Create details for each session (3 exercises per session based on performance metrics)
    details = []
    
    # Sit-ups -> Core exercise
    detail1 = df_joined.select(
        uuid_udf().alias("detail_id"),
        col("session_id"),
        lit(core_ex).alias("exercise_id"),
        lit(3).cast("integer").alias("sets"),
        when(col("sit-ups counts").isNotNull(), col("sit-ups counts").cast("integer"))
        .otherwise(lit(15))
        .alias("reps"),
        lit(None).cast("decimal(6,2)").alias("weight_kg")
    )
    details.append(detail1)
    
    # Broad jump -> Leg exercise
    detail2 = df_joined.select(
        uuid_udf().alias("detail_id"),
        col("session_id"),
        lit(leg_ex).alias("exercise_id"),
        lit(3).cast("integer").alias("sets"),
        lit(10).cast("integer").alias("reps"),
        lit(None).cast("decimal(6,2)").alias("weight_kg")
    )
    details.append(detail2)
    
    # Grip force -> Upper body exercise
    detail3 = df_joined.select(
        uuid_udf().alias("detail_id"),
        col("session_id"),
        lit(upper_ex).alias("exercise_id"),
        lit(3).cast("integer").alias("sets"),
        lit(12).cast("integer").alias("reps"),
        when(col("gripForce").isNotNull(), spark_round(col("gripForce") / 5, 2))
        .otherwise(lit(None))
        .cast("decimal(6,2)")
        .alias("weight_kg")
    )
    details.append(detail3)
    
    # Union all details
    df_details = details[0]
    for detail in details[1:]:
        df_details = df_details.union(detail)
    
    return df_details

def clean_and_validate(df_sessions: DataFrame, df_details: DataFrame = None):
    """Clean and validate all dataframes"""
    # Remove nulls in critical fields
    df_sessions_clean = df_sessions.filter(
        col("user_id").isNotNull() & 
        col("activity_id").isNotNull() &
        col("calories_burned").isNotNull()
    ).drop("source_row")
    
    if df_details is not None:
        df_details_clean = df_details.filter(
            col("session_id").isNotNull() &
            col("exercise_id").isNotNull()
        )
        return df_sessions_clean, df_details_clean
    
    return df_sessions_clean, None

def transform_body_performance(spark, csv_path: str):
    """Complete transformation pipeline to MCD schema"""
    print("⏳ Transforming data...")
    
    # Check if file exists
    from pathlib import Path
    if not Path(csv_path).exists():
        print(f"❌ FAILED: File not found: {csv_path}")
        raise FileNotFoundError(f"Raw data file not found: {csv_path}")
    
    df_raw = load_raw_data(spark, csv_path)
    
    # Get existing users
    from processors.gym_members.config import LOCAL_FILE as GYM_FILE
    if Path(GYM_FILE).exists():
        from processors.gym_members.transform import transform_gym_members
        df_users, _, _ = transform_gym_members(spark, str(GYM_FILE))
    else:
        df_users = spark.createDataFrame([
            (str(uuid.uuid4()),) for _ in range(100)
        ], ["user_id"])
    
    # Get activity types (need for workout_session)
    from processors.fitness_tracker.transform import create_activity_types
    df_activities = create_activity_types(spark)
    
    # Get exercises (need for session_detail)
    from processors.exercises.config import LOCAL_FILE as EXERCISE_FILE
    if Path(EXERCISE_FILE).exists():
        from processors.exercises.transform import transform_exercises
        df_exercises = transform_exercises(spark, str(EXERCISE_FILE))
    else:
        df_exercises = None
    
    # Transform to workout sessions
    df_sessions = transform_to_workout_session_performance(df_raw, df_users, df_activities)
    
    # Transform to session details if exercises available
    df_details = None
    if df_exercises is not None and df_exercises.count() > 0:
        df_details = transform_to_session_detail(df_raw, df_sessions, df_exercises)
    
    # Clean and validate
    df_sessions, df_details = clean_and_validate(df_sessions, df_details)
    
    print("✅ Transform completed")
    return df_sessions, df_details

if __name__ == "__main__":
    from spark.session import get_spark, stop_spark
    from processors.body_performance.config import LOCAL_FILE
    
    spark = get_spark("Transform_Body_Performance")
    
    try:
        df_sessions, df_details = transform_body_performance(spark, str(LOCAL_FILE))
        
        print("\n" + "=" * 60)
        print("📋 TRANSFORMED DATA PREVIEW")
        print("=" * 60)
        
        print("\n💪 WORKOUT SESSIONS:")
        df_sessions.show(10, truncate=False)
        
        if df_details is not None:
            print("\n🏋️ SESSION DETAILS:")
            df_details.show(10, truncate=False)
        
        print(f"\n📊 Statistics:")
        print(f"Workout sessions: {df_sessions.count()}")
        if df_details:
            print(f"Session details: {df_details.count()}")
        
    finally:
        stop_spark()
