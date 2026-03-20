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
    success = run_pipeline(name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Pipeline execution failed", "pipeline": name},
        )

    logger.info(f"📥 API transform request succeeded: pipeline={name}")
    return {"pipeline": name, "status": "transformed", "message": "Transform réussi"}


def load_pipeline(name: str) -> dict:
    _validate_pipeline_name(name)
    success = load_pipeline_data(name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Load failed", "pipeline": name},
        )

    logger.info(f"📦 API load request succeeded: pipeline={name}")
    return {"pipeline": name, "status": "loaded", "message": "Load réussi"}
