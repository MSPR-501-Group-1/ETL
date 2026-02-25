"""
Complete ETL pipeline orchestrator for gym members
Loads USER, USER_PROFILE, and USER_METRICS tables
"""
from spark.session import get_spark, stop_spark
from processors.gym_members.extract import download_gym_members
from processors.gym_members.transform import transform_gym_members
from processors.gym_members.load import load_gym_members
from processors.gym_members.config import LOCAL_FILE
from utils.logger import get_logger, log_pipeline_start, log_pipeline_success, log_pipeline_failure
import traceback

logger = get_logger(__name__)

def run_pipeline():
    """Execute complete ETL pipeline: Extract -> Transform -> Load"""
    
    log_pipeline_start(logger, "👥 Gym Members Pipeline")
    
    try:
        # Step 1: Extract
        logger.info("📥 EXTRACT: Downloading gym members data...")
        success = download_gym_members()
        
        if not success:
            log_pipeline_failure(logger, "Gym Members", "Extraction failed")
            return False
        
        # Quick count of extracted data
        spark = get_spark("Gym_Members_Pipeline")
        try:
            import pandas as pd
            df_raw = pd.read_csv(str(LOCAL_FILE))
            logger.info(f"✅ Extracted {len(df_raw)} gym members")
        except:
            logger.info(f"✅ Dataset downloaded: {LOCAL_FILE}")
        
        # Step 2: Transform
        logger.info("🔄 TRANSFORM: Processing data...")
        df_user, df_profile, df_metrics = transform_gym_members(spark, str(LOCAL_FILE))
        
        if df_user is None or df_user.count() == 0:
            log_pipeline_failure(logger, "Gym Members", "Transformation produced no data")
            return False
        
        user_count = df_user.count()
        logger.info(f"✅ Transformed {user_count} users into 3 tables")
        
        # Step 3: Load
        logger.info("📦 LOAD: Writing to database...")
        success = load_gym_members(spark, df_user, df_profile, df_metrics)
        
        if success:
            log_pipeline_success(logger, "Gym Members", f"{user_count} users loaded")
            return True
        else:
            log_pipeline_failure(logger, "Gym Members", "Load operation failed")
            return False
            
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Exception occurred: {error_msg}")
        logger.debug(traceback.format_exc())
        log_pipeline_failure(logger, "Gym Members", error_msg)
        return False
        
    finally:
        stop_spark()

if __name__ == "__main__":
    import sys
    success = run_pipeline()
    sys.exit(0 if success else 1)
