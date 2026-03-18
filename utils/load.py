"""
Common load utilities for all ETL pipelines.
"""
import csv
import shutil
from pathlib import Path
from uuid import uuid4

import psycopg2
from pyspark.sql import DataFrame
from pyspark.sql.functions import lit


from utils.logger import get_logger
from utils.db_utils import DB_TABLE_SCHEMAS, get_db_config

logger = get_logger(__name__)


def _connect_db(config: dict):
    return psycopg2.connect(
        host=config["host"],
        port=int(config["port"]),
        dbname=config["database"],
        user=config["user"],
        password=config["password"],
    )


def _default_schema_path() -> Path:
    return Path(__file__).resolve().parent.parent / "database" / "01_initdb.sql"


def init_db_schema(sql_path: str = None) -> bool:

    config = get_db_config()
    if sql_path is None:
        sql_path = _default_schema_path()
    sql_path = Path(sql_path)

    if not sql_path.exists():
        logger.error(f"init_db_schema: SQL file not found: {sql_path}")
        return False

    conn = None
    try:
        with open(sql_path, "r", encoding="utf-8") as f:
            sql = f.read()

        conn = _connect_db(config)
        schema_exists = False
        with conn:
            with conn.cursor() as cur:
                # Skip if schema already initialized (e.g. by docker-entrypoint)
                cur.execute("SELECT to_regclass('public.exercise')")
                schema_exists = cur.fetchone()[0] is not None
                if not schema_exists:
                    cur.execute(sql)

        if schema_exists:
            logger.info("✅ Database schema already exists, skipping init")
        else:
            logger.info(f"✅ Database schema initialized from {sql_path}")

        for ddl in [
            'ALTER TABLE exercise ALTER COLUMN name TYPE VARCHAR(200)',
            'ALTER TABLE exercise ALTER COLUMN description TYPE VARCHAR(500)',
            'ALTER TABLE exercise ALTER COLUMN video_url TYPE VARCHAR(200)',
            'ALTER TABLE exercise ALTER COLUMN equipment_required TYPE VARCHAR(100)',
        ]:
            try:
                with conn:
                    with conn.cursor() as cursor:
                        cursor.execute(ddl)
            except Exception as error:
                logger.debug(f"Migration skipped ({type(error).__name__}): {ddl[:60]}")

        return True
    except Exception as e:
        logger.error(f"init_db_schema failed: {e}")
        return False
    finally:
        if conn is not None:
            conn.close()

def save_and_load_table(df: DataFrame, table_name: str, output_dir) -> bool:

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    schema_cols = DB_TABLE_SCHEMAS.get(table_name)
    if not schema_cols:
        logger.warning(f"No DB schema defined for table '{table_name}', skipping")
        return False

    for col_name in schema_cols:
        if col_name not in df.columns:
            df = df.withColumn(col_name, lit(None).cast("string"))

    result_df = df.select(schema_cols)

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
            return False

        if final_csv.exists():
            final_csv.unlink()
        shutil.move(str(part_files[0]), str(final_csv))

        return load_csv_to_postgres(final_csv, table_name)
    finally:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)


def load_csv_to_postgres(csv_path: Path, table_name: str) -> bool:

    config = get_db_config()
    csv_path = Path(csv_path)

    if not csv_path.exists():
        logger.error(f"CSV path not found: {csv_path}")
        return False

    if csv_path.is_file():
        part_files = [csv_path]
    else:
        part_files = sorted(csv_path.glob("part-*.csv"))
        if not part_files:
            logger.error(f"No CSV part files found in: {csv_path}")
            return False

    conn = None
    try:
        conn = _connect_db(config)

        with conn:
            with conn.cursor() as cur:
                # Truncate first so re-runs never hit PK collisions; CASCADE
                # handles any FK-dependent child rows automatically.
                cur.execute(f'TRUNCATE "{table_name}" CASCADE')

                headers = None
                quoted_table = f'"{table_name}"'
                copy_sql = None

                for part_file in part_files:
                    with open(part_file, "r", encoding="utf-8", newline="") as f:
                        # Read header to build column list
                        reader = csv.reader(f)
                        current_headers = next(reader)

                        if headers is None:
                            headers = current_headers
                            quoted_cols = ", ".join(f'"{c}"' for c in headers)
                            copy_sql = (
                                f"COPY {quoted_table} ({quoted_cols}) "
                                f"FROM STDIN WITH (FORMAT CSV, NULL '', HEADER FALSE)"
                            )
                        elif current_headers != headers:
                            logger.error(
                                f"CSV header mismatch in '{part_file.name}' for table '{table_name}'"
                            )
                            return False

                        # Rewind past the header for COPY
                        f.seek(0)
                        next(f)

                        cur.copy_expert(copy_sql, f)

        logger.info(f"✅ Loaded table '{table_name}' from {len(part_files)} CSV part file(s)")
        return True

    except Exception as e:
        logger.error(f"load_csv_to_postgres failed for table '{table_name}': {e}")
        return False
    finally:
        if conn is not None:
            conn.close()
