from pyspark.sql import functions as F
from spark.session import get_spark, stop_spark
from processors.nutrition.transform import transform_combined
from processors.nutrition.config import (
    LOCAL_FILE, LOCAL_ZIP, RAW_DIR, KAGGLE_DATASET, PROCESSED_DIR,
    LOCAL_FILE_2, LOCAL_ZIP_2, RAW_DIR_2, KAGGLE_DATASET_2,
)
from utils.kaggle.extract import download_kaggle
from utils.load import save_and_load_table
from utils.logger import get_logger, log_dataframe_info, log_pipeline_start, log_pipeline_success, log_pipeline_failure
import traceback

logger = get_logger(__name__)

def run_pipeline(reuse_spark: bool = False):

    log_pipeline_start(logger, "🍎 Nutrition Pipeline (combined)")

    try:
        # Step 1a: Extract source 1
        logger.info("📥 EXTRACT: Downloading nutrition data (source 1)...")
        file_path1 = download_kaggle(LOCAL_ZIP, LOCAL_FILE, RAW_DIR, KAGGLE_DATASET)
        if not file_path1:
            log_pipeline_failure(logger, "Nutrition", "Extraction failed (source 1)")
            return False

        # Step 1b: Extract source 2 (non-blocking: warn and continue if unavailable)
        logger.info("📥 EXTRACT: Downloading nutrition values data (source 2)...")
        file_path2 = download_kaggle(LOCAL_ZIP_2, LOCAL_FILE_2, RAW_DIR_2, KAGGLE_DATASET_2)
        if not file_path2:
            logger.warning("⚠️  Source 2 extraction failed — continuing with source 1 only")

        spark = get_spark("Nutrition_Pipeline")
        logger.info(f"✅ Source 1 ready: {LOCAL_FILE}")
        if file_path2:
            logger.info(f"✅ Source 2 ready: {LOCAL_FILE_2}")

        # Step 2: Transform + Union
        logger.info("🔄 TRANSFORM: Processing and merging both sources...")
        df_transformed = transform_combined(
            spark,
            str(LOCAL_FILE),
            str(LOCAL_FILE_2) if file_path2 else None,
        )

        if df_transformed is None:
            log_pipeline_failure(logger, "Nutrition", "Transformation produced no data")
            end_execution(execution_id, status=False, error_message="Transform produced no data")
            return False

        df_transformed = df_transformed.cache()
        count = log_dataframe_info(logger, df_transformed, "Nutrition transformed")
        if count == 0:
            df_transformed.unpersist()
            log_pipeline_failure(logger, "Nutrition", "Transformation produced no data")
            end_execution(execution_id, status=False, error_message="Transform produced no data")
            return False

        logger.info(f"✅ Transformed {count} ingredients (combined + deduplicated)")

        # Step 3: Single load into ingredients
        logger.info("📦 Export to CSV and load into PostgreSQL...")
        if not save_and_load_table(df_transformed, "ingredients", PROCESSED_DIR):
            df_transformed.unpersist()
            log_pipeline_failure(logger, "Nutrition", "Failed to load ingredients table")
            end_execution(execution_id, status=False, error_message="Load failed")
            return False
        df_transformed.unpersist()

        log_pipeline_success(logger, "Nutrition", f"{count} ingredients loaded (2 sources merged)")
        return True

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Exception occurred: {error_msg}")
        logger.debug(traceback.format_exc())
        log_pipeline_failure(logger, "Nutrition", error_msg)
        end_execution(execution_id, status=False, error_message=error_msg[:50])
        return False

    finally:
        if not reuse_spark:
            stop_spark()

if __name__ == "__main__":
    import sys
    success = run_pipeline()
    sys.exit(0 if success else 1)
