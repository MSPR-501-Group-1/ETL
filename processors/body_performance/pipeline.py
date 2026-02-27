"""
Complete ETL pipeline orchestrator for body performance
Loads WORKOUT_SESSION and SESSION_DETAIL tables
"""
from spark.session import get_spark, stop_spark
from processors.body_performance.transform import transform_body_performance
from processors.body_performance.config import KAGGLE_DATASET, LOCAL_FILE, RAW_DIR, LOCAL_ZIP, PROCESSED_DIR
from utils.kaggle.extract import download_kaggle
from utils.transform import save_to_csv
from utils.logger import get_logger

logger = get_logger(__name__)

def run_pipeline():
    
    from utils.logger import log_pipeline_start, log_pipeline_success, log_pipeline_failure
    import traceback
    
    log_pipeline_start(logger, "💪 Body Performance Pipeline")
    
    try:
        # Step 1: Extract
        logger.info("📥 EXTRACT: Downloading body performance data...")
        success = download_kaggle(LOCAL_ZIP, LOCAL_FILE, RAW_DIR, KAGGLE_DATASET)
    
        
        if not success:
            log_pipeline_failure(logger, "Body Performance", "Extraction failed")
            return False
        
        # Quick count of extracted data
        spark = get_spark("Body_Performance_Pipeline")
        try:
            import pandas as pd
            df_raw = pd.read_csv(str(LOCAL_FILE))
            logger.info(f"✅ Extracted {len(df_raw)} body performance records")
        except:
            logger.info(f"✅ Dataset downloaded: {LOCAL_FILE}")
        
        # Step 2: Transform
        logger.info("🔄 TRANSFORM: Processing data...")
        df_sessions, df_details = transform_body_performance(spark, str(LOCAL_FILE))
        
        if df_sessions is None or df_sessions.count() == 0:
            log_pipeline_failure(logger, "Body Performance", "Transformation produced no data")
            return False
        
        session_count = df_sessions.count()
        detail_count = df_details.count() if df_details else 0
        logger.info(f"✅ Transformed {session_count} sessions and {detail_count} details")
        
        # Step 3: Export to CSV
        logger.info("📦 Export to CSV...")
        save_to_csv(df_sessions, str(PROCESSED_DIR / "workout_session"))
        if df_details is not None:
            save_to_csv(df_details, str(PROCESSED_DIR / "session_detail"))
        log_pipeline_success(logger, "Body Performance", f"{session_count} sessions, {detail_count} details exported to CSV")
        return True
            
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Exception occurred: {error_msg}")
        logger.debug(traceback.format_exc())
        log_pipeline_failure(logger, "Body Performance", error_msg)
        return False
        
    finally:
        stop_spark()

if __name__ == "__main__":
    import sys
    success = run_pipeline()
    sys.exit(0 if success else 1)
