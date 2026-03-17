from pyspark.sql import functions as F
from spark.session import get_spark, stop_spark
from processors.nutrition.transform import transform_nutrition
from processors.nutrition.config import LOCAL_FILE, LOCAL_ZIP, RAW_DIR, KAGGLE_DATASET, PROCESSED_DIR, SOURCE_ID
from utils.kaggle.extract import download_kaggle
from utils.load import save_and_load_table
from utils.logger import get_logger, log_pipeline_start, log_pipeline_success, log_pipeline_failure
from utils.etl_tracking import start_execution, end_execution
from utils.quality import QualityRule, run_quality_checks
import traceback

logger = get_logger(__name__)

def run_pipeline():
    
    log_pipeline_start(logger, "🍎 Nutrition Pipeline")

    # ── Ouvrir le run de tracking ─────────────────────────────────────────────
    execution_id = start_execution(SOURCE_ID)
    records_extracted = 0
    records_rejected  = 0

    try:
        # Step 1: Extract
        logger.info("📥 EXTRACT: Downloading nutrition data...")
        file_path = download_kaggle(LOCAL_ZIP, LOCAL_FILE, RAW_DIR, KAGGLE_DATASET)

        if not file_path:
            log_pipeline_failure(logger, "Nutrition", "Extraction failed")
            end_execution(execution_id, status=False, error_message="Extraction failed")
            return False

        # Step 1b: Charger le CSV brut avec Spark
        spark = get_spark("Nutrition_Pipeline")
        df_raw = spark.read.option("header", "true").csv(str(LOCAL_FILE))
        records_extracted = df_raw.count()
        logger.info(f"✅ Extracted {records_extracted} foods")

        # Step 1c: Data Quality checks sur le DataFrame brut
        # Les noms de colonnes correspondent au CSV brut avant normalisation
        rules = [
            QualityRule(
                check_type="NULL_CHECK",
                check_rule="Food_Item IS NOT NULL",
                target_table="ingredients",
                fail_condition=F.col("Food_Item").isNull(),
                source_col="Food_Item",
                identifier_col="Food_Item",
            ),
            QualityRule(
                check_type="RANGE_CHECK",
                check_rule="Calories (kcal) >= 0",
                target_table="ingredients",
                fail_condition=F.expr("try_cast(`Calories (kcal)` as double)") < 0,
                source_col="Calories (kcal)",
                identifier_col="Food_Item",
            ),
        ]
        _, records_rejected = run_quality_checks(
            df_raw, rules, execution_id, source_table="nutrition_raw"
        )

        # Step 2: Transform
        logger.info("🔄 TRANSFORM: Processing data...")
        df_transformed = transform_nutrition(spark, str(LOCAL_FILE))
        
        if df_transformed is None:
            log_pipeline_failure(logger, "Nutrition", "Transformation produced no data")
            end_execution(execution_id, status=False, error_message="Transform produced no data")
            return False

        count = df_transformed.count()
        if count == 0:
            log_pipeline_failure(logger, "Nutrition", "Transformation produced no data")
            end_execution(execution_id, status=False, error_message="Transform produced no data")
            return False

        logger.info(f"✅ Transformed {count} foods")

        # Step 3: Export to CSV + chargement PostgreSQL
        logger.info("📦 Export to CSV...")
        if not save_and_load_table(df_transformed, "ingredients", PROCESSED_DIR):
            log_pipeline_failure(logger, "Nutrition", "Failed to load ingredients table")
            end_execution(execution_id, status=False, error_message="Load failed")
            return False

        end_execution(execution_id, status=True,
                      records_extracted=records_extracted,
                      records_loaded=count,
                      records_rejected=records_rejected)
        log_pipeline_success(logger, "Nutrition", f"{count} ingredients loaded")
        return True
            
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Exception occurred: {error_msg}")
        logger.debug(traceback.format_exc())
        log_pipeline_failure(logger, "Nutrition", error_msg)
        end_execution(execution_id, status=False, error_message=error_msg[:50])
        return False
        
    finally:
        stop_spark()

if __name__ == "__main__":
    import sys
    success = run_pipeline()
    sys.exit(0 if success else 1)
