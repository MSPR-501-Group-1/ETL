"""Data quality monitoring for ETL pipelines.
Tracks executions, quality checks and anomalies in PostgreSQL.
"""
import csv
import json
import math
import uuid
from datetime import datetime
from pathlib import Path

import psycopg2
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from sqlalchemy import text

from utils.db_utils import get_db_config
from utils.logger import get_logger

logger = get_logger(__name__)

DLQ_BASE_DIR = Path(__file__).resolve().parent.parent / "data" / "processed" / "dlq"
DLQ_HEADERS = [
    "anomaly_id",
    "execution_id",
    "check_id",
    "source_table",
    "field_name",
    "record_identifier",
    "rule_type",
    "severity",
    "detected_at",
    "original_value",
    "corrected_value",
    "row_payload_json",
    "is_corrected",
    "corrected_by",
    "corrected_at",
    "replay_status",
    "replayed_at",
    "last_error",
]


def _to_serializable(value):
    if value is None:
        return None

    if hasattr(value, "item"):
        try:
            value = value.item()
        except Exception:
            pass

    if isinstance(value, float) and math.isnan(value):
        return None

    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass

    return value


def _to_string_or_empty(value):
    normalized = _to_serializable(value)
    if normalized is None:
        return ""
    return str(normalized)


def mark_loaded_execution(execution_id: str) -> None:
    """Update etl_execution status to LOADED after a successful load."""
    config = get_db_config()
    try:
        conn = psycopg2.connect(
            host=config["host"], port=int(config["port"]),
            dbname=config["database"], user=config["user"], password=config["password"],
        )
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE etl_execution SET status = 'LOADED' WHERE execution_id = %s",
                    (execution_id,),
                )
        conn.close()
        logger.info(f"ETL execution marked as LOADED: {execution_id}")
    except Exception as e:
        logger.error(f"mark_loaded_execution failed: {e}")


class DataQualityMonitor:

    def __init__(self, engine):
        self.engine = engine

    def start_execution(self, name: str) -> str:
        execution_id = str(uuid.uuid4())
        now = datetime.now()
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO etl_execution "
                    "(execution_id, name, started_at, status, records_extracted, records_loaded, records_rejected) "
                    "VALUES (:execution_id, :name, :started_at, 'PENDING', 0, 0, 0)"
                ),
                {"execution_id": execution_id, "name": name, "started_at": now},
            )
        logger.info(f"ETL execution started: {execution_id} pipeline={name}")
        return execution_id

    def end_execution(
        self,
        execution_id: str,
        status: str,
        records_extracted: int,
        records_loaded: int,
        records_rejected: int,
        error_msg: str = None,
    ):
        now = datetime.now()
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "UPDATE etl_execution SET "
                    "ended_at = :ended_at, status = :status, "
                    "records_extracted = :records_extracted, records_loaded = :records_loaded, "
                    "records_rejected = :records_rejected, error_message = :error_message "
                    "WHERE execution_id = :execution_id"
                ),
                {
                    "ended_at": now,
                    "status": status,
                    "records_extracted": records_extracted,
                    "records_loaded": records_loaded,
                    "records_rejected": records_rejected,
                    "error_message": error_msg,
                    "execution_id": execution_id,
                },
            )
        logger.info(
            f"ETL execution ended: {execution_id} | status={status} "
            f"extracted={records_extracted} loaded={records_loaded} rejected={records_rejected}"
        )

    def check_dataframe(
        self,
        spark_df: DataFrame,
        target_table_name: str,
        execution_id: str,
        rules: dict,
    ) -> tuple:
        total_rows = spark_df.count()
        error_condition = None

        # Build a combined error filter from the rules
        for rule_type, columns in rules.items():
            for col_name in columns:
                if rule_type == "not_null":
                    cond = F.col(col_name).isNull()
                elif rule_type == "positive":
                    cond = (F.col(col_name).isNull()) | (F.col(col_name) <= 0)
                elif rule_type == "not_negative":
                    cond = (F.col(col_name).isNull()) | (F.col(col_name) < 0)
                else:
                    logger.warning(f"Unknown rule type: {rule_type}, skipping")
                    continue

                error_condition = cond if error_condition is None else (error_condition | cond)

        if error_condition is None:
            logger.info(f"No rules to apply on {target_table_name}, returning full DataFrame")
            return spark_df, 0, None

        error_df = spark_df.filter(error_condition)
        clean_df = spark_df.filter(~error_condition)

        failed_count = error_df.count()
        passed = failed_count == 0

        # Log quality check
        check_id = str(uuid.uuid4())
        check_rule_summary = "; ".join(
            f"{rtype}: {', '.join(cols)}" for rtype, cols in rules.items()
        )
        now = datetime.now()

        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO data_quality_check_ "
                    "(check_id, target_table, check_type, check_rule, "
                    "records_checked, records_failed, checked_at, status, execution_id) "
                    "VALUES (:check_id, :target_table, :check_type, :check_rule, "
                    ":records_checked, :records_failed, :checked_at, :status, :execution_id)"
                ),
                {
                    "check_id": check_id,
                    "target_table": target_table_name,
                    "check_type": "COMPOSITE_CHECK",
                    "check_rule": check_rule_summary[:50],
                    "records_checked": total_rows,
                    "records_failed": failed_count,
                    "checked_at": now,
                    "status": passed,
                    "execution_id": execution_id,
                },
            )

        logger.info(
            f"Quality check on {target_table_name}: "
            f"{total_rows} checked, {failed_count} failed"
        )

        quality_summary = {
            "check_id": check_id,
            "target_table": target_table_name,
            "check_type": "COMPOSITE_CHECK",
            "check_rule": check_rule_summary,
            "records_checked": total_rows,
            "records_failed": failed_count,
            "status": passed,
            "checked_at": now.isoformat(),
        }

        # Log individual anomalies
        if failed_count > 0:
            self._log_anomalies(
                error_df, target_table_name, check_id, execution_id, rules
            )

        return clean_df, failed_count, quality_summary

    def _log_anomalies(
        self,
        error_df: DataFrame,
        target_table_name: str,
        check_id: str,
        execution_id: str,
        rules: dict,
    ):
        now = datetime.now()
        rows = error_df.limit(1000).toPandas()

        anomalies = []
        dlq_rows = []
        for _, row in rows.iterrows():
            row_payload = {
                column_name: _to_serializable(row.get(column_name))
                for column_name in rows.columns
            }
            record_identifier = _to_string_or_empty(row.get(rows.columns[0], "unknown")) or "unknown"

            for rule_type, columns in rules.items():
                for col_name in columns:
                    value = row.get(col_name)
                    is_violation = False

                    if rule_type == "not_null" and value is None:
                        is_violation = True
                    elif rule_type == "positive" and (value is None or value <= 0):
                        is_violation = True
                    elif rule_type == "not_negative" and (value is None or value < 0):
                        is_violation = True

                    if is_violation:
                        anomaly_id = str(uuid.uuid4())
                        severity = "HIGH" if rule_type == "not_null" else "MEDIUM"

                        anomalies.append(
                            {
                                "anomaly_id": anomaly_id,
                                "source_table": target_table_name,
                                "anomaly_table": target_table_name,
                                "field_name": col_name,
                                "record_identifier": record_identifier,
                                "original_value": _to_string_or_empty(value),
                                "detected_at": now,
                                "severity": severity,
                                "is_resolved": False,
                                "resolution_action": None,
                                "check_id": check_id,
                                "execution_id": execution_id,
                            }
                        )

                        dlq_rows.append(
                            {
                                "anomaly_id": anomaly_id,
                                "execution_id": execution_id,
                                "check_id": check_id,
                                "source_table": target_table_name,
                                "field_name": col_name,
                                "record_identifier": record_identifier,
                                "rule_type": rule_type,
                                "severity": severity,
                                "detected_at": now.isoformat(),
                                "original_value": _to_string_or_empty(value),
                                "corrected_value": "",
                                "row_payload_json": json.dumps(row_payload, ensure_ascii=True),
                                "is_corrected": "false",
                                "corrected_by": "",
                                "corrected_at": "",
                                "replay_status": "pending",
                                "replayed_at": "",
                                "last_error": "",
                            }
                        )

        if not anomalies:
            return

        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO data_anomaly "
                    "(anomaly_id, source_table, anomaly_table, field_name, "
                    "record_identifier, original_value, detected_at, severity, "
                    "is_resolved, resolution_action, check_id, execution_id) "
                    "VALUES (:anomaly_id, :source_table, :anomaly_table, :field_name, "
                    ":record_identifier, :original_value, :detected_at, :severity, "
                    ":is_resolved, :resolution_action, :check_id, :execution_id)"
                ),
                anomalies,
            )

        self._write_dlq_csv(target_table_name, execution_id, dlq_rows)

        logger.info(f"Logged {len(anomalies)} anomalies for {target_table_name}")

    def _write_dlq_csv(self, target_table_name: str, execution_id: str, rows: list[dict]):
        if not rows:
            return

        DLQ_BASE_DIR.mkdir(parents=True, exist_ok=True)
        dlq_path = DLQ_BASE_DIR / f"{target_table_name}_{execution_id}_dlq.csv"

        with dlq_path.open("w", encoding="utf-8", newline="") as dlq_file:
            writer = csv.DictWriter(dlq_file, fieldnames=DLQ_HEADERS)
            writer.writeheader()
            writer.writerows(rows)

        logger.info(
            "DLQ CSV written: %s (%s rows)",
            dlq_path,
            len(rows),
        )
