"""
Generic Data Quality engine.

Usage in any pipeline.py:
    from utils.quality import QualityRule, run_quality_checks

    rules = [
        QualityRule("NULL_CHECK",  "food_item IS NOT NULL", "ingredients",
                    col("food_item").isNull(), "food_item", "food_item"),
        QualityRule("RANGE_CHECK", "calories_kcal >= 0",   "ingredients",
                    col("calories_kcal") < 0,  "calories_kcal", "food_item"),
    ]
    df_valid, rejected = run_quality_checks(df_raw, rules, execution_id,
                                             source_table="nutrition_raw")
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import StringType

from utils.db_utils import get_db_config
from utils.etl_tracking import record_quality_check


def _get_jdbc_url() -> str:
    cfg = get_db_config()
    return f"jdbc:postgresql://{cfg['host']}:{cfg['port']}/{cfg['database']}"
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class QualityRule:
    check_type: str          # "NULL_CHECK" | "RANGE_CHECK" | "FORMAT_CHECK" ...
    check_rule: str          # texte lisible, ex: "food_item IS NOT NULL"
    target_table: str        # table destination PostgreSQL
    fail_condition: object   # colonne Spark qui vaut True sur les lignes INVALIDES
    source_col: str          # colonne inspectée (valeur à stocker dans original_value)
    identifier_col: str      # colonne qui identifie la ligne (ex: nom, id)
    severity: str = "WARNING"
    anomaly_table: str = ""  # si vide, prend target_table


def run_quality_checks(
    df: DataFrame,
    rules: list,
    execution_id: Optional[str],
    source_table: str,
) -> tuple:
    """
    Applique toutes les règles sur df.
    Insère les anomalies en bulk via JDBC.
    Retourne (df_valid_toutes_regles, total_rejected).
    """
    total = df.count()
    df_valid = df
    total_rejected = 0

    for rule in rules:
        fail_count = df.filter(rule.fail_condition).count()

        check_id = record_quality_check(
            execution_id, rule.target_table, rule.check_type,
            rule.check_rule, total, fail_count,
        )

        if fail_count > 0:
            df_invalid = df.filter(rule.fail_condition)
            _write_anomalies_bulk(
                df_invalid, execution_id, check_id,
                source_col=rule.source_col,
                identifier_col=rule.identifier_col,
                source_table=source_table,
                anomaly_table=rule.anomaly_table or rule.target_table,
                severity=rule.severity,
            )
            # On retire ces lignes du DataFrame propre
            df_valid = df_valid.filter(~rule.fail_condition)
            total_rejected += fail_count
            logger.info(f"[DQ] {rule.check_rule} — {fail_count} anomalie(s) détectée(s)")

    return df_valid, total_rejected


def _write_anomalies_bulk(
    df_anomalies: DataFrame,
    execution_id: Optional[str],
    check_id: Optional[str],
    source_col: str,
    identifier_col: str,
    source_table: str,
    anomaly_table: str,
    severity: str,
) -> None:
    """Insère df_anomalies dans data_anomaly via un seul appel JDBC. Zéro boucle Python."""
    uuid_udf = F.udf(lambda: str(uuid.uuid4()), StringType())

    df_to_insert = df_anomalies.select(
        uuid_udf().alias("anomaly_id"),
        F.lit(source_table[:50]).alias("source_table"),
        F.lit(anomaly_table[:50]).alias("anomaly_table"),
        F.lit(source_col[:50]).alias("field_name"),
        F.col(identifier_col).cast(StringType()).alias("record_identifier"),
        F.col(source_col).cast(StringType()).alias("original_value"),
        F.current_timestamp().alias("detected_at"),
        F.lit(severity).alias("severity"),
        F.lit(False).alias("is_resolved"),
        F.lit(check_id).alias("check_id"),
        F.lit(execution_id).alias("execution_id"),
    )

    try:
        props = {**get_db_config(), "driver": "org.postgresql.Driver"}
        df_to_insert.write.jdbc(
            url=_get_jdbc_url(),
            table="data_anomaly",
            mode="append",
            properties=props,
        )
    except Exception as e:
        import traceback
        logger.error(f"_write_anomalies_bulk FAILED: {e}\n{traceback.format_exc()}")