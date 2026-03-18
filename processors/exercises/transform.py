"""
Transform exercises data with PySpark to match MCD schema.
"""
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, trim, lower, when, lit, concat_ws, element_at, substring
from utils.uuid_utils import exercise_uuid_udf


def transform_exercises(spark: SparkSession, json_path: str) -> DataFrame:
    """Load, map and clean exercise JSON → MCD `exercise` table."""
    if not Path(json_path).exists():
        raise FileNotFoundError(f"Raw data file not found: {json_path}")

    df = spark.read.option("multiLine", "true").json(json_path)

    if "_corrupt_record" in df.columns:
        raise ValueError("Corrupt JSON data detected")

    # ── body_part_enum ────────────────────────────────────────────────────────
    raw_bp = (
        when(col("primaryMuscles").isNotNull(),
             lower(trim(element_at(col("primaryMuscles"), 1))))
        .otherwise(lit("other"))
    )
    body_part = (
        when(raw_bp == lit("chest"), lit("CHEST"))
        .when(raw_bp.isin("shoulders", "middle shoulders", "traps"), lit("SHOULDERS"))
        .when(raw_bp.isin("middle back", "lower back", "lats", "back"), lit("BACK"))
        .when(raw_bp.isin("biceps", "triceps", "forearms"), lit("ARMS"))
        .when(raw_bp.isin("quadriceps", "hamstrings", "calves", "glutes",
                          "adductors", "abductors"), lit("LEGS"))
        .when(raw_bp.isin("abdominals", "abs"), lit("CORE"))
        .otherwise(lit("FULL_BODY"))
    )

    # ── exercise_difficulty_enum ──────────────────────────────────────────────
    raw_lvl = lower(trim(col("level")))
    difficulty = (
        when(raw_lvl == lit("beginner"), lit("BEGINNER"))
        .when(raw_lvl == lit("intermediate"), lit("INTERMEDIATE"))
        .when(raw_lvl.isin("advanced", "expert"), lit("ADVANCED"))
        .otherwise(lit("BEGINNER"))
    )

    # ── exercise_category_enum ────────────────────────────────────────────────
    raw_cat = lower(trim(col("category")))
    category = (
        when(raw_cat.isin("strength", "powerlifting", "strongman",
                          "olympic weightlifting"), lit("STRENGTH"))
        .when(raw_cat.isin("cardio", "crossfit", "plyometrics"), lit("CARDIO"))
        .when(raw_cat.isin("stretching", "flexibility"), lit("FLEXIBILITY"))
        .when(raw_cat == lit("balance"), lit("BALANCE"))
        .otherwise(lit("OTHER"))
    )

    return (
        df.select(
            exercise_uuid_udf(trim(col("name"))).alias("exercise_id"),
            substring(trim(col("name")), 1, 200).alias("name"),
            body_part.alias("body_part_target"),
            substring(
                when(col("images").isNotNull(), element_at(col("images"), 1))
                .otherwise(lit(None)),
                1,
                200,
            ).alias("video_url"),
            substring(
                when(col("instructions").isNotNull(), concat_ws(" ", col("instructions")))
                .otherwise(lit(None)), 1, 500
            ).alias("description"),
            difficulty.alias("difficulty_level"),
            substring(
                when(col("equipment").isNotNull(), trim(col("equipment")))
                .otherwise(lit("body only")),
                1,
                100,
            ).alias("equipment_required"),
            category.alias("category"),
        )
        .dropDuplicates(["name"])
        .filter(col("name").isNotNull() & (trim(col("name")) != ""))
    )
