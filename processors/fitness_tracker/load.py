"""
Load fitness tracker data to PostgreSQL, Parquet, and CSV
Loads 2 tables: ACTIVITY_TYPE, WORKOUT_SESSION
"""
import os
from pyspark.sql import DataFrame
from processors.fitness_tracker.config import PROCESSED_DIR
from utils.db_utils import load_with_idempotency, get_jdbc_url, get_db_properties
from utils.logger import get_logger

logger = get_logger(__name__)

def load_to_postgres(spark, df_activities: DataFrame, df_sessions: DataFrame):
    """Load dataframes to PostgreSQL tables with idempotency checks"""
    
    try:
        # Load ACTIVITY_TYPE with idempotency check
        logger.info("Loading activity types...")
        success_activities = load_with_idempotency(
            df_activities,
            table="activity_type",
            id_column="activity_id",
            mode="append"
        )
        
        if not success_activities:
            return False
        
        # Load WORKOUT_SESSION with idempotency check
        logger.info("Loading workout sessions...")
        success_sessions = load_with_idempotency(
            df_sessions,
            table="workout_session",
            id_column="session_id",
            mode="append"
        )
        
        return success_sessions
        
    except Exception as e:
        logger.error(f"PostgreSQL load failed: {e}")
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
        logger.error(f"Parquet save failed: {e}")
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
        logger.error(f"CSV export failed: {e}")
        return False

def load_fitness_tracker(spark, df_activities: DataFrame, df_sessions: DataFrame) -> bool:
    """Load all fitness tracker data to all destinations with idempotency"""
    logger.info("⏳ Loading data...")
    logger.info(f"Activity types: {df_activities.count():,}")
    logger.info(f"Workout sessions: {df_sessions.count():,}")
    
    success = True
    
    # Load to PostgreSQL with idempotency checks
    if not load_to_postgres(spark, df_activities, df_sessions):
        success = False
    
    # Save to Parquet
    if not save_to_parquet(df_activities, df_sessions):
        success = False
    
    # Export to CSV
    if not export_to_csv(df_activities, df_sessions):
        success = False
    
    if success:
        logger.info("✅ Load completed")
    
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
