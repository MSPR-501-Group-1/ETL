"""Transform nutrition data with PySpark to match the INGREDIENTS schema."""
from pathlib import Path

from pyspark.sql import DataFrame
from pyspark.sql.column import Column
from pyspark.sql.functions import (
    col,
    trim,
    lower,
    when,
    lit,
    round as spark_round,
    coalesce,
    least,
    substring,
    regexp_extract,
)
from pyspark.sql.types import DoubleType, StringType

from utils.transform import ensure_columns, load_raw_data
from utils.uuid_utils import food_uuid_udf
from utils.logger import get_logger

logger = get_logger(__name__)

_NUM_RE = r'^-?\d+(\.\d+)?$'
_MAX_DECIMAL_4_1 = 999.9

_SOURCE_SPECS = {
    "nutrition": {
        "name_column": "food_item",
        "parser": "plain",
        "column_groups": {
            "calories_g": ["calories_kcal"],
            "protein_g": ["protein_g", "protein"],
            "carbs_g": ["carbohydrates_g", "carbohydrate_g", "carbs_g", "carbohydrates"],
            "fat_g": ["fat_g", "total_fat"],
            "fiber_g": ["fiber_g", "dietary_fiber"],
            "sugar_g": ["sugars_g", "sugar_g", "sugars"],
            "sodium_mg": ["sodium_mg", "sodium"],
            "cholesterol_mg": ["cholesterol_mg", "cholesterol"],
        },
        "category_columns": ["category", "food_category"],
        "salt_column": None,
    },
    "nutrition_values": {
        "name_column": "name",
        "parser": "embedded",
        "column_groups": {
            "calories_g": ["calories", "energy_kcal", "energy", "calorie"],
            "protein_g": ["protein_g", "protein", "proteins"],
            "carbs_g": ["carbohydrate_g", "carbs_g", "carbohydrates", "carbs", "total_carbohydrate"],
            "fat_g": ["fat_g", "total_fat", "fat", "lipid"],
            "fiber_g": ["fiber_g", "dietary_fiber", "fiber", "fibre"],
            "sugar_g": ["sugar_g", "sugars", "sugar", "total_sugars"],
            "sodium_mg": ["sodium_mg", "sodium"],
            "cholesterol_mg": ["cholesterol_mg", "cholesterol"],
        },
        "category_columns": ["category", "food_category", "food_group", "group"],
        "salt_column": "salt",
    },
}

_CATEGORY_KEYWORDS = {
    "VEGETABLE": ("vegetable", "veggie", "veg"),
    "FRUIT": ("fruit",),
    "MEAT": ("meat", "beef", "pork", "chicken", "poultry", "lamb", "fish", "seafood"),
    "DAIRY": ("dairy", "milk", "cheese", "yogurt", "cream"),
    "GRAIN": ("grain", "bread", "pasta", "rice", "cereal", "flour"),
    "BEVERAGE": ("beverage", "drink", "juice", "water", "alcohol", "soda"),
    "SNACK": ("snack", "candy", "chocolate", "chip", "dessert", "sweet", "biscuit"),
}


def _tc(c_name: str) -> Column:
    return spark_round(
        when(col(c_name).rlike(_NUM_RE), col(c_name).cast(DoubleType())).otherwise(lit(None)),
        2,
    )


def _tc_embedded(c_name: str) -> Column:
    extracted = regexp_extract(col(c_name), r'(-?\d+\.?\d*)', 1)
    return spark_round(
        when(extracted != lit(""), extracted.cast(DoubleType())).otherwise(lit(None)),
        2,
    )


def _cap(expr: Column) -> Column:
    return least(expr, lit(_MAX_DECIMAL_4_1))


def _normalize_columns(df: DataFrame) -> DataFrame:
    for old_col in df.columns:
        new_col = (
            old_col.lower()
            .replace(" ", "_")
            .replace("(", "")
            .replace(")", "")
            .replace("-", "_")
        )
        df = df.withColumnRenamed(old_col, new_col)
    return df


def _coalesced_text(columns: list[str]) -> Column:
    return coalesce(*[col(name) for name in columns], lit(""))


def _contains_any(expr: Column, keywords: tuple[str, ...]) -> Column:
    condition = lit(False)
    for keyword in keywords:
        condition = condition | expr.contains(keyword)
    return condition


def _category_expr(columns: list[str]) -> Column:
    raw_category = lower(trim(_coalesced_text(columns)))
    expr = lit("OTHER")
    for category_name, keywords in reversed(list(_CATEGORY_KEYWORDS.items())):
        expr = when(_contains_any(raw_category, keywords), lit(category_name)).otherwise(expr)
    return expr


def _numeric_expr(columns: list[str], parser_name: str, extra_expr: Column | None = None) -> Column:
    parser = _tc if parser_name == "plain" else _tc_embedded
    candidates = [parser(column_name) for column_name in columns]
    if extra_expr is not None:
        candidates.append(extra_expr)
    candidates.append(lit(0.0))
    return _cap(coalesce(*candidates))


def _required_columns(spec: dict) -> list[str]:
    required = [spec["name_column"], *spec["category_columns"]]
    for columns in spec["column_groups"].values():
        required.extend(columns)
    if spec["salt_column"]:
        required.append(spec["salt_column"])
    return required


def _map_source_to_mcd_schema(df: DataFrame, spec: dict) -> DataFrame:
    normalized_df = _normalize_columns(df)
    normalized_df = ensure_columns(normalized_df, _required_columns(spec))
    normalized_df = normalized_df.withColumn(
        "name",
        when(col(spec["name_column"]).isNotNull(), trim(col(spec["name_column"]))).otherwise(lit("Unknown")),
    )

    name_expr = substring(col("name"), 1, 50)
    sodium_extra = None
    if spec["salt_column"]:
        sodium_extra = when(
            _tc_embedded(spec["salt_column"]).isNotNull(),
            spark_round(_tc_embedded(spec["salt_column"]) * lit(400.0), 2),
        )

    return normalized_df.select(
        food_uuid_udf(name_expr, lit(None)).alias("ingredients_id"),
        name_expr.alias("name"),
        _numeric_expr(spec["column_groups"]["calories_g"], spec["parser"]).alias("calories_g"),
        _numeric_expr(spec["column_groups"]["protein_g"], spec["parser"]).alias("protein_g"),
        _numeric_expr(spec["column_groups"]["carbs_g"], spec["parser"]).alias("carbs_g"),
        _numeric_expr(spec["column_groups"]["fat_g"], spec["parser"]).alias("fat_g"),
        lit(None).cast(StringType()).alias("nutriscore"),
        _category_expr(spec["category_columns"]).alias("category"),
        _numeric_expr(spec["column_groups"]["fiber_g"], spec["parser"]).alias("fiber_g"),
        _numeric_expr(spec["column_groups"]["sugar_g"], spec["parser"]).alias("sugar_g"),
        _numeric_expr(spec["column_groups"]["sodium_mg"], spec["parser"], sodium_extra).alias("sodium_mg"),
        _numeric_expr(spec["column_groups"]["cholesterol_mg"], spec["parser"]).alias("cholesterol_mg"),
    )


def _clean_ingredients(df: DataFrame) -> DataFrame:
    return df.dropDuplicates(["name"]).filter(
        (col("name").isNotNull())
        & (trim(col("name")) != "")
        & (lower(col("name")) != "unknown")
        & (col("calories_g") >= 0)
        & (col("protein_g") >= 0)
        & (col("carbs_g") >= 0)
        & (col("fat_g") >= 0)
    )


def _transform_source(spark, csv_path: str, source_name: str, label: str) -> DataFrame:
    logger.info(f"⏳ Transforming {label}...")
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"Raw data file not found: {csv_path}")

    df_raw = load_raw_data(spark, csv_path)
    df_mapped = _map_source_to_mcd_schema(df_raw, _SOURCE_SPECS[source_name])
    df_clean = _clean_ingredients(df_mapped)

    logger.info("✅ Transform completed")
    return df_clean


def transform_nutrition(spark, csv_path: str) -> DataFrame:
    return _transform_source(spark, csv_path, "nutrition", "nutrition data")


def transform_nutrition_values(spark, csv_path: str) -> DataFrame:
    return _transform_source(spark, csv_path, "nutrition_values", "nutrition data source 2")


def transform_combined(spark, csv_path1: str, csv_path2: str = None) -> DataFrame:
    frames = []

    if Path(csv_path1).exists():
        logger.info("⏳ Transforming source 1 (nutrition)...")
        frames.append(transform_nutrition(spark, csv_path1))
    else:
        logger.warning(f"⚠️  Source 1 not found: {csv_path1}")

    if csv_path2 and Path(csv_path2).exists():
        logger.info("⏳ Transforming source 2 (nutrition_values)...")
        frames.append(transform_nutrition_values(spark, csv_path2))
    elif csv_path2:
        logger.warning(f"⚠️  Source 2 not found: {csv_path2}")

    if not frames:
        return None

    if len(frames) == 1:
        return frames[0]

    df_union = frames[0]
    for df in frames[1:]:
        df_union = df_union.unionByName(df)

    return df_union.dropDuplicates(["ingredients_id"])


if __name__ == "__main__":
    from processors.nutrition.config import LOCAL_FILE
    from spark.session import get_spark, stop_spark

    spark = get_spark("Transform_Nutrition")

    try:
        df_transformed = transform_nutrition(spark, str(LOCAL_FILE))
        df_transformed.show(5, truncate=False)
        logger.info(f"Total: {df_transformed.count()} foods")
        df_transformed.groupBy("category").count().show()
    finally:
        stop_spark()

