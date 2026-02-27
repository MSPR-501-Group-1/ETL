import os
from pathlib import Path

from pyspark.sql import DataFrame

from utils import logger
from utils.db_utils import get_db_config, get_jdbc_url, load_with_idempotency


# Idempotency check prevents duplicate records in PostgreSQL by checking for existing IDs before inserting new data
def load_to_postgres( df_activities: DataFrame, df_sessions: DataFrame):
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

def save_to_postgres(df: DataFrame, table_name: str):
    """Save DataFrame to PostgreSQL using JDBC"""
    config = get_db_config()
    jdbc_url = get_jdbc_url()
    
    connection_properties = {
        "user": config["user"],
        "password": config["password"],
        "driver": "org.postgresql.Driver",
        "stringtype": "unspecified" 
    }
    
    try:
        df.write.jdbc(
            url=jdbc_url,
            table=table_name,
            mode="overwrite",
            properties=connection_properties
        )
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: PostgreSQL load error - {e}")
        return False

def log_etl_execution(spark, status: str, records_loaded: int, error_msg: str = None, SOURCE_NAME: str = ""):
    """Log ETL execution to metadata table"""
    from pyspark.sql.functions import lit, current_timestamp
    
    log_df = spark.createDataFrame([(
        SOURCE_NAME,
        status,
        records_loaded,
        error_msg or "",
        "docker_etl"
    )], ["source_name", "status", "records_loaded", "error_message", "triggered_by"])
    
    log_df = log_df.withColumn("started_at", current_timestamp()) \
                   .withColumn("ended_at", current_timestamp())
    
    try:
        config = get_db_config()
        jdbc_url = get_jdbc_url()
        
        connection_properties = {
            "user": config["user"],
            "password": config["password"],
            "driver": "org.postgresql.Driver",
            "stringtype": "unspecified"  # Allow PostgreSQL to cast strings to UUIDs
        }
        
        log_df.write.jdbc(
            url=jdbc_url,
            table="etl_execution",
            mode="append",
            properties=connection_properties
        )
    except Exception as e:
        pass
