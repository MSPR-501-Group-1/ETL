import sys
import argparse
import warnings
warnings.filterwarnings('ignore')

from processors.exercises.pipeline       import run_pipeline as run_exercises_pipeline
from processors.nutrition.pipeline       import run_pipeline as run_nutrition_pipeline
from processors.nutrition_values.pipeline import run_pipeline as run_nutrition_values_pipeline
from utils.load import init_db_schema
from utils.seed import seed_reference_data
from utils.logger import get_logger

logger = get_logger(__name__)

def run_exercises() -> bool:
    """Extract, transform and load the exercises dataset → `exercise` table."""
    logger.info("🏋️  Running Exercises pipeline...")
    return run_exercises_pipeline()


def run_nutrition() -> bool:
    """Extract, transform and load the nutrition dataset → ingredient tables."""
    logger.info("🍎 Running Nutrition pipeline...")
    return run_nutrition_pipeline()


def run_nutrition_values() -> bool:
    """Extract, transform and load the nutrition-values dataset → ingredient tables."""
    logger.info("🥗 Running Nutrition Values pipeline...")
    return run_nutrition_values_pipeline()


_PIPELINES = [
    ("exercises",         run_exercises),
    ("nutrition",         run_nutrition),
    ("nutrition_values",  run_nutrition_values),
]


def _init_db() -> bool:
    """Initialize schema and seed reference data. Returns False on failure."""
    logger.info("🗄️  Initializing database schema and seeding reference data...")
    if not init_db_schema():
        logger.error("❌ Failed to initialize database schema — aborting")
        return False
    if not seed_reference_data():
        logger.error("❌ Failed to seed reference data — aborting")
        return False
    logger.info("✅ Database ready")
    return True


def run_all() -> bool:
    """Run all pipelines in dependency order."""
    logger.info("🏥 HEALTHAI COACH — FULL ETL RUN")

    if not _init_db():
        return False

    failed = []
    for name, runner in _PIPELINES:
        try:
            if not runner():
                failed.append(name)
        except Exception as e:
            logger.error(f"{name} pipeline raised: {e}")
            failed.append(name)

    if failed:
        logger.warning(f"⚠️  ETL completed with {len(failed)} failure(s): {', '.join(failed)}")
        return False

    logger.info("✅ ALL PIPELINES COMPLETED SUCCESSFULLY")
    return True


def run_selected(names: list[str]) -> bool:
    """Run only the pipelines whose names are in *names*, in dependency order."""
    pipeline_map = dict(_PIPELINES)
    unknown = [n for n in names if n not in pipeline_map]
    if unknown:
        logger.error(f"Unknown pipeline(s): {', '.join(unknown)}")
        logger.info(f"Available: {', '.join(pipeline_map)}")
        return False

    if not _init_db():
        return False

    failed = []
    # iterate _PIPELINES to preserve dependency order
    for name, runner in _PIPELINES:
        if name not in names:
            continue
        try:
            if not runner():
                failed.append(name)
        except Exception as e:
            logger.error(f"{name} pipeline raised: {e}")
            failed.append(name)

    if failed:
        logger.warning(f"⚠️  Completed with {len(failed)} failure(s): {', '.join(failed)}")
        return False

    logger.info("✅ Selected pipeline(s) completed successfully")
    return True

def main():
    available = [name for name, _ in _PIPELINES]

    parser = argparse.ArgumentParser(
        description="HealthAI Coach ETL — run one, several, or all pipelines."
    )
    parser.add_argument(
        "pipelines",
        nargs="*",
        metavar="PIPELINE",
        help=(
            f"Pipeline(s) to run: {', '.join(available)}. "
            "Omit to run all pipelines in order."
        ),
    )
    args = parser.parse_args()

    if args.pipelines:
        success = run_selected(args.pipelines)
    else:
        success = run_all()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
