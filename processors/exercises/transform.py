"""
Transform exercises data with PySpark to match MCD schema.
"""
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import (
    coalesce, col, concat_ws, element_at, lit, lower, substring, trim, when,
)
from utils.uuid_utils import exercise_uuid_udf


def _body_part_expr():
    raw = (
        when(col("primaryMuscles").isNotNull(),
             lower(trim(element_at(col("primaryMuscles"), 1))))
        .otherwise(lit("other"))
    )
    return (
        when(raw == lit("chest"), lit("CHEST"))
        .when(raw.isin("shoulders", "middle shoulders", "traps"), lit("SHOULDERS"))
        .when(raw.isin("middle back", "lower back", "lats", "back"), lit("BACK"))
        .when(raw.isin("biceps", "triceps", "forearms"), lit("ARMS"))
        .when(raw.isin("quadriceps", "hamstrings", "calves", "glutes",
                       "adductors", "abductors"), lit("LEGS"))
        .when(raw.isin("abdominals", "abs"), lit("CORE"))
        .otherwise(lit("FULL_BODY"))
    )


def _difficulty_expr():
    raw = lower(trim(col("level")))
    return (
        when(raw == lit("beginner"), lit("BEGINNER"))
        .when(raw == lit("intermediate"), lit("INTERMEDIATE"))
        .when(raw.isin("advanced", "expert"), lit("ADVANCED"))
        .otherwise(lit("BEGINNER"))
    )


def _category_expr():
    raw = lower(trim(col("category")))
    return (
        when(raw.isin("strength", "powerlifting", "strongman",
                      "olympic weightlifting"), lit("STRENGTH"))
        .when(raw.isin("cardio", "crossfit", "plyometrics"), lit("CARDIO"))
        .when(raw.isin("stretching", "flexibility"), lit("FLEXIBILITY"))
        .when(raw == lit("balance"), lit("BALANCE"))
        .otherwise(lit("OTHER"))
    )

# Use of Spark to transform exercises data from JSON to match the MCD `exercise` table schema.
def transform_exercises(spark: SparkSession, json_path: str) -> DataFrame:
    """Load, map and clean exercise JSON → MCD `exercise` table."""
    if not Path(json_path).exists():
        raise FileNotFoundError(f"Raw data file not found: {json_path}")

    df = spark.read.option("multiLine", "true").json(json_path)

    if "_corrupt_record" in df.columns:
        raise ValueError("Corrupt JSON data detected")

    _name = trim(col("name"))

    return (
        df.select(
            exercise_uuid_udf(_name).alias("exercise_id"),
            substring(_name, 1, 200).alias("name"),
            _body_part_expr().alias("body_part_target"),
            substring(element_at(col("images"), 1), 1, 200).alias("video_url"),
            substring(concat_ws(" ", col("instructions")), 1, 500).alias("description"),
            _difficulty_expr().alias("difficulty_level"),
            substring(coalesce(trim(col("equipment")), lit("body only")), 1, 100).alias("equipment_required"),
            _category_expr().alias("category"),
        )
        .dropDuplicates(["name"])
        .filter(col("name").isNotNull() & (_name != ""))
    )
