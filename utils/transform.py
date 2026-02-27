
from pyspark.pandas import DataFrame

from utils import logger

def load_raw_data(spark, csv_path: str) -> DataFrame:
    """Load raw CSV data with Spark"""
    df = spark.read.csv(csv_path, header=True, inferSchema=True)
    return df

# Save to parquet is useful for local testing and debugging, but in production we primarily load to PostgreSQL
def save_to_parquet(df: DataFrame, output_path: str):
    """Save DataFrame to Parquet format"""
    df.write.mode("overwrite").parquet(output_path)

def save_to_csv(df: DataFrame, output_path: str):
    """Save DataFrame to CSV format"""
    df.coalesce(1).write.mode("overwrite") \
        .option("header", "true") \
        .csv(output_path)
    
def export_to_csv(df_user: DataFrame, df_profile: DataFrame, df_metrics: DataFrame, PROCESSED_DIR: Path):
    """Export dataframes to CSV format"""
    try:
        # Export USER
        user_csv_dir = PROCESSED_DIR / "user_csv"
        # Coalesce is a method to reduce the number of partitions to 1, which results in a single CSV file output
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