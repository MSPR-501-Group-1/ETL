from fastapi import APIRouter, status

from api.controllers.pipeline_controller import load_pipeline, replay_dlq, transform_pipeline
from api.schemas.pipeline_schema import DLQReplayResponse, PipelineActionResponse

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
    "/pipelines/exercises/load/{execution_id}",
    response_model=PipelineActionResponse,
    status_code=status.HTTP_200_OK,
)
def load_exercises(execution_id: str) -> PipelineActionResponse:
    return PipelineActionResponse(**load_pipeline("exercises", execution_id))


@router.post(
    "/pipelines/nutrition/load/{execution_id}",
    response_model=PipelineActionResponse,
    status_code=status.HTTP_200_OK,
)
def load_nutrition(execution_id: str) -> PipelineActionResponse:
    return PipelineActionResponse(**load_pipeline("nutrition", execution_id))


@router.post(
    "/dlq/replay/{source_table}/{execution_id}",
    response_model=DLQReplayResponse,
    status_code=status.HTTP_200_OK,
)
def replay_dlq_rows(source_table: str, execution_id: str) -> DLQReplayResponse:
    return DLQReplayResponse(**replay_dlq(source_table, execution_id))
