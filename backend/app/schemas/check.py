from pydantic import BaseModel, Field

from app.constants.finding_status import ALL_FINDING_STATUSES


class CheckCreate(BaseModel):
    scope: str = Field(default="all", max_length=32)


class FindingTriageRequest(BaseModel):
    status: str

    def validate_status(self) -> str:
        if self.status not in ALL_FINDING_STATUSES:
            raise ValueError(f"status must be one of {ALL_FINDING_STATUSES}")
        return self.status


class CheckSummary(BaseModel):
    id: int
    batch_no: str
    status: str
    scope: str
    consistency_score: int
    conflict_count: int
    high_count: int
    metrics_checked: int
    versions_checked: int
