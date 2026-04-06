"""
Data quality monitoring for ETL pipelines.
Tracks executions, quality checks and anomalies in PostgreSQL.
"""
import uuid
from datetime import datetime

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from sqlalchemy import text

from utils.logger import get_logger

logger = get_logger(__name__)


class DataQualityMonitor:

    def __init__(self, engine):
        self.engine = engine

    def start_execution(self) -> str:
        execution_id = str(uuid.uuid4())
        now = datetime.now()
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO etl_execution "
                    "(execution_id, started_at, status, records_extracted, records_loaded, records_rejected) "
                    "VALUES (:execution_id, :started_at, FALSE, 0, 0, 0)"
                ),
                {"execution_id": execution_id, "started_at": now},
            )
        logger.info(f"ETL execution started: {execution_id}")
        return execution_id

    def end_execution(
        self,
        execution_id: str,
        status: bool,
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
        for _, row in rows.iterrows():
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
                        anomalies.append(
                            {
                                "anomaly_id": str(uuid.uuid4()),
                                "source_table": target_table_name,
                                "anomaly_table": target_table_name,
                                "field_name": col_name,
                                "record_identifier": str(row.get(rows.columns[0], "unknown")),
                                "original_value": str(value),
                                "detected_at": now,
                                "severity": "HIGH" if rule_type == "not_null" else "MEDIUM",
                                "is_resolved": False,
                                "resolution_action": None,
                                "check_id": check_id,
                                "execution_id": execution_id,
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

        logger.info(f"Logged {len(anomalies)} anomalies for {target_table_name}")
