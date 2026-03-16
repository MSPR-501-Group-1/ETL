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
import os

def seed_reference_data() -> bool:
    """
    Insert required reference rows into `role` and `health_goal` before any
    pipeline data is loaded.  Uses ON CONFLICT DO NOTHING so re-runs are safe.

    role_id values are derived at runtime via generate_role_uuid() — the same
    function used in the pipelines — so the FK from user_.role_id always matches.
    """
    from utils.uuid_utils import generate_role_uuid

    config = get_db_config()
    roles = [
        (generate_role_uuid("FREEMIUM"),    "FREEMIUM",     True),
        (generate_role_uuid("PREMIUM"),     "PREMIUM",      True),
        (generate_role_uuid("PREMIUM_PLUS"),"PREMIUM_PLUS", True),
        (generate_role_uuid("B2B"),         "B2B",          True),
        (generate_role_uuid("ADMIN"),       "ADMIN",        True),
    ]
    # Minimal health_goal rows — goal_id is nullable in pipelines but the
    # table must exist with at least a couple of rows for future FK use.
    from utils.uuid_utils import NAMESPACE_PROFILE
    import uuid
    _hg_ns = uuid.UUID('6ba7b819-9dad-11d1-80b4-00c04fd430c8')
    def _hg_id(label): return str(uuid.uuid5(_hg_ns, label))
    health_goals = [
        (_hg_id("LOSE_WEIGHT"),      "LOSE_WEIGHT",      "Reduce body fat"),
        (_hg_id("GAIN_MUSCLE"),      "GAIN_MUSCLE",      "Increase muscle mass"),
        (_hg_id("MAINTAIN_WEIGHT"),  "MAINTAIN_WEIGHT",  "Maintain current weight"),
        (_hg_id("IMPROVE_STAMINA"),  "IMPROVE_STAMINA",  "Improve cardiovascular endurance"),
    ]
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
                for role_id, role_type, is_system in roles:
                    cur.execute(
                        'INSERT INTO "role" (role_id, role_type, is_system) '
                        'VALUES (%s, %s::role_type_enum, %s) ON CONFLICT DO NOTHING',
                        (role_id, role_type, is_system),
                    )
                for goal_id, label, description in health_goals:
                    cur.execute(
                        'INSERT INTO health_goal (goal_id, label, description) '
                        'VALUES (%s, %s, %s) ON CONFLICT DO NOTHING',
                        (goal_id, label, description),
                    )
        conn.close()
        logger.info(f"✅ Reference data seeded: {len(roles)} roles, {len(health_goals)} health goals")
        return True
    except Exception as e:
        logger.error(f"seed_reference_data failed: {e}")
        return False

def init_db_schema(sql_path: str = None) -> bool:

    config = get_db_config()
    if sql_path is None:
        sql_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "01_initdb.sql")
    if not os.path.exists(sql_path):
        logger.error(f"init_db_schema: SQL file not found: {sql_path}")
        return False
    try:
        with open(sql_path, "r", encoding="utf-8") as f:
            sql = f.read()
        conn = psycopg2.connect(
            host=config["host"],
            port=int(config["port"]),
            dbname=config["database"],
            user=config["user"],
            password=config["password"],
        )
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
        conn.close()
        logger.info(f"✅ Database schema initialized from {sql_path}")
        return True
    except Exception as e:
        logger.error(f"init_db_schema failed: {e}")
        return False

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

            # Count and cache before writing so we don't re-trigger the full
            # Spark DAG a second time just for the log message.
            result_df = result_df.cache()
            row_count = result_df.count()

            # --- Write to a single CSV file ---
            # quote/escape options ensure multiline or comma-containing fields
            # (e.g. exercise descriptions) are properly quoted so psycopg2 COPY
            # can parse the file without "extra data after last expected column".
            tmp_dir = output_dir / f"_{table_name}_tmp"
            result_df.coalesce(1).write.mode("overwrite") \
                .option("header", "true") \
                .option("nullValue", "") \
                .option("quote", '"') \
                .option("escape", '"') \
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
