"""DLQ helpers for replaying corrected anomalies stored as CSV files."""

import csv
import json
from datetime import datetime
from pathlib import Path

import psycopg2
from psycopg2 import sql

from utils.db_utils import DB_TABLE_SCHEMAS, get_db_config
from utils.logger import get_logger

logger = get_logger(__name__)

DLQ_BASE_DIR = Path(__file__).resolve().parent.parent / "data" / "processed" / "dlq"


def _normalize_value(value):
    if value is None:
        return None

    text_value = str(value).strip()
    if text_value == "" or text_value.lower() in {"null", "none", "nan"}:
        return None

    return value


def _connect_db(config: dict):
    return psycopg2.connect(
        host=config["host"],
        port=int(config["port"]),
        dbname=config["database"],
        user=config["user"],
        password=config["password"],
    )


def _read_dlq_rows(dlq_path: Path):
    with dlq_path.open("r", encoding="utf-8", newline="") as dlq_file:
        return list(csv.DictReader(dlq_file))


def _write_dlq_rows(dlq_path: Path, rows: list[dict]):
    if not rows:
        return

    fieldnames = list(rows[0].keys())
    with dlq_path.open("w", encoding="utf-8", newline="") as dlq_file:
        writer = csv.DictWriter(dlq_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def replay_corrected_rows(source_table: str, execution_id: str) -> dict:
    if source_table not in DB_TABLE_SCHEMAS:
        raise ValueError(f"Unsupported source_table: {source_table}")

    DLQ_BASE_DIR.mkdir(parents=True, exist_ok=True)
    dlq_path = DLQ_BASE_DIR / f"{source_table}_{execution_id}_dlq.csv"

    if not dlq_path.exists():
        raise FileNotFoundError(f"DLQ file not found: {dlq_path}")

    rows = _read_dlq_rows(dlq_path)
    if not rows:
        return {
            "source_table": source_table,
            "execution_id": execution_id,
            "dlq_file": str(dlq_path),
            "replayed": 0,
            "failed": 0,
            "message": "DLQ file is empty",
        }

    schema_columns = DB_TABLE_SCHEMAS[source_table]
    primary_key = schema_columns[0]

    insert_stmt = sql.SQL(
        "INSERT INTO {table} ({columns}) VALUES ({values}) "
        "ON CONFLICT ({primary_key}) DO UPDATE SET {updates}"
    ).format(
        table=sql.Identifier(source_table),
        columns=sql.SQL(", ").join(sql.Identifier(column) for column in schema_columns),
        values=sql.SQL(", ").join(sql.Placeholder() for _ in schema_columns),
        primary_key=sql.Identifier(primary_key),
        updates=sql.SQL(", ").join(
            sql.SQL("{column} = EXCLUDED.{column}").format(column=sql.Identifier(column))
            for column in schema_columns
            if column != primary_key
        ),
    )

    replayed = 0
    failed = 0
    errors = []
    now_iso = datetime.utcnow().isoformat()

    config = get_db_config()
    conn = None

    try:
        conn = _connect_db(config)

        with conn:
            with conn.cursor() as cursor:
                for row in rows:
                    is_corrected = str(row.get("is_corrected", "")).strip().lower() == "true"
                    already_replayed = bool(str(row.get("replayed_at", "")).strip())

                    if not is_corrected or already_replayed:
                        continue

                    anomaly_id = str(row.get("anomaly_id", "")).strip() or "unknown"

                    try:
                        payload = json.loads(row.get("row_payload_json") or "{}")
                        if not isinstance(payload, dict):
                            raise ValueError("row_payload_json must be an object")

                        target_field = str(row.get("field_name", "")).strip()
                        corrected_value = row.get("corrected_value")
                        if target_field and corrected_value is not None and str(corrected_value) != "":
                            payload[target_field] = corrected_value

                        record = {
                            column: _normalize_value(payload.get(column))
                            for column in schema_columns
                        }

                        if not record.get(primary_key):
                            raise ValueError(f"Missing primary key '{primary_key}' in row payload")

                        cursor.execute(insert_stmt, [record[column] for column in schema_columns])

                        row["replay_status"] = "replayed"
                        row["replayed_at"] = now_iso
                        row["last_error"] = ""
                        replayed += 1
                    except Exception as replay_error:  # pragma: no cover - defensive path
                        row["replay_status"] = "failed"
                        row["last_error"] = str(replay_error)[:300]
                        failed += 1
                        errors.append(
                            {
                                "anomaly_id": anomaly_id,
                                "error": str(replay_error),
                            }
                        )

        _write_dlq_rows(dlq_path, rows)

        logger.info(
            "DLQ replay completed | table=%s execution_id=%s replayed=%s failed=%s",
            source_table,
            execution_id,
            replayed,
            failed,
        )

        result = {
            "source_table": source_table,
            "execution_id": execution_id,
            "dlq_file": str(dlq_path),
            "replayed": replayed,
            "failed": failed,
        }
        if errors:
            result["errors"] = errors

        return result
    finally:
        if conn is not None:
            conn.close()
