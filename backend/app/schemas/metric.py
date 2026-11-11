from pydantic import BaseModel, Field, field_validator

from app.constants.domains import ALL_DOMAINS
from app.constants.metric_status import ALL_METRIC_STATUSES


class MetricCreate(BaseModel):
    metric_key: str = Field(min_length=2, max_length=80, pattern=r"^[a-z][a-z0-9_]{1,79}$")
    display_name: str = Field(min_length=1, max_length=120)
    domain: str
    owner_team_id: int
    status: str = "draft"
    description: str | None = None
    consumers: list[str] = Field(default_factory=list)

    @field_validator("domain")
    @classmethod
    def check_domain(cls, value: str) -> str:
        if value not in ALL_DOMAINS:
            raise ValueError(f"domain must be one of {ALL_DOMAINS}")
        return value

    @field_validator("status")
    @classmethod
    def check_status(cls, value: str) -> str:
        if value not in ALL_METRIC_STATUSES:
            raise ValueError(f"status must be one of {ALL_METRIC_STATUSES}")
        return value


class MetricUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=120)
    status: str | None = None
    description: str | None = None
    consumers: list[str] | None = None
    owner_team_id: int | None = None

    @field_validator("status")
    @classmethod
    def check_status(cls, value: str | None) -> str | None:
        if value is not None and value not in ALL_METRIC_STATUSES:
            raise ValueError(f"status must be one of {ALL_METRIC_STATUSES}")
        return value


class VersionCreate(BaseModel):
    dsl_text: str = Field(min_length=10, max_length=4000)
    team_id: int | None = None
    effective_from: str | None = None
    set_current: bool = True


class VersionUpdate(BaseModel):
    dsl_text: str = Field(min_length=10, max_length=4000)


class DslParseRequest(BaseModel):
    dsl_text: str = Field(min_length=1, max_length=4000)
    metric_id: int | None = None
