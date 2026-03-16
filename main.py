import sys
import warnings
warnings.filterwarnings('ignore')
from pathlib import Path
from collections import defaultdict
from processors.exercises.pipeline import run_pipeline as run_exercises_pipeline
from processors.nutrition.pipeline import run_pipeline as run_nutrition_pipeline
from processors.nutrition_values.pipeline import run_pipeline as run_nutrition_values_pipeline
from processors.gym_members.pipeline import run_pipeline as run_gym_members_pipeline
from processors.body_performance.pipeline import run_pipeline as run_body_performance_pipeline
from processors.fitness_tracker.pipeline import run_pipeline as run_fitness_tracker_pipeline
from utils.load import aggregate_to_csv, load_csv_to_postgres, init_db_schema, seed_reference_data
from utils.logger import get_logger
from spark.session import get_spark, stop_spark

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
    
    logger.info("\n👥 STAGE 1: Running Gym Members pipeline...")
    try:
        if not run_gym_members_pipeline():
            failed_pipelines.append("Gym Members")
            logger.error("CRITICAL: Gym Members failed - dependent pipelines may fail")
        else:
            logger.info("✅ Users transformed successfully")
    except Exception as e:
        logger.error(f"Gym Members pipeline failed: {e}")
        failed_pipelines.append("Gym Members")
        logger.error("CRITICAL: Cannot continue without users")
        return False, failed_pipelines
    
    logger.info("\n🏋️  STAGE 2: Running Exercises pipeline...")
    try:
        if not run_exercises_pipeline():
            failed_pipelines.append("Exercises")
        else:
            logger.info("✅ Exercises transformed successfully")
    except Exception as e:
        logger.error(f"Exercises pipeline failed: {e}")
        failed_pipelines.append("Exercises")
    
    logger.info("\n📱 STAGE 3: Running Fitness Tracker pipeline...")
    try:
        if not run_fitness_tracker_pipeline():
            failed_pipelines.append("Fitness Tracker")
        else:
            logger.info("✅ Workout sessions transformed successfully")
    except Exception as e:
        logger.error(f"Fitness Tracker pipeline failed: {e}")
        failed_pipelines.append("Fitness Tracker")

    logger.info("\n💪 STAGE 4: Running Body Performance pipeline...")
    try:
        if not run_body_performance_pipeline():
            failed_pipelines.append("Body Performance")
            logger.error("CRITICAL: Body Performance failed")
        else:
            logger.info("✅ Activity types transformed successfully")
    except Exception as e:
        logger.error(f"Body Performance pipeline failed: {e}")
        failed_pipelines.append("Body Performance")
    
    logger.info("\n🍎 STAGE 5: Running Nutrition pipeline...")
    try:
        if not run_nutrition_pipeline():
            failed_pipelines.append("Nutrition")
        else:
            logger.info("✅ Foods transformed successfully")
    except Exception as e:
        logger.error(f"Nutrition pipeline failed: {e}")
        failed_pipelines.append("Nutrition")
    
    logger.info("\n🥗 STAGE 6: Running Nutrition Values pipeline...")
    try:
        if not run_nutrition_values_pipeline():
            failed_pipelines.append("Nutrition Values")
        else:
            logger.info("✅ Nutrition values transformed successfully")
    except Exception as e:
        logger.error(f"Nutrition Values pipeline failed: {e}")
        failed_pipelines.append("Nutrition Values")

    logger.info("\n🗄️  STAGE 7: Aggregating CSVs and loading to PostgreSQL...")
    try:
        spark = get_spark("ETL_Load")
        processed_root = Path("data/processed")
        table_dataframes = defaultdict(list)

        # Scan all subfolders in data/processed (except _aligned)
        for subdir in processed_root.iterdir():
            if not subdir.is_dir() or subdir.name.startswith("_"):
                continue
            # Find all CSV folders/files in each subdir
            for item in subdir.iterdir():
                # Spark CSV output: folder with part-*.csv inside
                if item.is_dir():
                    part_files = list(item.glob("part-*.csv"))
                    if part_files:
                        df = spark.read.option("header", "true").csv(str(item))
                        table_dataframes[item.name].append(df)
                # Direct CSV file (rare, but support it)
                elif item.suffix == ".csv":
                    df = spark.read.option("header", "true").csv(str(item))
                    table_dataframes[item.stem].append(df)

        global_csv_dir = Path("data/processed/_aligned")
        csv_paths = aggregate_to_csv(table_dataframes, global_csv_dir)

        # --- INIT DB SCHEMA ---
        if not init_db_schema():
            logger.error("❌ Failed to initialize database schema from 01_initdb.sql")
            failed_pipelines.append("DB Schema Init")
            stop_spark()
            return False, failed_pipelines

        # --- SEED REFERENCE DATA (role, health_goal) ---
        # Must run before loading user_ (FK role_id → role.role_id).
        if not seed_reference_data():
            logger.error("❌ Failed to seed reference data (role / health_goal)")
            failed_pipelines.append("Seed Reference Data")
            stop_spark()
            return False, failed_pipelines

        # FK-safe load order matching 01_initdb.sql dependency chain:
        # health_goal and role have no FKs so go first (seed tables).
        # user_ must precede user_profile (user_profile.user_id → user_.user_id).
        # user_metrics and gets come after their parents.
        # workout_session and exercice_details come after user_ and exercise.
        load_order = [
            "health_goal",
            "role",
            "user_",
            "user_profile",
            "user_metrics",
            "gets",
            "exercise",
            "workout_session",
            "exercice_details",
            "ingredients",
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
    logger.info("🔧 Initializing distributed ETL with ordered pipeline execution...")
    success, failed_pipelines = run_all_pipelines_ordered()
    if not success:
        logger.error("ETL process completed with failures")
        sys.exit(1)
    logger.info("🎉 ETL process completed successfully!")
    sys.exit(0)

if __name__ == "__main__":
    main()
