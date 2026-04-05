from spark.session import get_spark, stop_spark
from processors.exercises.transform import transform_exercises
from processors.exercises.config import LOCAL_FILE, URLS, PROCESSED_DIR
from utils.github.extract import download_github
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
    
    log_pipeline_start(logger, "🏋️  Exercises Pipeline")

    engine = _build_engine()
    monitor = DataQualityMonitor(engine)
    execution_id = monitor.start_execution()

    records_extracted = 0
    records_loaded = 0
    records_rejected = 0

    try:
        # Step 1: Extract
        logger.info("📥 EXTRACT: Downloading exercises data...")
        file_path = download_github(LOCAL_FILE, URLS, force_download=False)

        if not file_path:
            monitor.end_execution(execution_id, False, 0, 0, 0, "Extraction failed")
            log_pipeline_failure(logger, "Exercises", "Extraction failed")
            return False

        logger.info(f"✅ Source ready: {file_path}")
        
        # Step 2: Transform
        logger.info("🔄 TRANSFORM: Processing data...")
        spark = get_spark("Exercises_Pipeline")
        
        df_transformed = transform_exercises(spark, str(LOCAL_FILE)).cache()
        records_extracted = df_transformed.count()
        log_dataframe_info(logger, df_transformed, "Exercises transformed")

        if records_extracted == 0:
            df_transformed.unpersist()
            monitor.end_execution(execution_id, False, 0, 0, 0, "Transformation produced no data")
            log_pipeline_failure(logger, "Exercises", "Transformation produced no data")
            return False

        # Step 3: Quality check
        logger.info("🔍 QUALITY CHECK: Validating data...")
        rules = {
            "not_null": ["exercise_id", "name", "body_part_target", "difficulty_level", "category"],
        }
        clean_df, records_rejected = monitor.check_dataframe(
            df_transformed, "exercise", execution_id, rules
        )
        df_transformed.unpersist()
        records_loaded = clean_df.count()

        # Step 4: Load
        logger.info("📦 Saving transformed CSV...")
        csv_path = save_table_csv(clean_df, "exercise", PROCESSED_DIR)
        if csv_path is None:
            monitor.end_execution(
                execution_id, False, records_extracted, 0, records_rejected,
                "Failed to save transformed CSV",
            )
            log_pipeline_failure(logger, "Exercises", "Failed to save transformed CSV")
            return False

        monitor.end_execution(
            execution_id, True, records_extracted, records_loaded, records_rejected,
        )
        log_pipeline_success(logger, "Exercises", f"{records_loaded} exercises loaded ({csv_path.name})")
        return True

    except Exception as e:
        error_message = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Exception occurred: {error_message}")
        logger.debug(traceback.format_exc())
        monitor.end_execution(
            execution_id, False, records_extracted, records_loaded, records_rejected, error_message,
        )
        log_pipeline_failure(logger, "Exercises", error_message)
        return False
        
    finally:
        if not reuse_spark:
            stop_spark()

if __name__ == "__main__":
    import sys
    success = run_pipeline()
    sys.exit(0 if success else 1)
