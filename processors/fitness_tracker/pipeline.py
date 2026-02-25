"""
Complete ETL pipeline orchestrator for fitness tracker
Loads ACTIVITY_TYPE and WORKOUT_SESSION tables
"""
from spark.session import get_spark, stop_spark
from processors.fitness_tracker.extract import download_fitness_tracker
from processors.fitness_tracker.transform import transform_fitness_tracker
from processors.fitness_tracker.load import load_fitness_tracker
from processors.fitness_tracker.config import LOCAL_FILE
from utils.logger import get_logger

logger = get_logger(__name__)

def run_pipeline():
    """Execute complete ETL pipeline: Extract -> Transform -> Load"""
    
    from utils.logger import log_pipeline_start, log_pipeline_success, log_pipeline_failure
    import traceback
    
    log_pipeline_start(logger, "📱 Fitness Tracker Pipeline")
    
    try:
        # Step 1: Extract
        logger.info("📥 EXTRACT: Downloading fitness tracker data...")
        success = download_fitness_tracker()
        
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
        df_activities, df_sessions = transform_fitness_tracker(spark, str(LOCAL_FILE))
        
        if df_activities is None or df_activities.count() == 0:
            log_pipeline_failure(logger, "Fitness Tracker", "Transformation produced no data")
            return False
        
        activity_count = df_activities.count()
        session_count = df_sessions.count()
        logger.info(f"✅ Transformed {activity_count} activity types and {session_count} sessions")
        
        # Step 3: Load
        logger.info("📦 LOAD: Writing to database...")
        success = load_fitness_tracker(spark, df_activities, df_sessions)
        
        if success:
            log_pipeline_success(logger, "Fitness Tracker", f"{activity_count} activities, {session_count} sessions loaded")
            return True
        else:
            log_pipeline_failure(logger, "Fitness Tracker", "Load operation failed")
            return False
            
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
