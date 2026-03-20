from fastapi import APIRouter, status

from api.controllers.pipeline_controller import load_pipeline, transform_pipeline
from api.schemas.pipeline_schema import PipelineActionResponse

router = APIRouter(prefix="/api", tags=["pipelines"])

@router.post(
    "/pipelines/exercises/transform",
    response_model=PipelineActionResponse,
    status_code=status.HTTP_200_OK,
)

def transform_exercises() -> PipelineActionResponse:
    return PipelineActionResponse(**transform_pipeline("exercises"))


@router.post(
    "/pipelines/nutrition/transform",
    response_model=PipelineActionResponse,
    status_code=status.HTTP_200_OK,
)
def transform_nutrition() -> PipelineActionResponse:
    return PipelineActionResponse(**transform_pipeline("nutrition"))


@router.post(
    "/pipelines/exercises/load",
    response_model=PipelineActionResponse,
    status_code=status.HTTP_200_OK,
)
def load_exercises() -> PipelineActionResponse:
    return PipelineActionResponse(**load_pipeline("exercises"))


@router.post(
    "/pipelines/nutrition/load",
    response_model=PipelineActionResponse,
    status_code=status.HTTP_200_OK,
)
def load_nutrition() -> PipelineActionResponse:
    return PipelineActionResponse(**load_pipeline("nutrition"))
