"""
Complete ETL pipeline orchestrator for exercises
"""
from spark.session import get_spark, stop_spark
from processors.exercises.extract import download_exercises
from processors.exercises.transform import transform_exercises
from processors.exercises.load import load_exercises
from processors.exercises.config import LOCAL_FILE
from utils.logger import get_logger, log_pipeline_start, log_pipeline_success, log_pipeline_failure
import traceback

logger = get_logger(__name__)

def run_pipeline():
    """Execute complete ETL pipeline: Extract -> Transform -> Load"""
    
    log_pipeline_start(logger, "🏋️  Exercises Pipeline")
    
    try:
        # Step 1: Extract
        logger.info("📥 EXTRACT: Downloading exercises data...")
        data = download_exercises()
        
        if not data:
            log_pipeline_failure(logger, "Exercises", "Extraction failed")
            return False
        
        logger.info(f"✅ Extracted {len(data)} exercises")
        
        # Step 2: Transform
        logger.info("🔄 TRANSFORM: Processing data...")
        spark = get_spark("Exercises_Pipeline")
        
        df_transformed = transform_exercises(spark, str(LOCAL_FILE))
        
        if df_transformed is None or df_transformed.count() == 0:
            log_pipeline_failure(logger, "Exercises", "Transformation produced no data")
            return False
        
        count = df_transformed.count()
        logger.info(f"✅ Transformed {count} exercises")
        
        # Step 3: Load
        logger.info("📦 LOAD: Writing to database...")
        success = load_exercises(spark, df_transformed)
        
        if success:
            log_pipeline_success(logger, "Exercises", f"{count} exercises loaded")
            return True
        else:
            log_pipeline_failure(logger, "Exercises", "Load operation failed")
            return False
            
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
