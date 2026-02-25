"""
Load fitness tracker data to PostgreSQL, Parquet, and CSV
Loads 2 tables: ACTIVITY_TYPE, WORKOUT_SESSION
"""
import os
from pyspark.sql import DataFrame
from processors.fitness_tracker.config import PROCESSED_DIR

def get_db_properties():
    """Get PostgreSQL connection properties from environment"""
    return {
        "user": os.getenv("DB_USER", "healthai"),
        "password": os.getenv("DB_PASSWORD", "password"),
        "driver": "org.postgresql.Driver",
        "stringtype": "unspecified"  # Allow PostgreSQL to cast strings to UUIDs
    }

def get_jdbc_url():
    """Build PostgreSQL JDBC URL from environment"""
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    dbname = os.getenv("DB_NAME", "healthai_db")
    return f"jdbc:postgresql://{host}:{port}/{dbname}"

def load_to_postgres(spark, df_activities: DataFrame, df_sessions: DataFrame):
    """Load 2 dataframes to PostgreSQL tables"""
    jdbc_url = get_jdbc_url()
    db_properties = get_db_properties()
    
    try:
        # Load ACTIVITY_TYPE table
        df_activities.write \
            .jdbc(url=jdbc_url, table="activity_type", mode="append", properties=db_properties)
        
        # Load WORKOUT_SESSION table
        df_sessions.write \
            .jdbc(url=jdbc_url, table="workout_session", mode="append", properties=db_properties)
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: PostgreSQL load failed: {e}")
        return False

def save_to_parquet(df_activities: DataFrame, df_sessions: DataFrame):
    """Save dataframes to Parquet format"""
    try:
        # Save ACTIVITY_TYPE
        activities_parquet = PROCESSED_DIR / "activity_type.parquet"
        df_activities.write.mode("overwrite").parquet(str(activities_parquet))
        
        # Save WORKOUT_SESSION
        sessions_parquet = PROCESSED_DIR / "workout_session.parquet"
        df_sessions.write.mode("overwrite").parquet(str(sessions_parquet))
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Parquet save failed: {e}")
        return False

def export_to_csv(df_activities: DataFrame, df_sessions: DataFrame):
    """Export dataframes to CSV format"""
    try:
        # Export ACTIVITY_TYPE
        activities_csv_dir = PROCESSED_DIR / "activity_type_csv"
        df_activities.coalesce(1).write.mode("overwrite") \
            .option("header", "true") \
            .csv(str(activities_csv_dir))
        
        # Export WORKOUT_SESSION
        sessions_csv_dir = PROCESSED_DIR / "workout_session_csv"
        df_sessions.coalesce(1).write.mode("overwrite") \
            .option("header", "true") \
            .csv(str(sessions_csv_dir))
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: CSV export failed: {e}")
        return False

def load_fitness_tracker(spark, df_activities: DataFrame, df_sessions: DataFrame):
    """Load all fitness tracker data to all destinations"""
    print("⏳ Loading data...")
    
    success = True
    
    # Load to PostgreSQL
    if not load_to_postgres(spark, df_activities, df_sessions):
        success = False
    
    # Save to Parquet
    if not save_to_parquet(df_activities, df_sessions):
        success = False
    
    # Export to CSV
    if not export_to_csv(df_activities, df_sessions):
        success = False
    
    if success:
        print("✅ Load completed")
    
    return success

if __name__ == "__main__":
    from spark.session import get_spark, stop_spark
    from processors.fitness_tracker.transform import transform_fitness_tracker
    from processors.fitness_tracker.config import LOCAL_FILE
    
    spark = get_spark("Load_Fitness_Tracker")
    
    try:
        print("🔄 Running transform...")
        df_activities, df_sessions = transform_fitness_tracker(spark, str(LOCAL_FILE))
        
        print("\n🚀 Starting load...")
        success = load_fitness_tracker(spark, df_activities, df_sessions)
        
        import sys
        sys.exit(0 if success else 1)
        
    finally:
        stop_spark()
