from threading import Lock

from spark.session import stop_spark

from processors.exercises.pipeline import run_pipeline as run_exercises_pipeline
from processors.nutrition.pipeline import run_pipeline as run_nutrition_pipeline
from utils.load import init_db_schema, load_table_from_processed
from utils.logger import get_logger
from processors.exercises.config import PROCESSED_DIR as EXERCISES_PROCESSED_DIR
from processors.nutrition.config import PROCESSED_DIR as NUTRITION_PROCESSED_DIR

logger = get_logger(__name__)

_PIPELINES = {
    "exercises": run_exercises_pipeline,
    "nutrition": run_nutrition_pipeline,
}

_PIPELINE_TARGETS = {
    "exercises": ("exercise", EXERCISES_PROCESSED_DIR),
    "nutrition": ("ingredients", NUTRITION_PROCESSED_DIR),
}

_EXECUTION_LOCK = Lock()


def list_pipelines() -> list[str]:
    return list(_PIPELINES)


def run_pipeline(name: str) -> bool:
    if name not in _PIPELINES:
        logger.error(f"Unknown pipeline: {name}")
        logger.info(f"Available: {', '.join(list_pipelines())}")
        return False

    with _EXECUTION_LOCK:
        logger.info(f"🚀 Pipeline run started: pipeline={name}")
        try:
            return _PIPELINES[name](reuse_spark=True)
        finally:
            stop_spark()


def load_pipeline_data(name: str) -> bool:
    target = _PIPELINE_TARGETS.get(name)
    if target is None:
        logger.error(f"Unknown pipeline for load: {name}")
        logger.info(f"Available: {', '.join(list_pipelines())}")
        return False

    if not _init_db():
        return False

    table_name, output_dir = target
    logger.info(f"📤 Loading transformed CSV for pipeline={name}, table={table_name}")
    return load_table_from_processed(table_name, output_dir)

def _init_db() -> bool:
    logger.info("🗄️ Initializing database schema...")
    if not init_db_schema():
        logger.error("❌ Failed to initialize database schema — aborting")
        return False
    logger.info("✅ Database ready")
    return True