"""
ETL tracking — records pipeline execution metadata directly in PostgreSQL.

Three tables are written to:
  - etl_execution       one row per pipeline run
  - data_quality_check_ one row per validation rule applied
  - data_anomaly        one row per rejected / flagged record

All functions use psycopg2 (no Spark).
They are designed to never raise: any DB failure is logged and swallowed
so tracking issues can never break a pipeline.
"""
import uuid
from datetime import datetime
from typing import Optional

import psycopg2

from utils.db_utils import get_db_config
from utils.logger import get_logger

logger = get_logger(__name__)


def _connect():
    cfg = get_db_config()
    return psycopg2.connect(
        host=cfg["host"], port=int(cfg["port"]),
        dbname=cfg["database"], user=cfg["user"], password=cfg["password"],
    )


# ── etl_execution ─────────────────────────────────────────────────────────────

def start_execution(source_id: str) -> Optional[str]:
    """
    Record the start of a pipeline run in etl_execution.
    Returns the new execution_id, or None if the INSERT failed.
    """
    execution_id = str(uuid.uuid4())
    try:
        conn = _connect()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    'INSERT INTO etl_execution '
                    '(execution_id, started_at, status, triggered_by, source_id) '
                    'VALUES (%s, %s, %s, %s, %s)',
                    (execution_id, datetime.utcnow(), None, "etl_pipeline", source_id),
                )
        conn.close()
        logger.debug(f"etl_execution started: {execution_id}")
        return execution_id
    except Exception as e:
        logger.warning(f"start_execution failed (non-blocking): {e}")
        return None


def end_execution(
    execution_id: Optional[str],
    status: bool,
    records_extracted: int = 0,
    records_loaded: int = 0,
    records_rejected: int = 0,
    error_message: Optional[str] = None,
) -> None:
    """
    Update the etl_execution row with the final status and metrics.

    Note: the DB columns records_* are BOOLEAN (schema constraint),
    so we store True if the count is > 0.
    """
    if not execution_id:
        return
    try:
        conn = _connect()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    'UPDATE etl_execution SET '
                    'ended_at=%s, status=%s, '
                    'records_extracted=%s, records_loaded=%s, records_rejected=%s, '
                    'error_message=%s '
                    'WHERE execution_id=%s',
                    (
                        datetime.utcnow(),
                        status,
                        bool(records_extracted),
                        bool(records_loaded),
                        bool(records_rejected),
                        (error_message or "")[:50],
                        execution_id,
                    ),
                )
        conn.close()
        logger.debug(f"etl_execution ended: {execution_id} — status={status}")
    except Exception as e:
        logger.warning(f"end_execution failed (non-blocking): {e}")


# ── data_quality_check_ ───────────────────────────────────────────────────────

def record_quality_check(
    execution_id: Optional[str],
    target_table: str,
    check_type: str,
    check_rule: str,
    records_checked: int,
    records_failed: int,
) -> Optional[str]:
    """
    Insert a data_quality_check_ row for a validation rule that was applied.
    Returns the new check_id, or None on failure.

    Example:
        check_id = record_quality_check(
            execution_id, "ingredients", "NULL_CHECK", "name IS NOT NULL",
            total_count, null_count,
        )
    """
    if not execution_id:
        return None
    check_id = str(uuid.uuid4())
    status = records_failed == 0
    try:
        conn = _connect()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    'INSERT INTO data_quality_check_ '
                    '(check_id, target_table, check_type, check_rule, '
                    'records_checked, records_failed, checked_at, status, execution_id) '
                    'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                    (
                        check_id,
                        target_table[:50], check_type[:50], check_rule[:50],
                        str(records_checked), str(records_failed),
                        datetime.utcnow(), status,
                        execution_id,
                    ),
                )
        conn.close()
        logger.debug(f"quality check recorded: {check_type} on {target_table} — {records_failed} failed")
        return check_id
    except Exception as e:
        logger.warning(f"record_quality_check failed (non-blocking): {e}")
        return None


# ── data_anomaly ──────────────────────────────────────────────────────────────

def record_anomaly(
    execution_id: Optional[str],
    check_id: Optional[str],
    source_table: str,
    field_name: str,
    record_identifier: str,
    original_value: str,
    severity: str = "WARNING",
) -> None:
    """
    Insert a data_anomaly row for a rejected or flagged record.

    severity: "INFO" | "WARNING" | "ERROR"
    """
    if not execution_id:
        return
    anomaly_id = str(uuid.uuid4())
    try:
        conn = _connect()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    'INSERT INTO data_anomaly '
                    '(anomaly_id, source_table, field_name, record_identifier, '
                    'original_value, detected_at, severity, is_resolved, '
                    'check_id, execution_id) '
                    'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                    (
                        anomaly_id,
                        source_table[:50], field_name[:50],
                        str(record_identifier)[:50], str(original_value)[:50],
                        datetime.utcnow(), severity[:50], False,
                        check_id, execution_id,
                    ),
                )
        conn.close()
    except Exception as e:
        logger.warning(f"record_anomaly failed (non-blocking): {e}")
