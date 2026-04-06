"""
Load utilities for the ETL pipeline.

    - init_db_schema       : run 01_initdb.sql against PostgreSQL
    - save_table_csv       : align DataFrame to schema and write a single CSV
    - load_csv_to_postgres : bulk-load a CSV into PostgreSQL via COPY
"""
import csv
import shutil
from pathlib import Path
from uuid import uuid4

import psycopg2
from pyspark.sql import DataFrame
from pyspark.sql.functions import lit

from utils.db_utils import DB_TABLE_SCHEMAS, get_db_config
from utils.logger import get_logger

logger = get_logger(__name__)

_EXERCISE_MIGRATIONS = [
    'ALTER TABLE exercise ALTER COLUMN name TYPE VARCHAR(200)',
    'ALTER TABLE exercise ALTER COLUMN description TYPE VARCHAR(500)',
    'ALTER TABLE exercise ALTER COLUMN video_url TYPE VARCHAR(200)',
    'ALTER TABLE exercise ALTER COLUMN equipment_required TYPE VARCHAR(100)',
]


def _connect_db(config: dict):
    return psycopg2.connect(
        host=config["host"],
        port=int(config["port"]),
        dbname=config["database"],
        user=config["user"],
        password=config["password"],
    )


def _default_schema_path() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "database" / "01_initdb.sql"


def _apply_migrations(conn, statements: list[str]) -> None:
    for ddl in statements:
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(ddl)
        except Exception as error:
            logger.debug(f"Migration skipped ({type(error).__name__}): {ddl[:60]}")


def init_db_schema(sql_path: str = None) -> bool:

    config = get_db_config()
    conn = None
    try:
        conn = _connect_db(config)

        # Check if schema already exists (e.g. initialized by docker-entrypoint)
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT to_regclass('public.exercise')")
                schema_exists = cur.fetchone()[0] is not None

        if schema_exists:
            logger.info("✅ Database schema already exists, skipping init")
            _apply_migrations(conn, _EXERCISE_MIGRATIONS)
            return True

        # Schema missing — resolve and run the SQL file
        if sql_path is None:
            sql_path = _default_schema_path()
        sql_path = Path(sql_path)

        if not sql_path.exists():
            logger.error(f"init_db_schema: SQL file not found: {sql_path}")
            return False

        with open(sql_path, "r", encoding="utf-8") as f:
            sql = f.read()

        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)

        logger.info(f"✅ Database schema initialized from {sql_path}")
        _apply_migrations(conn, _EXERCISE_MIGRATIONS)
        return True

    except Exception as e:
        logger.error(f"init_db_schema failed: {e}")
        return False
    finally:
        if conn is not None:
            conn.close()

def _align_df_to_schema(df: DataFrame, schema_cols: list[str]) -> DataFrame:
    aligned_df = df
    for col_name in schema_cols:
        if col_name not in aligned_df.columns:
            aligned_df = aligned_df.withColumn(col_name, lit(None).cast("string"))
    return aligned_df.select(schema_cols)


def save_table_csv(df: DataFrame, table_name: str, output_dir) -> Path | None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    schema_cols = DB_TABLE_SCHEMAS.get(table_name)
    if not schema_cols:
        logger.warning(f"No DB schema defined for table '{table_name}', skipping")
        return None

    result_df = _align_df_to_schema(df, schema_cols)

    tmp_dir = output_dir / f"_{table_name}_csv_tmp_{uuid4().hex}"
    final_csv = output_dir / f"{table_name}.csv"

    try:
        result_df.coalesce(1).write.mode("overwrite") \
            .option("header", "true") \
            .option("nullValue", "") \
            .option("quote", '"') \
            .option("escape", '"') \
            .csv(str(tmp_dir))

        part_files = sorted(tmp_dir.glob("part-*.csv"))
        if not part_files:
            logger.error(f"Spark produced no CSV for table '{table_name}'")
            return None

        if final_csv.exists():
            final_csv.unlink()
        shutil.move(str(part_files[0]), str(final_csv))
        return final_csv
    finally:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)


def load_table_from_processed(table_name: str, output_dir) -> bool:
    output_dir = Path(output_dir)
    csv_path = output_dir / f"{table_name}.csv"
    return load_csv_to_postgres(csv_path, table_name)


def load_csv_to_postgres(csv_path: Path, table_name: str) -> bool:

    config = get_db_config()
    csv_path = Path(csv_path)

    if not csv_path.exists():
        logger.error(f"CSV path not found: {csv_path}")
        return False

    if not csv_path.is_file():
        logger.error(f"CSV file expected, got: {csv_path}")
        return False

    conn = None
    try:
        conn = _connect_db(config)

        with conn:
            with conn.cursor() as cur:
                cur.execute(f'TRUNCATE "{table_name}" CASCADE')

                quoted_table = f'"{table_name}"'
                with open(csv_path, "r", encoding="utf-8", newline="") as f:
                    headers = next(csv.reader(f))
                    quoted_cols = ", ".join(f'"{c}"' for c in headers)
                    copy_sql = (
                        f"COPY {quoted_table} ({quoted_cols}) "
                        f"FROM STDIN WITH (FORMAT CSV, NULL '', HEADER FALSE)"
                    )
                    f.seek(0)
                    next(f)
                    cur.copy_expert(copy_sql, f)

        logger.info(f"✅ Loaded table '{table_name}' from {csv_path.name}")
        return True

    except Exception as e:
        logger.error(f"load_csv_to_postgres failed for table '{table_name}': {e}")
        return False
    finally:
        if conn is not None:
            conn.close()
