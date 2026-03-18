from typing import List

from pyspark.sql import DataFrame
from pyspark.sql.functions import lit

from utils.logger import get_logger

logger = get_logger(__name__)

def load_raw_data(spark, csv_path: str) -> DataFrame:
    """Load raw CSV data with Spark without schema inference for faster reads."""
    return spark.read.option("header", True).option("inferSchema", False).csv(csv_path)


def ensure_columns(df: DataFrame, col_names: List[str], cast_type: str = "string") -> DataFrame:
    """
    Ensure all listed columns exist in the DataFrame.
    Any column that is absent is added as NULL (cast to cast_type).
    """
    for col_name in col_names:
        if col_name not in df.columns:
            df = df.withColumn(col_name, lit(None).cast(cast_type))
    return df

