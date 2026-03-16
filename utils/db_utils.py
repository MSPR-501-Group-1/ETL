"""
Database utility functions for ETL pipelines
Includes connection helpers, idempotency checks, and retry logic
"""
import os
import time
from typing import Dict, List, List, Optional, Any
from pyspark.sql import SparkSession, DataFrame
from utils.logger import get_logger

logger = get_logger(__name__)

def get_db_config() -> dict:
    """Get database configuration from environment"""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "database": os.getenv("DB_NAME", "healthai_db"),
        "user": os.getenv("DB_USER", "healthai"),
        "password": os.getenv("DB_PASSWORD", "password"),
        "driver": "org.postgresql.Driver",
        "stringtype": "unspecified"  # Allow PostgreSQL to cast strings to UUIDs
    }

def get_jdbc_url() -> str:
    """Build PostgreSQL JDBC URL"""
    config = get_db_config()
    return f"jdbc:postgresql://{config['host']}:{config['port']}/{config['database']}"

def read_table_with_retry(
    spark: SparkSession, 
    table: str, 
    max_retries: int = 3,
    retry_delay: int = 2
) -> Optional[DataFrame]:
 
    jdbc_url = get_jdbc_url()
    db_properties = get_db_config()
    
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


DB_TABLE_SCHEMAS: Dict[str, List[str]] = {
    # Reference / seed tables (must be loaded first)
    "health_goal": [
        "goal_id", "label", "description",
    ],
    "role": [
        "role_id", "role_type", "is_system",
    ],
    # Core user tables
    "user_profile": [
        "user_id",
        "height_cm", "current_weight_kg", "activity_level_ref",
        "allergies", "diet_type", "updated_at",
        "goal_id",
    ],
    "user_": [
        "user_id", "email", "password_hash",
        "first_name", "last_name", "birth_date", "gender_code",
        "created_at", "is_active", "role_code",
        "role_id", "user_id_1",
    ],
    # Metrics (no user_id — linked via gets junction)
    "user_metrics": [
        "metric_id", "recorded_date",
        "weight_kg", "body_fat_pourcentage", "steps", "calories_burned",
        "heart_rate_avg", "heart_rate_max", "sleep_hours",
    ],
    # Junction: health_goal ↔ user_metrics
    "gets": [
        "goal_id", "metric_id",
    ],
    # Exercise / workout tables
    "exercise": [
        "exercise_id", "name", "body_part_target", "video_url", "description",
        "difficulty_level", "equipment_required", "category",
    ],
    "workout_session": [
        "session_id", "start_time", "duration_time", "calories_burned", "notes",
        "user_id",
    ],
    "exercice_details": [
        "exercice_details_id", "sets", "reps",
        "exercise_id", "session_id",
    ],
    # Food / nutrition
    "ingredients": [
        "ingredients_id", "name",
        "calories_g", "fat_g", "nutriscore", "category",
        "fiber_g", "sugar_g", "sodium_mg", "cholesterol_mg",
        "protein_g", "carbs_g",
    ],
}