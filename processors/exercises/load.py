"""
Load transformed exercises data to PostgreSQL
"""
import os
from pyspark.sql import DataFrame
from datetime import datetime

def get_db_config() -> dict:
    """Get database configuration from environment"""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "database": os.getenv("DB_NAME", "healthai_db"),
        "user": os.getenv("DB_USER", "healthai"),
        "password": os.getenv("DB_PASSWORD", "password")
    }

def get_jdbc_url() -> str:
    """Build PostgreSQL JDBC URL"""
    config = get_db_config()
    return f"jdbc:postgresql://{config['host']}:{config['port']}/{config['database']}"

def save_to_parquet(df: DataFrame, output_path: str):
    """Save DataFrame to Parquet format"""
    df.write.mode("overwrite").parquet(output_path)

def save_to_csv(df: DataFrame, output_path: str):
    """Save DataFrame to CSV format"""
    df.coalesce(1).write.mode("overwrite") \
        .option("header", "true") \
        .csv(output_path)

def save_to_postgres(df: DataFrame, table_name: str = "exercise"):
    """
    Save DataFrame to PostgreSQL using JDBC
    
    Args:
        df: Transformed DataFrame
        table_name: Target table name
    """
    config = get_db_config()
    jdbc_url = get_jdbc_url()
    
    connection_properties = {
        "user": config["user"],
        "password": config["password"],
        "driver": "org.postgresql.Driver",
        "stringtype": "unspecified"  # Allow PostgreSQL to cast strings to appropriate types
    }
    
    try:
        # Write to PostgreSQL
        df.write.jdbc(
            url=jdbc_url,
            table=table_name,
            mode="append",  # Changed from overwrite to avoid FK constraint issues
            properties=connection_properties
        )
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: PostgreSQL load error - {e}")
        return False

def log_etl_execution(spark, status: str, records_loaded: int, error_msg: str = None):
    """Log ETL execution to metadata table"""
    from pyspark.sql.functions import lit, current_timestamp
    
    log_df = spark.createDataFrame([(
        "exercises_source",
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

def load_exercises(spark, df: DataFrame) -> bool:
    """
    Complete load pipeline: Parquet + CSV + PostgreSQL
    
    Args:
        spark: Spark session
        df: Transformed DataFrame
        
    Returns:
        bool: Success status
    """
    print("⏳ Loading exercises data...")
    
    from processors.exercises.config import PROCESSED_DIR
    
    try:
        # 1. Save to Parquet (optimized format)
        parquet_path = str(PROCESSED_DIR / "exercises.parquet")
        save_to_parquet(df, parquet_path)
        
        # 2. Save to CSV (for exports)
        csv_path = str(PROCESSED_DIR / "exercises_csv")
        save_to_csv(df, csv_path)
        
        # 3. Load to PostgreSQL
        success = save_to_postgres(df, "exercise")
        
        if success:
            # Log successful execution
            log_etl_execution(spark, "SUCCESS", df.count())
            print("✅ Load completed")
            return True
        else:
            log_etl_execution(spark, "FAILED", 0, "PostgreSQL load failed")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: Load error - {e}")
        log_etl_execution(spark, "FAILED", 0, str(e))
        return False

if __name__ == "__main__":
    from spark.session import get_spark, stop_spark
    from processors.exercises.transform import transform_exercises
    from processors.exercises.config import LOCAL_FILE
    
    spark = get_spark("Load_Exercises")
    
    try:
        # Transform data first
        print("🔄 Running transformation...")
        df_transformed = transform_exercises(spark, str(LOCAL_FILE))
        
        # Load to destinations
        success = load_exercises(spark, df_transformed)
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 ETL PIPELINE COMPLETED")
            print("=" * 60)
            print(f"✅ Data available in:")
            print(f"   - PostgreSQL: exercise table")
            print(f"   - Parquet: data/processed/exercises.parquet")
            print(f"   - CSV: data/processed/exercises_csv/")
        
    finally:
        stop_spark()
