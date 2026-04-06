from typing import Optional
from pydantic import BaseModel


class QualityCheckResponse(BaseModel):
    check_id: str
    target_table: str
    check_type: str
    check_rule: str
    records_checked: int
    records_failed: int
    status: bool
    checked_at: str


class PipelineActionResponse(BaseModel):
    pipeline: str
    status: str
    # transform endpoints
    execution_id: Optional[str] = None
    records_extracted: Optional[int] = None
    records_loaded: Optional[int] = None
    records_rejected: Optional[int] = None
    quality_check: Optional[QualityCheckResponse] = None
    # load endpoints / legacy
    message: Optional[str] = None
