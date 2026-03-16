"""
Complete ETL pipeline orchestrator for body performance
Loads WORKOUT_SESSION and SESSION_DETAIL tables
"""
from spark.session import get_spark, stop_spark
from processors.body_performance.transform import transform_body_performance
from processors.body_performance.config import KAGGLE_DATASET, LOCAL_FILE, RAW_DIR, LOCAL_ZIP, PROCESSED_DIR
from utils.kaggle.extract import download_kaggle
from utils.transform import split_and_save_per_table
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
        df_transformed = transform_body_performance(spark, str(LOCAL_FILE))
        
        if df_transformed is None or df_transformed.count() == 0:
            log_pipeline_failure(logger, "Body Performance", "Transformation produced no data")
            return False
        
        count = df_transformed.count()
        logger.info(f"✅ Transformed {count} body performance records")
        
        # Step 3: Split and save per table.
        # Now that UUIDs are generated in the transform, we populate all three
        # tables: user, user_profile, and user_metrics (with FK user_id linkage).
        logger.info("📦 Splitting and saving per table...")
        table_column_map = {
            "user_": {
                "user_id":       "user_id",
                "email":         "email",
                "password_hash": "password_hash",
                "first_name":    "first_name",
                "last_name":     "last_name",
                "birth_date":    "birth_date",
                "gender_code":   "gender_code",
                "created_at":    "created_at",
                "is_active":     "is_active",
                "role_code":     "role_code",
                "role_id":       "role_id",
            },
            "user_profile": {
                "user_id":              "user_id",
                "height_cm":            "height_cm",
                "current_weight_kg":    "current_weight_kg",
                "activity_level_ref":   "activity_level_ref",
                "allergies":            "allergies",
                "diet_type":            "diet_type",
                "updated_at":           "updated_at",
                "goal_id":              "goal_id",
            },
            "user_metrics": {
                "metric_id":            "metric_id",
                "recorded_date":        "recorded_date",
                "weight_kg":            "weight_kg",
                "body_fat_pourcentage": "body_fat_pourcentage",
                "steps":                "steps",
                "calories_burned":      "calories_burned",
                "heart_rate_avg":       "heart_rate_avg",
                "heart_rate_max":       "heart_rate_max",
                "sleep_hours":          "sleep_hours",
            },
        }
        split_and_save_per_table(df_transformed, PROCESSED_DIR, table_column_map)
        log_pipeline_success(logger, "Body Performance", f"{count} body performance records split into user_ / user_profile / user_metrics")
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
