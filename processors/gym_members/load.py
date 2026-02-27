"""
Load gym members data to PostgreSQL, Parquet, and CSV
Loads 3 tables: USER, USER_PROFILE, USER_METRICS
"""
import os
from pyspark.sql import DataFrame
from processors.gym_members.config import PROCESSED_DIR
from utils.db_utils import load_with_idempotency
from utils.load import export_to_csv, load_to_postgres, save_to_parquet
from utils.logger import get_logger

logger = get_logger(__name__)

def load_gym_members(spark, df_user: DataFrame, df_profile: DataFrame, df_metrics: DataFrame):
    """Load all gym members data to all destinations"""
    logger.info("📦 Loading gym members data...")
    
    success = True
    
    # Load to PostgreSQL
    if not load_to_postgres(df_user, df_profile, df_metrics):
        success = False
    
    # Save to Parquet
    if not save_to_parquet(df_user, df_profile, df_metrics):
        success = False
    
    # Export to CSV
    if not export_to_csv(df_user, df_profile, df_metrics):
        success = False
    
    if success:
        logger.info("✅ Load completed")
    
    return success

if __name__ == "__main__":
    from spark.session import get_spark, stop_spark
    from processors.gym_members.transform import transform_gym_members
    from processors.gym_members.config import LOCAL_FILE
    
    spark = get_spark("Load_Gym_Members")
    
    try:
        print("🔄 Running transform...")
        df_user, df_profile, df_metrics = transform_gym_members(spark, str(LOCAL_FILE))
        
        print("\n🚀 Starting load...")
        success = load_gym_members(spark, df_user, df_profile, df_metrics)
        
        import sys
        sys.exit(0 if success else 1)
        
    finally:
        stop_spark()
