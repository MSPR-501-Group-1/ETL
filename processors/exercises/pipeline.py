from spark.session import get_spark, stop_spark
from processors.exercises.transform import transform_exercises
from processors.exercises.config import LOCAL_FILE, URLS, PROCESSED_DIR
from utils.github.extract import download_github
from utils.load import save_and_load_table
from utils.profiling import profile_dataframe

from utils.logger import get_logger, log_pipeline_start, log_pipeline_success, log_pipeline_failure
import traceback

logger = get_logger(__name__)

def run_pipeline():
    
    log_pipeline_start(logger, "🏋️  Exercises Pipeline")
    
    try:
        # Step 1: Extract
        logger.info("📥 EXTRACT: Downloading exercises data...")
        data = download_github(LOCAL_FILE, URLS, force_download=False)

        
        if not data:
            log_pipeline_failure(logger, "Exercises", "Extraction failed")
            return False
        
        logger.info(f"✅ Extracted {len(data)} exercises")
        
        # Step 2: Transform
        logger.info("🔄 TRANSFORM: Processing data...")
        spark = get_spark("Exercises_Pipeline")
        
        df_transformed = transform_exercises(spark, str(LOCAL_FILE))
        count = df_transformed.count()

        if count == 0:
            log_pipeline_failure(logger, "Exercises", "Transformation produced no data")
            return False

        # Optional data profiling (set ENABLE_PROFILING=true to activate)
        profile_dataframe(df_transformed, "exercises")

        logger.info("📦 Save and load to PostgreSQL...")
        if not save_and_load_table(df_transformed, "exercise", PROCESSED_DIR):
            log_pipeline_failure(logger, "Exercises", "Failed to load exercise table")
            return False
        log_pipeline_success(logger, "Exercises", f"{count} exercises loaded")
        return True

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Exception occurred: {error_msg}")
        logger.debug(traceback.format_exc())
        log_pipeline_failure(logger, "Exercises", error_msg)
        return False
        
    finally:
        stop_spark()

if __name__ == "__main__":
    import sys
    success = run_pipeline()
    sys.exit(0 if success else 1)
