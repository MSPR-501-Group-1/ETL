"""
HealthAI Coach - ETL Main Entry Point
"""
import sys
import argparse
import warnings

# Suppress all warnings
warnings.filterwarnings('ignore')

from pathlib import Path

from processors.exercises.pipeline import run_pipeline as run_exercises_pipeline
from processors.nutrition.pipeline import run_pipeline as run_nutrition_pipeline
from processors.nutrition_values.pipeline import run_pipeline as run_nutrition_values_pipeline
from processors.gym_members.pipeline import run_pipeline as run_gym_members_pipeline
from processors.body_performance.pipeline import run_pipeline as run_body_performance_pipeline
from processors.fitness_tracker.pipeline import run_pipeline as run_fitness_tracker_pipeline
from processors.exercises.config import PROCESSED_DIR as EXERCISES_DIR
from processors.nutrition.config import PROCESSED_DIR as NUTRITION_DIR
from processors.nutrition_values.config import PROCESSED_DIR as NUTRITION_VALUES_DIR
from processors.gym_members.config import PROCESSED_DIR as GYM_MEMBERS_DIR
from processors.fitness_tracker.config import PROCESSED_DIR as FITNESS_TRACKER_DIR
from processors.body_performance.config import PROCESSED_DIR as BODY_PERFORMANCE_DIR
from utils.load import aggregate_to_csv, load_csv_to_postgres
from utils.logger import get_logger

logger = get_logger(__name__)

def run_all_pipelines_ordered():
    """
    Run all ETL pipelines in explicit order:
    1. gym_members
    2. exercises
    3. fitness_tracker
    4. body_performance
    5. nutrition
    6. nutrition_values
    7. aggregate CSVs → load to PostgreSQL
    """
    logger.info("🏥 HEALTHAI COACH - ORCHESTRATED ETL PIPELINE")
    logger.info("Pipeline Order: Gym Members → Exercises → Fitness Tracker → Body Performance → Nutrition → Nutrition Values → PostgreSQL Load")
    
    failed_pipelines = []
    
    # Stage 1: Gym Members (creates users - dependency for others)
    logger.info("\n👥 STAGE 1: Running Gym Members pipeline...")
    try:
        if not run_gym_members_pipeline():
            failed_pipelines.append("Gym Members")
            logger.error("CRITICAL: Gym Members failed - dependent pipelines may fail")
        else:
            logger.info("✅ Users loaded successfully")
    except Exception as e:
        logger.error(f"Gym Members pipeline failed: {e}")
        failed_pipelines.append("Gym Members")
        logger.error("CRITICAL: Cannot continue without users")
        return False, failed_pipelines
    
    # Stage 2: Exercises
    logger.info("\n🏋️  STAGE 2: Running Exercises pipeline...")
    try:
        if not run_exercises_pipeline():
            failed_pipelines.append("Exercises")
        else:
            logger.info("✅ Exercises loaded successfully")
    except Exception as e:
        logger.error(f"Exercises pipeline failed: {e}")
        failed_pipelines.append("Exercises")
    
    # Stage 3: Fitness Tracker
    logger.info("\n📱 STAGE 3: Running Fitness Tracker pipeline...")
    try:
        if not run_fitness_tracker_pipeline():
            failed_pipelines.append("Fitness Tracker")
        else:
            logger.info("✅ Workout sessions loaded successfully")
    except Exception as e:
        logger.error(f"Fitness Tracker pipeline failed: {e}")
        failed_pipelines.append("Fitness Tracker")

    # Stage 4: Body Performance
    logger.info("\n💪 STAGE 4: Running Body Performance pipeline...")
    try:
        if not run_body_performance_pipeline():
            failed_pipelines.append("Body Performance")
            logger.error("CRITICAL: Body Performance failed")
        else:
            logger.info("✅ Activity types loaded successfully")
    except Exception as e:
        logger.error(f"Body Performance pipeline failed: {e}")
        failed_pipelines.append("Body Performance")
    
    # Stage 5: Nutrition
    logger.info("\n🍎 STAGE 5: Running Nutrition pipeline...")
    try:
        if not run_nutrition_pipeline():
            failed_pipelines.append("Nutrition")
    except Exception as e:
        logger.error(f"Nutrition pipeline failed: {e}")
        failed_pipelines.append("Nutrition")
    
    logger.info("\n🥗 STAGE 6: Running Nutrition Values pipeline...")
    try:
        if not run_nutrition_values_pipeline():
            failed_pipelines.append("Nutrition Values")
    except Exception as e:
        logger.error(f"Nutrition Values pipeline failed: {e}")
        failed_pipelines.append("Nutrition Values")

    # Stage 7: Aggregate individual CSVs per DB table and bulk-load into PostgreSQL
    logger.info("\n🗄️  STAGE 7: Aggregating CSVs and loading to PostgreSQL...")
    try:
        from spark.session import get_spark, stop_spark

        spark = get_spark("ETL_Load")

        def _read_csv(path: Path):
            if path.exists():
                return spark.read.option("header", "true").csv(str(path))
            logger.warning(f"CSV not found, skipping: {path}")
            return None

        table_dataframes = {}

        df = _read_csv(EXERCISES_DIR / "exercise")
        if df is not None:
            table_dataframes["exercise"] = [df]

        # food — union of both nutrition sources
        food_dfs = [df for df in (
            _read_csv(NUTRITION_DIR / "food"),
            _read_csv(NUTRITION_VALUES_DIR / "food"),
        ) if df is not None]
        if food_dfs:
            table_dataframes["food"] = food_dfs

        for table in ("user", "user_profile", "user_metrics"):
            df = _read_csv(GYM_MEMBERS_DIR / table)
            if df is not None:
                table_dataframes[table] = [df]

        df = _read_csv(FITNESS_TRACKER_DIR / "activity_type")
        if df is not None:
            table_dataframes["activity_type"] = [df]

        # workout_session — union of fitness_tracker + body_performance
        workout_dfs = [df for df in (
            _read_csv(FITNESS_TRACKER_DIR / "workout_session"),
            _read_csv(BODY_PERFORMANCE_DIR / "workout_session"),
        ) if df is not None]
        if workout_dfs:
            table_dataframes["workout_session"] = workout_dfs

        df = _read_csv(BODY_PERFORMANCE_DIR / "session_detail")
        if df is not None:
            table_dataframes["session_detail"] = [df]

        global_csv_dir = Path("data/processed/_aligned")
        csv_paths = aggregate_to_csv(table_dataframes, global_csv_dir)

        load_order = [
            "user", "exercise", "food",
            "activity_type", "user_profile", "user_metrics",
            "workout_session", "session_detail",
        ]
        load_failures = []
        for table in load_order:
            if table not in csv_paths:
                continue
            if not load_csv_to_postgres(csv_paths[table], table):
                load_failures.append(table)

        stop_spark()

        if load_failures:
            logger.error(f"❌ Failed to load tables: {', '.join(load_failures)}")
            failed_pipelines.append("PostgreSQL Load")
        else:
            logger.info("✅ All tables loaded into PostgreSQL successfully")

    except Exception as e:
        logger.error(f"Stage 7 (PostgreSQL load) failed: {e}")
        failed_pipelines.append("PostgreSQL Load")

    # Final summary
    success = len(failed_pipelines) == 0
    if success:
        logger.info("\n✅ ALL PIPELINES COMPLETED SUCCESSFULLY")
    else:
        logger.warning(f"\n⚠️  ETL COMPLETED WITH {len(failed_pipelines)} FAILURES")
        for pipeline in failed_pipelines:
            logger.error(f"   ❌ {pipeline}")
    
    return success, failed_pipelines

def main():
    """Main ETL orchestrator"""
    parser = argparse.ArgumentParser(description='HealthAI Coach ETL Pipeline')
    parser.add_argument(
        '--pipeline',
        choices=['exercises', 'nutrition', 'nutrition-values', 'nutrition-all', 
                 'gym-members', 'body-performance', 'fitness-tracker', 'all'],
        default='all',
        help='Pipeline to run (nutrition-all runs both nutrition sources, all runs everything)'
    )
    
    args = parser.parse_args()
    
    # If running all pipelines, use ordered execution
    if args.pipeline == 'all':
        logger.info("🔧 Initializing distributed ETL with ordered pipeline execution...")
        success, failed_pipelines = run_all_pipelines_ordered()
        
        if not success:
            logger.error("ETL process completed with failures")
            sys.exit(1)
        
        logger.info("🎉 ETL process completed successfully!")
        sys.exit(0)
    
    # Individual pipeline execution
    logger.info(f"🏥 HEALTHAI COACH - ETL PIPELINE: {args.pipeline.upper()}")
    
    success = True
    failed_pipelines = []
    
    if args.pipeline == 'exercises':
        logger.info("🏋️  Running EXERCISES pipeline...")
        try:
            if not run_exercises_pipeline():
                success = False
                failed_pipelines.append("Exercises")
        except Exception as e:
            logger.error(f"EXERCISES pipeline failed: {e}")
            success = False
            failed_pipelines.append("Exercises")
    
    elif args.pipeline == 'nutrition' or args.pipeline == 'nutrition-all':
        logger.info("🍎 Running NUTRITION pipeline (Daily Food)...")
        try:
            if not run_nutrition_pipeline():
                success = False
                failed_pipelines.append("Nutrition")
        except Exception as e:
            logger.error(f"NUTRITION pipeline failed: {e}")
            success = False
            failed_pipelines.append("Nutrition")
        
        if args.pipeline == 'nutrition-all':
            logger.info("🥗 Running NUTRITION VALUES pipeline (Common Foods)...")
            try:
                if not run_nutrition_values_pipeline():
                    success = False
                    failed_pipelines.append("Nutrition Values")
            except Exception as e:
                logger.error(f"NUTRITION VALUES pipeline failed: {e}")
                success = False
                failed_pipelines.append("Nutrition Values")
    
    elif args.pipeline == 'nutrition-values':
        logger.info("🥗 Running NUTRITION VALUES pipeline (Common Foods)...")
        try:
            if not run_nutrition_values_pipeline():
                success = False
                failed_pipelines.append("Nutrition Values")
        except Exception as e:
            logger.error(f"NUTRITION VALUES pipeline failed: {e}")
            success = False
            failed_pipelines.append("Nutrition Values")
    
    elif args.pipeline == 'gym-members':
        logger.info("👥 Running GYM MEMBERS pipeline...")
        try:
            if not run_gym_members_pipeline():
                success = False
                failed_pipelines.append("Gym Members")
        except Exception as e:
            logger.error(f"GYM MEMBERS pipeline failed: {e}")
            success = False
            failed_pipelines.append("Gym Members")
    
    elif args.pipeline == 'body-performance':
        logger.info("💪 Running BODY PERFORMANCE pipeline...")
        try:
            if not run_body_performance_pipeline():
                success = False
                failed_pipelines.append("Body Performance")
        except Exception as e:
            logger.error(f"BODY PERFORMANCE pipeline failed: {e}")
            success = False
            failed_pipelines.append("Body Performance")
    
    elif args.pipeline == 'fitness-tracker':
        logger.info("📱 Running FITNESS TRACKER pipeline...")
        try:
            if not run_fitness_tracker_pipeline():
                success = False
                failed_pipelines.append("Fitness Tracker")
        except Exception as e:
            logger.error(f"FITNESS TRACKER pipeline failed: {e}")
            success = False
            failed_pipelines.append("Fitness Tracker")
    
    if success:
        logger.info("✅ ETL COMPLETED SUCCESSFULLY")
    else:
        logger.error("❌ ETL COMPLETED WITH FAILURES")
        logger.error(f"   Failed pipelines: {', '.join(failed_pipelines)}")
        if any(p in failed_pipelines for p in ["Nutrition", "Nutrition Values", "Gym Members", "Body Performance", "Fitness Tracker"]):
            logger.info("\n💡 Note: Kaggle pipelines require credentials.")
            logger.info("   Set KAGGLE_USERNAME and KAGGLE_KEY environment variables,")
            logger.info("   or mount ~/.kaggle/kaggle.json in docker-compose.yml")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
