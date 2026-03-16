
from pathlib import Path
from typing import Dict, List

from pyspark.sql import DataFrame
from pyspark.sql.functions import lit

from utils.logger import get_logger

logger = get_logger(__name__)

def load_raw_data(spark, csv_path: str) -> DataFrame:
    """Load raw CSV data with Spark"""
    df = spark.read.csv(csv_path, header=True, inferSchema=True)
    return df


# Save to parquet is useful for local testing and debugging, but in production we primarily load to PostgreSQL
def save_to_parquet(df: DataFrame, output_path: str):
    """Save DataFrame to Parquet format"""
    df.write.mode("overwrite").parquet(output_path)


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


def save_to_csv(df: DataFrame, output_path: str):
    """Save DataFrame to CSV format with proper quoting for multiline/comma values."""
    df.coalesce(1).write.mode("overwrite") \
        .option("header", "true") \
        .option("quote", '"') \
        .option("escape", '"') \
        .option("quoteAll", "false") \
        .csv(output_path)


def split_and_save_per_table(
    df: DataFrame,
    processed_dir: str,
    table_column_map: Dict[str, Dict[str, str]],
) -> None:
    """
    Split a flat DataFrame into multiple per-table CSVs.

    Each entry in table_column_map defines one output table:
        {
            "table_name": {
                "flat_col":   "schema_col",   # rename flat_col to schema_col
                "same_col":   "same_col",     # direct passthrough (no rename)
            }
        }

    Missing flat columns are added as NULL rather than raising an error.

    Output path per table:
        {processed_dir}/{table_name}/   <- Spark part-*.csv folder

    Stage 7 of main.py discovers tables by scanning these folder names, so
    each folder name must exactly match the DB table name.
    """
    processed_dir = Path(processed_dir)

    for table_name, col_map in table_column_map.items():
        # Rename flat columns → schema column names, adding NULLs for missing ones
        schema_cols = []
        working_df = df
        for flat_col, schema_col in col_map.items():
            if flat_col in working_df.columns:
                if flat_col != schema_col:

                    if schema_col in working_df.columns:
                        working_df = working_df.drop(schema_col)
                    working_df = working_df.withColumnRenamed(flat_col, schema_col)
            else:
                working_df = working_df.withColumn(schema_col, lit(None).cast("string"))
            schema_cols.append(schema_col)

        table_df = working_df.select(*schema_cols)

        out_path = str(processed_dir / table_name)
        table_df.coalesce(1).write.mode("overwrite") \
            .option("header", "true") \
            .option("quote", '"') \
            .option("escape", '"') \
            .option("quoteAll", "false") \
            .csv(out_path)

        logger.info(f"✅ Saved {table_df.count():,} rows → {out_path}")
