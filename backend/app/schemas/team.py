from pydantic import BaseModel


class TeamOut(BaseModel):
    id: int
    code: str
    name: str
    domain: str
    domain_label: str
    lead_name: str
    member_count: int
    sla_hours: int
    metric_count: int = 0
