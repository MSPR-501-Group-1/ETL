"""
Load body performance data to PostgreSQL, Parquet, and CSV
Loads 2 tables: WORKOUT_SESSION, SESSION_DETAIL
"""
import os
from pyspark.sql import DataFrame
from processors.body_performance.config import PROCESSED_DIR

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

def load_to_postgres(spark, df_sessions: DataFrame, df_details: DataFrame = None):
    """Load dataframes to PostgreSQL tables"""
    jdbc_url = get_jdbc_url()
    db_properties = get_db_properties()
    
    try:
        # Load WORKOUT_SESSION table
        df_sessions.write \
            .jdbc(url=jdbc_url, table="workout_session", mode="append", properties=db_properties)
        
        # Load SESSION_DETAIL table if available
        if df_details is not None:
            df_details.write \
                .jdbc(url=jdbc_url, table="session_detail", mode="append", properties=db_properties)
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: PostgreSQL load failed: {e}")
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
        print(f"❌ FAILED: Parquet save failed: {e}")
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
        print(f"❌ FAILED: CSV export failed: {e}")
        return False

def load_body_performance(spark, df_sessions: DataFrame, df_details: DataFrame = None):
    """Load all body performance data to all destinations"""
    print("⏳ Loading data...")
    
    success = True
    
    # Load to PostgreSQL
    if not load_to_postgres(spark, df_sessions, df_details):
        success = False
    
    # Save to Parquet
    if not save_to_parquet(df_sessions, df_details):
        success = False
    
    # Export to CSV
    if not export_to_csv(df_sessions, df_details):
        success = False
    
    if success:
        print("✅ Load completed")
    
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
