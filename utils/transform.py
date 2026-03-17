from typing import List

from pyspark.sql import DataFrame
from pyspark.sql.functions import lit

from utils.logger import get_logger

logger = get_logger(__name__)

def load_raw_data(spark, csv_path: str) -> DataFrame:
    """Load raw CSV data with Spark"""
    df = spark.read.csv(csv_path, header=True, inferSchema=True)
    return df


def ensure_columns(df: DataFrame, col_names: List[str], cast_type: str = "string") -> DataFrame:
    """
    Ensure all listed columns exist in the DataFrame.
    Any column that is absent is added as NULL (cast to cast_type).

    Use this before any select() or when() chain that references column names
    which may or may not be present in the source CSV — PySpark 4.x raises
    AnalysisException at plan-compilation time for missing column references,
    even inside unreachable WHEN branches.
    """
    for col_name in col_names:
        if col_name not in df.columns:
            df = df.withColumn(col_name, lit(None).cast(cast_type))
    return df

