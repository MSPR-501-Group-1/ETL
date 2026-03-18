from spark.session import get_spark, stop_spark
from processors.exercises.transform import transform_exercises
from processors.exercises.config import LOCAL_FILE, URLS, PROCESSED_DIR
from utils.github.extract import download_github
from utils.load import save_and_load_table

from utils.logger import get_logger, log_dataframe_info, log_pipeline_start, log_pipeline_success, log_pipeline_failure
import traceback

logger = get_logger(__name__)

def run_pipeline(reuse_spark: bool = False):
    
    log_pipeline_start(logger, "🏋️  Exercises Pipeline")
    
    try:
        # Step 1: Extract
        logger.info("📥 EXTRACT: Downloading exercises data...")
        file_path = download_github(LOCAL_FILE, URLS, force_download=False)

        if not file_path:
            log_pipeline_failure(logger, "Exercises", "Extraction failed")
            return False

        logger.info(f"✅ Source ready: {file_path}")
        
        # Step 2: Transform
        logger.info("🔄 TRANSFORM: Processing data...")
        spark = get_spark("Exercises_Pipeline")
        
        df_transformed = transform_exercises(spark, str(LOCAL_FILE)).cache()
        count = log_dataframe_info(logger, df_transformed, "Exercises transformed")

        if count == 0:
            df_transformed.unpersist()
            log_pipeline_failure(logger, "Exercises", "Transformation produced no data")
            return False
        
        logger.info("📦 Save and load to PostgreSQL...")
        if not save_and_load_table(df_transformed, "exercise", PROCESSED_DIR):
            df_transformed.unpersist()
            log_pipeline_failure(logger, "Exercises", "Failed to load exercise table")
            return False
        df_transformed.unpersist()
        log_pipeline_success(logger, "Exercises", f"{count} exercises loaded")
        return True

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Exception occurred: {error_msg}")
        logger.debug(traceback.format_exc())
        log_pipeline_failure(logger, "Exercises", error_msg)
        return False
        
    finally:
        if not reuse_spark:
            stop_spark()

if __name__ == "__main__":
    import sys
    success = run_pipeline()
    sys.exit(0 if success else 1)
