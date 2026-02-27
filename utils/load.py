"""
Common load utilities for all ETL pipelines.

Two main methods:
  - aggregate_to_csv : merge pipeline DataFrames into one CSV per table, aligned to the DB schema
  - load_csv_to_postgres : bulk-load a CSV file into PostgreSQL via COPY
"""
import csv
import glob
import shutil
from pathlib import Path
from typing import Dict, List

import psycopg2
from pyspark.sql import DataFrame
from pyspark.sql.functions import lit

from utils.logger import get_logger
from utils.db_utils import DB_TABLE_SCHEMAS, get_db_config

logger = get_logger(__name__)

def aggregate_to_csv(
    table_dataframes: Dict[str, List[DataFrame]],
    output_dir: Path,
) -> Dict[str, Path]:
    """
    Aggregate one or more pipeline DataFrames per DB table into a single CSV.
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results: Dict[str, Path] = {}

    for table_name, dataframes in table_dataframes.items():
        if not dataframes:
            logger.warning(f"No DataFrames provided for table '{table_name}', skipping")
            continue

        schema_cols = DB_TABLE_SCHEMAS.get(table_name)
        if not schema_cols:
            logger.warning(f"No DB schema defined for table '{table_name}', skipping")
            continue

        try:
            # --- Union all DataFrames for this table ---
            # Before union, align columns so every DF has the same set
            all_cols = set()
            for df in dataframes:
                all_cols.update(df.columns)

            aligned = []
            for df in dataframes:
                for col_name in all_cols:
                    if col_name not in df.columns:
                        df = df.withColumn(col_name, lit(None).cast("string"))
                aligned.append(df.select(sorted(all_cols)))

            combined_df = aligned[0]
            for df in aligned[1:]:
                combined_df = combined_df.union(df)

            # --- Align to DB schema ---
            # Add columns that exist in the schema but not in the data
            for col_name in schema_cols:
                if col_name not in combined_df.columns:
                    combined_df = combined_df.withColumn(col_name, lit(None).cast("string"))

            # Select only schema columns, in schema order
            result_df = combined_df.select(schema_cols)

            # --- Write to a single CSV file ---
            tmp_dir = output_dir / f"_{table_name}_tmp"
            result_df.coalesce(1).write.mode("overwrite") \
                .option("header", "true") \
                .option("nullValue", "") \
                .csv(str(tmp_dir))

            # Spark writes part-*.csv inside a directory; move it to the final path
            part_files = glob.glob(str(tmp_dir / "part-*.csv"))
            if not part_files:
                logger.error(f"Spark produced no CSV file for table '{table_name}'")
                shutil.rmtree(str(tmp_dir), ignore_errors=True)
                continue

            csv_path = output_dir / f"{table_name}.csv"
            shutil.move(part_files[0], str(csv_path))
            shutil.rmtree(str(tmp_dir), ignore_errors=True)

            row_count = result_df.count()
            results[table_name] = csv_path
            logger.info(f"✅ {table_name}.csv written — {row_count:,} rows, {len(schema_cols)} columns")

        except Exception as e:
            logger.error(f"aggregate_to_csv failed for table '{table_name}': {e}")

    return results


def load_csv_to_postgres(csv_path: Path, table_name: str) -> bool:

    config = get_db_config()
    csv_path = Path(csv_path)

    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        return False

    try:
        conn = psycopg2.connect(
            host=config["host"],
            port=int(config["port"]),
            dbname=config["database"],
            user=config["user"],
            password=config["password"],
        )

        with conn:
            with conn.cursor() as cur:
                with open(csv_path, "r", encoding="utf-8", newline="") as f:
                    # Read header to build column list
                    reader = csv.reader(f)
                    headers = next(reader)

                    # Quote table name (handles reserved words like "user")
                    quoted_table = f'"{table_name}"'
                    quoted_cols = ", ".join(f'"{c}"' for c in headers)

                    # Rewind past the header for COPY
                    f.seek(0)
                    next(f)

                    copy_sql = (
                        f"COPY {quoted_table} ({quoted_cols}) "
                        f"FROM STDIN WITH (FORMAT CSV, NULL '', HEADER FALSE)"
                    )
                    cur.copy_expert(copy_sql, f)
                    row_count = cur.rowcount

        conn.close()
        logger.info(f"✅ Loaded {row_count:,} rows into '{table_name}'")
        return True

    except Exception as e:
        logger.error(f"load_csv_to_postgres failed for table '{table_name}': {e}")
        return False


def log_etl_execution(spark, status: str, records_loaded: int, error_msg: str = None, SOURCE_NAME: str = ""):
    """Log ETL pipeline execution metadata to the etl_execution table."""
    from pyspark.sql.functions import current_timestamp

    log_df = spark.createDataFrame([(
        SOURCE_NAME,
        status,
        records_loaded,
        error_msg or "",
        "docker_etl",
    )], ["source_name", "status", "records_loaded", "error_message", "triggered_by"])

    log_df = log_df \
        .withColumn("started_at", current_timestamp()) \
        .withColumn("ended_at", current_timestamp())

    try:
        from utils.db_utils import get_jdbc_url

        connection_properties = {
            "user": get_db_config()["user"],
            "password": get_db_config()["password"],
            "driver": "org.postgresql.Driver",
            "stringtype": "unspecified",
        }

        log_df.write.jdbc(
            url=get_jdbc_url(),
            table="etl_execution",
            mode="append",
            properties=connection_properties,
        )
    except Exception:
        pass  # Metadata logging must never break the main pipeline
