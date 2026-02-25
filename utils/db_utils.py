"""
Database utility functions for ETL pipelines
Includes connection helpers, idempotency checks, and retry logic
"""
import os
import time
from typing import Optional, Dict, Any
from pyspark.sql import SparkSession, DataFrame
from utils.logger import get_logger

logger = get_logger(__name__)

def get_jdbc_url() -> str:
    """Build PostgreSQL JDBC URL from environment variables"""
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    dbname = os.getenv("DB_NAME", "healthai_db")
    return f"jdbc:postgresql://{host}:{port}/{dbname}"

def get_db_properties() -> Dict[str, str]:
    """Get PostgreSQL connection properties from environment"""
    return {
        "user": os.getenv("DB_USER", "healthai"),
        "password": os.getenv("DB_PASSWORD", "password"),
        "driver": "org.postgresql.Driver",
        "stringtype": "unspecified"  # Allow PostgreSQL to cast strings to UUIDs
    }

def read_table_with_retry(
    spark: SparkSession, 
    table: str, 
    max_retries: int = 3,
    retry_delay: int = 2
) -> Optional[DataFrame]:
    """
    Read table from PostgreSQL with retry logic
    
    Args:
        spark: SparkSession
        table: Table name
        max_retries: Maximum number of retry attempts
        retry_delay: Delay in seconds between retries
        
    Returns:
        DataFrame or None if table doesn't exist or read fails
    """
    jdbc_url = get_jdbc_url()
    db_properties = get_db_properties()
    
    for attempt in range(max_retries):
        try:
            df = spark.read.jdbc(url=jdbc_url, table=table, properties=db_properties)
            count = df.count()
            
            if count == 0:
                logger.info(f"Table '{table}' exists but is empty")
                return None
            else:
                logger.info(f"Read {count:,} records from '{table}'")
                return df
                
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed to read '{table}': {e}")
                time.sleep(retry_delay)
            else:
                logger.info(f"Table '{table}' not accessible (may not exist yet): {e}")
                return None
    
    return None

def check_records_exist(
    spark: SparkSession,
    table: str,
    id_column: str,
    ids_to_check: list
) -> set:
    """
    Check which IDs already exist in the database
    
    Args:
        spark: SparkSession
        table: Table name
        id_column: Primary key column name
        ids_to_check: List of IDs to check
        
    Returns:
        Set of IDs that already exist in database
    """
    df_existing = read_table_with_retry(spark, table, max_retries=1)
    
    if df_existing is None:
        logger.info(f"No existing records in '{table}'")
        return set()
    
    try:
        existing_ids = {row[id_column] for row in df_existing.select(id_column).collect()}
        overlap = existing_ids.intersection(set(ids_to_check))
        
        if overlap:
            logger.info(f"Found {len(overlap):,} existing records in '{table}'")
        
        return overlap
        
    except Exception as e:
        logger.warning(f"Could not check existing IDs in '{table}': {e}")
        return set()

def load_with_idempotency(
    df: DataFrame,
    table: str,
    id_column: str,
    mode: str = "append"
) -> bool:
    """
    Load data to PostgreSQL with idempotency check
    
    Args:
        df: DataFrame to load
        table: Target table name
        id_column: Primary key column name
        mode: Write mode (append, overwrite, ignore)
        
    Returns:
        True if successful, False otherwise
    """
    jdbc_url = get_jdbc_url()
    db_properties = get_db_properties()
    
    try:
        # Get IDs to insert
        ids_to_insert = {row[id_column] for row in df.select(id_column).collect()}
        logger.info(f"Preparing to load {len(ids_to_insert):,} records to '{table}'")
        
        # Check existing records
        existing_ids = check_records_exist(df.sparkSession, table, id_column, list(ids_to_insert))
        
        # Filter out existing records
        if existing_ids:
            logger.info(f"Skipping {len(existing_ids):,} existing records")
            df_to_insert = df.filter(~df[id_column].isin(list(existing_ids)))
            new_count = df_to_insert.count()
            
            if new_count == 0:
                logger.info(f"All records already exist in '{table}' - skipping load")
                return True
            else:
                logger.info(f"Loading {new_count:,} new records to '{table}'")
        else:
            df_to_insert = df
            logger.info(f"Loading all {df.count():,} records to '{table}'")
        
        # Perform the load
        df_to_insert.write.jdbc(
            url=jdbc_url,
            table=table,
            mode=mode,
            properties=db_properties
        )
        
        logger.info(f"✅ Successfully loaded data to '{table}'")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to load data to '{table}': {e}")
        return False

def execute_with_retry(
    func,
    max_retries: int = 3,
    retry_delay: int = 2,
    operation_name: str = "operation"
) -> Any:
    """
    Execute a function with retry logic
    
    Args:
        func: Function to execute
        max_retries: Maximum number of retry attempts
        retry_delay: Delay in seconds between retries
        operation_name: Name for logging
        
    Returns:
        Function result or None if all attempts fail
    """
    for attempt in range(max_retries):
        try:
            result = func()
            logger.info(f"✅ {operation_name} succeeded")
            return result
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} for {operation_name} failed: {e}")
                time.sleep(retry_delay)
            else:
                logger.error(f"❌ {operation_name} failed after {max_retries} attempts: {e}")
                raise
    
    return None
