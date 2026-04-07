from functools import reduce

from pyspark.sql import DataFrame
from spark.session import get_spark, stop_spark
from processors.nutrition.transform_nutrition import transform_nutrition
from processors.nutrition.transform_nutrition_values import transform_nutrition_values
from processors.nutrition.config import (
    LOCAL_FILE, RAW_DIR, KAGGLE_DATASET, PROCESSED_DIR,
    LOCAL_FILE_2, RAW_DIR_2, KAGGLE_DATASET_2,
)
from utils.kaggle.extract import download_kaggle
from utils.load import save_table_csv
from utils.data_quality import DataQualityMonitor
from utils.logger import get_logger, log_dataframe_info, log_pipeline_start, log_pipeline_success, log_pipeline_failure
import traceback

from sqlalchemy import create_engine
from utils.db_utils import get_db_config

logger = get_logger(__name__)


def _build_engine():
    db_config = get_db_config()
    url = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    return create_engine(url)


def run_pipeline(reuse_spark: bool = False):

    log_pipeline_start(logger, "🍎 Nutrition Pipeline (combined)")

    engine = _build_engine()
    monitor = DataQualityMonitor(engine)
    execution_id = monitor.start_execution("nutrition")

    records_extracted = 0
    records_loaded = 0
    records_rejected = 0

    try:
        # Step 1a: Extract source 1
        logger.info("📥 EXTRACT: Downloading nutrition data (source 1)...")
        file_path1 = download_kaggle(LOCAL_FILE, RAW_DIR, KAGGLE_DATASET)
        if not file_path1:
            monitor.end_execution(execution_id, 'FAILED', 0, 0, 0, "Extraction failed (source 1)")
            log_pipeline_failure(logger, "Nutrition", "Extraction failed (source 1)")
            return False

        # Step 1b: Extract source 2 (non-blocking: warn and continue if unavailable)
        logger.info("📥 EXTRACT: Downloading nutrition values data (source 2)...")
        file_path2 = download_kaggle(LOCAL_FILE_2, RAW_DIR_2, KAGGLE_DATASET_2)
        if not file_path2:
            logger.warning("⚠️  Source 2 extraction failed — continuing with source 1 only")

        spark = get_spark("Nutrition_Pipeline")
        logger.info(f"✅ Source 1 ready: {LOCAL_FILE}")
        if file_path2:
            logger.info(f"✅ Source 2 ready: {LOCAL_FILE_2}")

        # Step 2: Transform each source
        logger.info("🔄 TRANSFORM: Processing source 1...")
        frames = [transform_nutrition(spark, str(LOCAL_FILE))]

        if file_path2:
            logger.info("🔄 TRANSFORM: Processing source 2...")
            frames.append(transform_nutrition_values(spark, str(LOCAL_FILE_2)))

        # Step 3: Union + deduplicate
        df_transformed = reduce(DataFrame.unionByName, frames).dropDuplicates(["ingredient_id"])

        df_transformed = df_transformed.cache()
        records_extracted = df_transformed.count()
        log_dataframe_info(logger, df_transformed, "Nutrition transformed")

        if records_extracted == 0:
            df_transformed.unpersist()
            monitor.end_execution(execution_id, 'FAILED', 0, 0, 0, "Transformation produced no data")
            log_pipeline_failure(logger, "Nutrition", "Transformation produced no data")
            return False

        logger.info(f"✅ Transformed {records_extracted} ingredients (combined + deduplicated)")

   # Step 4: Quality check
        logger.info("🔍 QUALITY CHECK: Validating data...")
        rules = {
            "not_null": ["ingredient_id", "name", "category"],
            "not_negative": ["calories_g", "protein_g", "carbs_g", "fat_g"],
        }
        clean_df, records_rejected, quality_summary = monitor.check_dataframe(
            df_transformed, "ingredient", execution_id, rules
        )
        df_transformed.unpersist()
        records_loaded = clean_df.count()

        # Step 4: Save transformed CSV
        logger.info("📦 Saving transformed CSV...")
        logger.info(f"🆔 Execution ID: {execution_id}")
        csv_path = save_table_csv(clean_df, "ingredient", PROCESSED_DIR, execution_id)
        if csv_path is None:
            monitor.end_execution(
                execution_id, 'FAILED', records_extracted, 0, records_rejected,
                "Failed to save transformed CSV",
            )
            log_pipeline_failure(logger, "Nutrition", "Failed to save transformed CSV")
            return False

        monitor.end_execution(
            execution_id, 'TRANSFORMED', records_extracted, records_loaded, records_rejected,
        )
        log_pipeline_success(logger, "Nutrition", f"{records_loaded} ingredients loaded ({csv_path.name})")
        return {
            "execution_id": execution_id,
            "records_extracted": records_extracted,
            "records_loaded": records_loaded,
            "records_rejected": records_rejected,
            "quality": quality_summary,
        }

    except Exception as e:
        error_message = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Exception occurred: {error_message}")
        logger.debug(traceback.format_exc())
        monitor.end_execution(
            execution_id, 'FAILED', records_extracted, records_loaded, records_rejected, error_message,
        )
        log_pipeline_failure(logger, "Nutrition", error_message)
        return False

    finally:
        if not reuse_spark:
            stop_spark()

if __name__ == "__main__":
    import sys
    success = run_pipeline()
    sys.exit(0 if success else 1)
