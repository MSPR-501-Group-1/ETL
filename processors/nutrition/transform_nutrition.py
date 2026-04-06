"""Transform source 1 — Kaggle 'nutrition' dataset."""
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import (
    coalesce, col, least, lit, lower,
    round as spark_round, substring, trim, when,
)
from pyspark.sql.types import DoubleType, StringType

from utils.logger import get_logger
from utils.transform import ensure_columns, load_raw_data
from utils.uuid_utils import food_uuid_udf

logger = get_logger(__name__)

_NUM_RE = r'^-?\d+(\.\d+)?$'


def _normalize_columns(df: DataFrame) -> DataFrame:
    def _clean(name: str) -> str:
        return name.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
    return df.toDF(*[_clean(c) for c in df.columns])


def _tc(c_name: str):
    """Cast a plain numeric column to Double, null on non-numeric."""
    return spark_round(
        when(col(c_name).rlike(_NUM_RE), col(c_name).cast(DoubleType())).otherwise(lit(None)), 2
    )


def _num(*cols: str):
    """Coalesce plain-numeric columns, cap at 999.9, default 0."""
    return least(coalesce(*[_tc(c) for c in cols], lit(0.0)), lit(999.9))


def _category_expr():
    raw = lower(trim(coalesce(col("category"), col("food_category"), lit(""))))
    return (
        when(raw.rlike("vegetable|veggie|veg"), lit("VEGETABLE"))
        .when(raw.rlike("fruit"), lit("FRUIT"))
        .when(raw.rlike("meat|beef|pork|chicken|poultry|lamb|fish|seafood"), lit("MEAT"))
        .when(raw.rlike("dairy|milk|cheese|yogurt|cream"), lit("DAIRY"))
        .when(raw.rlike("grain|bread|pasta|rice|cereal|flour"), lit("GRAIN"))
        .when(raw.rlike("beverage|drink|juice|water|alcohol|soda"), lit("BEVERAGE"))
        .when(raw.rlike("snack|candy|chocolate|chip|dessert|sweet|biscuit"), lit("SNACK"))
        .otherwise(lit("OTHER"))
    )


def transform_nutrition(spark: SparkSession, csv_path: str) -> DataFrame:
    """Load, map, and clean source 1 → MCD `ingredients` schema."""
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"Raw data file not found: {csv_path}")

    logger.info("⏳ Transforming nutrition (source 1)...")

    df = _normalize_columns(load_raw_data(spark, csv_path))
    df = ensure_columns(df, [
        "food_item", "category", "food_category",
        "calories_kcal", "protein_g", "protein",
        "carbohydrates_g", "carbohydrate_g", "carbs_g", "carbohydrates",
        "fat_g", "total_fat", "fiber_g", "dietary_fiber",
        "sugars_g", "sugar_g", "sugars",
        "sodium_mg", "sodium", "cholesterol_mg", "cholesterol",
    ])
    _name = coalesce(trim(col("food_item")), lit("Unknown"))
    name_expr = substring(_name, 1, 50)

    return (
        df.select(
            food_uuid_udf(name_expr, lit(None)).alias("ingredients_id"),
            name_expr.alias("name"),
            _num("calories_kcal").alias("calories_g"),
            _num("protein_g", "protein").alias("protein_g"),
            _num("carbohydrates_g", "carbohydrate_g", "carbs_g", "carbohydrates").alias("carbs_g"),
            _num("fat_g", "total_fat").alias("fat_g"),
            lit(None).cast(StringType()).alias("nutriscore"),
            _category_expr().alias("category"),
            _num("fiber_g", "dietary_fiber").alias("fiber_g"),
            _num("sugars_g", "sugar_g", "sugars").alias("sugar_g"),
            _num("sodium_mg", "sodium").alias("sodium_mg"),
            _num("cholesterol_mg", "cholesterol").alias("cholesterol_mg"),
        )
        .dropDuplicates(["name"])
        .filter(
            col("name").isNotNull()
            & (col("name") != "")
            & (lower(col("name")) != "unknown")
            & (col("calories_g") >= 0)
            & (col("protein_g") >= 0)
            & (col("carbs_g") >= 0)
            & (col("fat_g") >= 0)
        )
    )
