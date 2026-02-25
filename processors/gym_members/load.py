"""
Load gym members data to PostgreSQL, Parquet, and CSV
Loads 3 tables: USER, USER_PROFILE, USER_METRICS
"""
import os
from pyspark.sql import DataFrame
from processors.gym_members.config import PROCESSED_DIR

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

def load_to_postgres(spark, df_user: DataFrame, df_profile: DataFrame, df_metrics: DataFrame):
    """Load 3 dataframes to PostgreSQL tables"""
    print("⏳ Loading gym members data...")
    
    jdbc_url = get_jdbc_url()
    db_properties = get_db_properties()
    
    try:
        # Load USER table
        df_user.write \
            .jdbc(url=jdbc_url, table="user", mode="append", properties=db_properties)
        
        # Load USER_PROFILE table
        df_profile.write \
            .jdbc(url=jdbc_url, table="user_profile", mode="append", properties=db_properties)
        
        # Load USER_METRICS table
        df_metrics.write \
            .jdbc(url=jdbc_url, table="user_metrics", mode="append", properties=db_properties)
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: PostgreSQL load error - {e}")
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
        print(f"❌ FAILED: Parquet save error - {e}")
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
        print(f"❌ FAILED: CSV export error - {e}")
        return False

def load_gym_members(spark, df_user: DataFrame, df_profile: DataFrame, df_metrics: DataFrame):
    """Load all gym members data to all destinations"""
    print("=" * 60)
    print("📦 LOAD GYM MEMBERS DATA")
    print("=" * 60)
    
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
        print("✅ Load completed")
    
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
