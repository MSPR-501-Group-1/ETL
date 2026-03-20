from pydantic import BaseModel


class PipelineActionResponse(BaseModel):
    pipeline: str
    status: str
    message: str
