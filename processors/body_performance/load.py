"""
Load body performance data to PostgreSQL, Parquet, and CSV
Loads 2 tables: WORKOUT_SESSION, SESSION_DETAIL
"""
from pyspark.sql import DataFrame
from processors.body_performance.config import PROCESSED_DIR
from utils.load import (
    save_multiple_to_parquet,
    save_multiple_to_csv,
    save_multiple_to_postgres_with_idempotency,
    log_etl_execution
)
from utils.logger import get_logger

logger = get_logger(__name__)

def load_body_performance(spark, df_sessions: DataFrame, df_details: DataFrame = None) -> bool:
    """
    Load all body performance data to all destinations with idempotency
    
    Args:
        spark: Spark session
        df_sessions: Workout sessions DataFrame
        df_details: Session details DataFrame (optional)
    
    Returns:
        bool: Success status
    """
    logger.info("📦 Loading body performance data...")
    logger.info(f"Workout sessions: {df_sessions.count():,}")
    if df_details:
        logger.info(f"Session details: {df_details.count():,}")
    
    try:
        # Prepare data dictionaries
        parquet_data = {"workout_session": df_sessions}
        csv_data = {"workout_session": df_sessions}
        postgres_data = [(df_sessions, "workout_session", "session_id")]
        
        # Add session details if available
        if df_details:
            parquet_data["session_detail"] = df_details
            csv_data["session_detail"] = df_details
            postgres_data.append((df_details, "session_detail", "detail_id"))
        
        # 1. Save to Parquet
        if not save_multiple_to_parquet(parquet_data, PROCESSED_DIR):
            return False
        
        # 2. Save to CSV
        if not save_multiple_to_csv(csv_data, PROCESSED_DIR):
            return False
        
        # 3. Load to PostgreSQL with idempotency checks
        if not save_multiple_to_postgres_with_idempotency(postgres_data, mode="append"):
            return False
        
        # Log successful execution
        total_records = df_sessions.count()
        if df_details:
            total_records += df_details.count()
        log_etl_execution(spark, "SUCCESS", total_records, SOURCE_NAME="body_performance")
        
        logger.info("✅ Load completed")
        return True
        
    except Exception as e:
        logger.error(f"Load failed: {e}")
        log_etl_execution(spark, "FAILED", 0, str(e), SOURCE_NAME="body_performance")
        return False

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
