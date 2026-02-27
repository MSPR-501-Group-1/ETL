
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
