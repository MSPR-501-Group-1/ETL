"""
Complete ETL pipeline orchestrator for nutrition
"""
from spark.session import get_spark, stop_spark
from processors.nutrition.transform import transform_nutrition
from processors.nutrition.config import LOCAL_FILE, LOCAL_ZIP, RAW_DIR, KAGGLE_DATASET, PROCESSED_DIR
from utils.kaggle.extract import download_kaggle
from utils.transform import save_to_csv
from utils.logger import get_logger, log_pipeline_start, log_pipeline_success, log_pipeline_failure
import traceback

logger = get_logger(__name__)

def run_pipeline():
    
    log_pipeline_start(logger, "🍎 Nutrition Pipeline")
    
    try:
        # Step 1: Extract
        logger.info("📥 EXTRACT: Downloading nutrition data...")
        file_path = download_kaggle(LOCAL_ZIP, LOCAL_FILE, RAW_DIR, KAGGLE_DATASET)
    
        
        if not file_path:
            log_pipeline_failure(logger, "Nutrition", "Extraction failed")
            return False
        
        # Quick count of extracted data
        spark = get_spark("Nutrition_Pipeline")
        try:
            import pandas as pd
            df_raw = pd.read_csv(str(LOCAL_FILE))
            logger.info(f"✅ Extracted {len(df_raw)} foods")
        except:
            logger.info(f"✅ Extracted data to {file_path}")
        
        # Step 2: Transform
        logger.info("🔄 TRANSFORM: Processing data...")
        df_transformed = transform_nutrition(spark, str(LOCAL_FILE))
        
        if df_transformed is None or df_transformed.count() == 0:
            log_pipeline_failure(logger, "Nutrition", "Transformation produced no data")
            return False
        
        count = df_transformed.count()
        logger.info(f"✅ Transformed {count} foods")
        
        # Step 3: Export to CSV
        logger.info("📦 Export to CSV...")
        save_to_csv(df_transformed, str(PROCESSED_DIR / "food"))
        log_pipeline_success(logger, "Nutrition", f"{count} foods exported to CSV")
        return True
            
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Exception occurred: {error_msg}")
        logger.debug(traceback.format_exc())
        log_pipeline_failure(logger, "Nutrition", error_msg)
        return False
        
    finally:
        stop_spark()

if __name__ == "__main__":
    import sys
    success = run_pipeline()
    sys.exit(0 if success else 1)
