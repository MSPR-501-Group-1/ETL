from spark.session import get_spark, stop_spark
from processors.gym_members.transform import transform_gym_members
from processors.gym_members.config import KAGGLE_DATASET, LOCAL_FILE, LOCAL_ZIP, RAW_DIR, PROCESSED_DIR
from utils.kaggle.extract import download_kaggle
from utils.load import save_and_load_table
from utils.logger import get_logger, log_pipeline_start, log_pipeline_success, log_pipeline_failure
from pyspark.sql.functions import col as _col
import traceback

logger = get_logger(__name__)

def run_pipeline():
    
    log_pipeline_start(logger, "👥 Gym Members Pipeline")
    
    try:
        # Step 1: Extract
        logger.info("📥 EXTRACT: Downloading gym members data...")
        success = download_kaggle(LOCAL_ZIP, LOCAL_FILE, RAW_DIR, KAGGLE_DATASET)
        
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
        df_transformed = transform_gym_members(spark, str(LOCAL_FILE))
        
        if df_transformed is None or df_transformed.count() == 0:
            log_pipeline_failure(logger, "Gym Members", "Transformation produced no data")
            return False
        
        count = df_transformed.count()
        
        logger.info("📦 Splitting and saving per table...")
        # Map flat DF columns → per-table schema columns.
        # profile_updated_at and metrics_created_at are renamed to match the DB schema.
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
        table_load_order = ["user_", "user_profile", "user_metrics"]
        load_failures = []
        for table_name in table_load_order:
            col_map = table_column_map[table_name]
            sub_df = df_transformed.select([
                _col(flat).alias(schema)
                for flat, schema in col_map.items()
                if flat in df_transformed.columns
            ])
            if not save_and_load_table(sub_df, table_name, PROCESSED_DIR):
                load_failures.append(table_name)
        if load_failures:
            log_pipeline_failure(logger, "Gym Members", f"Failed to load: {', '.join(load_failures)}")
            return False
        log_pipeline_success(logger, "Gym Members", f"{count} users loaded into user_ / user_profile / user_metrics")
        return True
            
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
