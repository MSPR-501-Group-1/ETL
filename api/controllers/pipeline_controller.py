from fastapi import HTTPException, status

from services.pipeline_runner import list_pipelines, load_pipeline_data, run_pipeline
from utils.logger import get_logger

logger = get_logger(__name__)


def _validate_pipeline_name(name: str) -> None:
    available = list_pipelines()
    if name not in available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Unknown pipeline",
                "pipeline": name,
                "available": available,
            },
        )


def transform_pipeline(name: str) -> dict:
    _validate_pipeline_name(name)
    result = run_pipeline(name)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Pipeline execution failed", "pipeline": name},
        )

    logger.info(f"📥 API transform request succeeded: pipeline={name}")
    return {
        "pipeline": name,
        "status": "transformed",
        "execution_id": result.get("execution_id"),
        "records_extracted": result.get("records_extracted"),
        "records_loaded": result.get("records_loaded"),
        "records_rejected": result.get("records_rejected"),
        "quality_check": result.get("quality"),
    }


def load_pipeline(name: str, execution_id: str) -> dict:
    _validate_pipeline_name(name)
    success = load_pipeline_data(name, execution_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Load failed", "pipeline": name},
        )

    logger.info(f"📦 API load request succeeded: pipeline={name}, execution_id={execution_id}")
    return {"pipeline": name, "status": "loaded", "execution_id": execution_id}
