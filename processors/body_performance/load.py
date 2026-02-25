"""
Load body performance data to PostgreSQL, Parquet, and CSV
Loads 2 tables: WORKOUT_SESSION, SESSION_DETAIL
"""
import os
from pyspark.sql import DataFrame
from processors.body_performance.config import PROCESSED_DIR
from utils.db_utils import load_with_idempotency, get_jdbc_url, get_db_properties
from utils.logger import get_logger

logger = get_logger(__name__)

def load_to_postgres(spark, df_sessions: DataFrame, df_details: DataFrame = None):
    """Load dataframes to PostgreSQL tables with idempotency checks"""
    
    try:
        # Load WORKOUT_SESSION with idempotency check
        logger.info("Loading workout sessions...")
        success_sessions = load_with_idempotency(
            df_sessions,
            table="workout_session",
            id_column="session_id",
            mode="append"
        )
        
        if not success_sessions:
            return False
        
        # Load SESSION_DETAIL if available
        if df_details is not None:
            logger.info("Loading session details...")
            success_details = load_with_idempotency(
                df_details,
                table="session_detail",
                id_column="detail_id",
                mode="append"
            )
            
            if not success_details:
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"PostgreSQL load failed: {e}")
        return False

def save_to_parquet(df_sessions: DataFrame, df_details: DataFrame = None):
    """Save dataframes to Parquet format"""
    try:
        # Save WORKOUT_SESSION
        sessions_parquet = PROCESSED_DIR / "workout_session.parquet"
        df_sessions.write.mode("overwrite").parquet(str(sessions_parquet))
        
        # Save SESSION_DETAIL if available
        if df_details is not None:
            details_parquet = PROCESSED_DIR / "session_detail.parquet"
            df_details.write.mode("overwrite").parquet(str(details_parquet))
        
        return True
        
    except Exception as e:
        logger.error(f"Parquet save failed: {e}")
        return False

def export_to_csv(df_sessions: DataFrame, df_details: DataFrame = None):
    """Export dataframes to CSV format"""
    try:
        # Export WORKOUT_SESSION
        sessions_csv_dir = PROCESSED_DIR / "workout_session_csv"
        df_sessions.coalesce(1).write.mode("overwrite") \
            .option("header", "true") \
            .csv(str(sessions_csv_dir))
        
        # Export SESSION_DETAIL if available
        if df_details is not None:
            details_csv_dir = PROCESSED_DIR / "session_detail_csv"
            df_details.coalesce(1).write.mode("overwrite") \
                .option("header", "true") \
                .csv(str(details_csv_dir))
        
        return True
        
    except Exception as e:
        logger.error(f"CSV export failed: {e}")
        return False

def load_body_performance(spark, df_sessions: DataFrame, df_details: DataFrame = None) -> bool:
    """Load all body performance data to all destinations with idempotency"""
    logger.info("⏳ Loading data...")
    logger.info(f"Workout sessions: {df_sessions.count():,}")
    if df_details:
        logger.info(f"Session details: {df_details.count():,}")
    
    success = True
    
    # Load to PostgreSQL with idempotency checks
    if not load_to_postgres(spark, df_sessions, df_details):
        success = False
    
    # Save to Parquet
    if not save_to_parquet(df_sessions, df_details):
        success = False
    
    # Export to CSV
    if not export_to_csv(df_sessions, df_details):
        success = False
    
    if success:
        logger.info("✅ Load completed")
    
    return success

if __name__ == "__main__":
    from spark.session import get_spark, stop_spark
    from processors.body_performance.transform import transform_body_performance
    from processors.body_performance.config import LOCAL_FILE
    
    spark = get_spark("Load_Body_Performance")
    
    try:
        print("🔄 Running transform...")
        df_sessions, df_details = transform_body_performance(spark, str(LOCAL_FILE))
        
        print("\n🚀 Starting load...")
        success = load_body_performance(spark, df_sessions, df_details)
        
        import sys
        sys.exit(0 if success else 1)
        
    finally:
        stop_spark()
