"""
Load gym members data to PostgreSQL, Parquet, and CSV
Loads 3 tables: USER, USER_PROFILE, USER_METRICS
"""
import os
from pyspark.sql import DataFrame
from processors.gym_members.config import PROCESSED_DIR
from utils.db_utils import load_with_idempotency
from utils.logger import get_logger

logger = get_logger(__name__)

def load_to_postgres(spark, df_user: DataFrame, df_profile: DataFrame, df_metrics: DataFrame):
    """Load 3 dataframes to PostgreSQL tables with idempotency checks"""
    logger.info("⏳ Loading gym members data...")
    
    try:
        # Load USER table with idempotency check (quoted because 'user' is reserved)
        logger.info("Loading users...")
        success_user = load_with_idempotency(
            df_user,
            table='"user"',
            id_column="user_id",
            mode="append"
        )
        
        if not success_user:
            return False
        
        # Load USER_PROFILE with idempotency check
        logger.info("Loading user profiles...")
        success_profile = load_with_idempotency(
            df_profile,
            table="user_profile",
            id_column="profile_id",
            mode="append"
        )
        
        if not success_profile:
            return False
        
        # Load USER_METRICS with idempotency check
        logger.info("Loading user metrics...")
        success_metrics = load_with_idempotency(
            df_metrics,
            table="user_metrics",
            id_column="metric_id",
            mode="append"
        )
        
        return success_metrics
        
    except Exception as e:
        logger.error(f"PostgreSQL load error: {e}")
        return False

def save_to_parquet(df_user: DataFrame, df_profile: DataFrame, df_metrics: DataFrame):
    """Save dataframes to Parquet format"""
    try:
        # Save USER
        user_parquet = PROCESSED_DIR / "user.parquet"
        df_user.write.mode("overwrite").parquet(str(user_parquet))
        
        # Save USER_PROFILE
        profile_parquet = PROCESSED_DIR / "user_profile.parquet"
        df_profile.write.mode("overwrite").parquet(str(profile_parquet))
        
        # Save USER_METRICS
        metrics_parquet = PROCESSED_DIR / "user_metrics.parquet"
        df_metrics.write.mode("overwrite").parquet(str(metrics_parquet))
        
        return True
        
    except Exception as e:
        logger.error(f"Parquet save failed: {e}")
        return False

def export_to_csv(df_user: DataFrame, df_profile: DataFrame, df_metrics: DataFrame):
    """Export dataframes to CSV format"""
    try:
        # Export USER
        user_csv_dir = PROCESSED_DIR / "user_csv"
        df_user.coalesce(1).write.mode("overwrite") \
            .option("header", "true") \
            .csv(str(user_csv_dir))
        
        # Export USER_PROFILE
        profile_csv_dir = PROCESSED_DIR / "user_profile_csv"
        df_profile.coalesce(1).write.mode("overwrite") \
            .option("header", "true") \
            .csv(str(profile_csv_dir))
        
        # Export USER_METRICS
        metrics_csv_dir = PROCESSED_DIR / "user_metrics_csv"
        df_metrics.coalesce(1).write.mode("overwrite") \
            .option("header", "true") \
            .csv(str(metrics_csv_dir))
        
        return True
        
    except Exception as e:
        logger.error(f"CSV export error: {e}")
        return False

def load_gym_members(spark, df_user: DataFrame, df_profile: DataFrame, df_metrics: DataFrame):
    """Load all gym members data to all destinations"""
    logger.info("📦 Loading gym members data...")
    
    success = True
    
    # Load to PostgreSQL
    if not load_to_postgres(spark, df_user, df_profile, df_metrics):
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
