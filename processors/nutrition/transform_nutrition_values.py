"""Transform source 2 — Kaggle 'nutrition_values' dataset."""
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import (
    coalesce, col, least, lit, lower, regexp_extract, regexp_replace,
    round as spark_round, split, substring, trim, when,
)
from pyspark.sql.types import DoubleType, StringType

from utils.logger import get_logger
from utils.transform import ensure_columns, load_raw_data
from utils.uuid_utils import food_uuid_udf

logger = get_logger(__name__)


def _normalize_columns(df: DataFrame) -> DataFrame:
    def _clean(name: str) -> str:
        return name.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
    return df.toDF(*[_clean(c) for c in df.columns])


def _tc(c_name: str):
    """Extract the first number from an embedded-text column and cast to Double."""
    extracted = regexp_extract(col(c_name), r'(-?\d+\.?\d*)', 1)
    return spark_round(
        when(extracted != lit(""), extracted.cast(DoubleType())).otherwise(lit(None)), 2
    )


def _num(*cols: str):
    """Coalesce embedded-text columns, cap at 999.9, default 0."""
    return least(coalesce(*[_tc(c) for c in cols], lit(0.0)), lit(999.9))


def _category_expr():
    raw = lower(trim(coalesce(col("category"), col("food_category"), col("food_group"), col("group"), lit(""))))
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


def transform_nutrition_values(spark: SparkSession, csv_path: str) -> DataFrame:
    """Load, map, and clean source 2 → MCD `ingredients` schema."""
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"Raw data file not found: {csv_path}")

    logger.info("⏳ Transforming nutrition values (source 2)...")

    df = _normalize_columns(load_raw_data(spark, csv_path))
    df = ensure_columns(df, [
        "name", "salt", "category", "food_category", "food_group", "group",
        "calories", "energy_kcal", "energy", "calorie",
        "protein_g", "protein", "proteins",
        "carbohydrate_g", "carbs_g", "carbohydrates", "carbs", "total_carbohydrate",
        "fat_g", "total_fat", "fat", "lipid",
        "fiber_g", "dietary_fiber", "fiber", "fibre",
        "sugar_g", "sugars", "sugar", "total_sugars",
        "sodium_mg", "sodium", "cholesterol_mg", "cholesterol",
    ])
    _raw = coalesce(trim(col("name")), lit("Unknown"))
    _strip_quotes = lambda c: regexp_replace(c, r'^"+', '')
    usda_name_expr = _strip_quotes(substring(_raw, 1, 255))
    name_expr = _strip_quotes(substring(trim(split(_raw, ",")[0]), 1, 100))
    _salt = _tc("salt")
    _sodium_from_salt = when(_salt.isNotNull(), spark_round(_salt * 400.0, 2))

    return (
        df.select(
            food_uuid_udf(usda_name_expr, lit(None)).alias("ingredient_id"),
            name_expr.alias("name"),
            usda_name_expr.alias("usda_name"),
            _num("calories", "energy_kcal", "energy", "calorie").alias("calories_g"),
            _num("protein_g", "protein", "proteins").alias("protein_g"),
            _num("carbohydrate_g", "carbs_g", "carbohydrates", "carbs", "total_carbohydrate").alias("carbs_g"),
            _num("fat_g", "total_fat", "fat", "lipid").alias("fat_g"),
            lit(None).cast(StringType()).alias("nutriscore"),
            _category_expr().alias("category"),
            _num("fiber_g", "dietary_fiber", "fiber", "fibre").alias("fiber_g"),
            _num("sugar_g", "sugars", "sugar", "total_sugars").alias("sugar_g"),
            least(coalesce(_tc("sodium_mg"), _tc("sodium"), _sodium_from_salt, lit(0.0)), lit(999.9)).alias("sodium_mg"),
            _num("cholesterol_mg", "cholesterol").alias("cholesterol_mg"),
        )
        .dropDuplicates(["usda_name"])
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
