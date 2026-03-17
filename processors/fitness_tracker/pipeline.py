from spark.session import get_spark, stop_spark
from processors.fitness_tracker.transform import transform_fitness_tracker
from processors.fitness_tracker.config import KAGGLE_DATASET, LOCAL_FILE, LOCAL_ZIP, RAW_DIR, PROCESSED_DIR
from utils.kaggle.extract import download_kaggle
from utils.load import save_and_load_table
from utils.logger import get_logger

logger = get_logger(__name__)

def run_pipeline():
    
    from utils.logger import log_pipeline_start, log_pipeline_success, log_pipeline_failure
    import traceback
    
    log_pipeline_start(logger, "📱 Fitness Tracker Pipeline")
    
    try:
        # Step 1: Extract
        logger.info("📥 EXTRACT: Downloading fitness tracker data...")
        success = download_kaggle(LOCAL_ZIP, LOCAL_FILE, RAW_DIR, KAGGLE_DATASET)

        
        if not success:
            log_pipeline_failure(logger, "Fitness Tracker", "Extraction failed")
            return False
        
        # Quick count of extracted data
        spark = get_spark("Fitness_Tracker_Pipeline")
        try:
            import pandas as pd
            df_raw = pd.read_csv(str(LOCAL_FILE))
            logger.info(f"✅ Extracted {len(df_raw)} fitness tracker records")
        except:
            logger.info(f"✅ Dataset downloaded: {LOCAL_FILE}")
        
        # Step 2: Transform
        logger.info("🔄 TRANSFORM: Processing data...")
        df_sessions = transform_fitness_tracker(spark, str(LOCAL_FILE))

        if df_sessions is None or df_sessions.count() == 0:
            log_pipeline_failure(logger, "Fitness Tracker", "Transformation produced no data")
            return False

        session_count = df_sessions.count()
        logger.info(f"✅ Transformed {session_count} workout sessions")

        # Step 3: Export to CSV
        logger.info("📦 Export to CSV...")
        if not save_and_load_table(df_sessions, "workout_session", PROCESSED_DIR):
            log_pipeline_failure(logger, "Fitness Tracker", "Failed to load workout_session table")
            return False
        log_pipeline_success(logger, "Fitness Tracker", f"{session_count} sessions loaded")
        return True
            
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Exception occurred: {error_msg}")
        logger.debug(traceback.format_exc())
        log_pipeline_failure(logger, "Fitness Tracker", error_msg)
        return False
        
    finally:
        stop_spark()

if __name__ == "__main__":
    import sys
    success = run_pipeline()
    sys.exit(0 if success else 1)
