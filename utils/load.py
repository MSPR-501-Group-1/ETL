"""
Common load utilities for all ETL pipelines.
"""
import csv
import glob
import shutil
from pathlib import Path

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
    import uuid

    config = get_db_config()
    roles = [
        (generate_role_uuid("FREEMIUM"),     "FREEMIUM",     True),
        (generate_role_uuid("PREMIUM"),      "PREMIUM",      True),
        (generate_role_uuid("PREMIUM_PLUS"), "PREMIUM_PLUS", True),
        (generate_role_uuid("B2B"),          "B2B",          True),
        (generate_role_uuid("ADMIN"),        "ADMIN",        True),
    ]
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
        schema_exists = False
        with conn:
            with conn.cursor() as cur:
                # Skip if schema already initialized (e.g. by docker-entrypoint)
                cur.execute("SELECT to_regclass('public.role')")
                schema_exists = cur.fetchone()[0] is not None
                if not schema_exists:
                    cur.execute(sql)
        conn.close()
        if schema_exists:
            logger.info("✅ Database schema already exists, skipping init")
        else:
            logger.info(f"✅ Database schema initialized from {sql_path}")

        # Apply schema migrations idempotently — each in its own transaction so
        # one failure does not roll back the others.
        _migrations = [
            'ALTER TABLE exercise ALTER COLUMN name TYPE VARCHAR(200)',
            'ALTER TABLE exercise ALTER COLUMN description TYPE VARCHAR(500)',
            'ALTER TABLE exercise ALTER COLUMN video_url TYPE VARCHAR(200)',
            'ALTER TABLE exercise ALTER COLUMN equipment_required TYPE VARCHAR(100)',
            (
                'ALTER TABLE user_profile ALTER COLUMN height_cm '
                'TYPE SMALLINT USING ROUND(COALESCE(height_cm, 0))::SMALLINT'
            ),
        ]
        _db = dict(
            host=config["host"], port=int(config["port"]),
            dbname=config["database"], user=config["user"],
            password=config["password"],
        )
        for ddl in _migrations:
            _m = psycopg2.connect(**_db)
            try:
                with _m:
                    with _m.cursor() as _c:
                        _c.execute(ddl)
            except Exception as _e:
                logger.debug(f"Migration skipped ({type(_e).__name__}): {ddl[:60]}")
            finally:
                _m.close()

        return True
    except Exception as e:
        logger.error(f"init_db_schema failed: {e}")
        return False

logger = get_logger(__name__)

def save_and_load_table(df: DataFrame, table_name: str, output_dir) -> bool:
    """
    Align *df* to DB_TABLE_SCHEMAS[table_name], write a single CSV, then
    COPY it into PostgreSQL.  DataFrame columns must already carry schema
    names; any schema column absent from the DataFrame is added as NULL.
    Returns True on success.
    """
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

    tmp_dir = output_dir / f"_{table_name}_tmp"
    result_df.coalesce(1).write.mode("overwrite") \
        .option("header", "true") \
        .option("nullValue", "") \
        .option("quote", '"') \
        .option("escape", '"') \
        .csv(str(tmp_dir))

    part_files = glob.glob(str(tmp_dir / "part-*.csv"))
    if not part_files:
        logger.error(f"Spark produced no CSV for table '{table_name}'")
        shutil.rmtree(str(tmp_dir), ignore_errors=True)
        return False

    csv_path = output_dir / f"{table_name}.csv"
    shutil.move(part_files[0], str(csv_path))
    shutil.rmtree(str(tmp_dir), ignore_errors=True)

    return load_csv_to_postgres(csv_path, table_name)


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
                # Truncate first so re-runs never hit PK collisions; CASCADE
                # handles any FK-dependent child rows automatically.
                cur.execute(f'TRUNCATE "{table_name}" CASCADE')

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
