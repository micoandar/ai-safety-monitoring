from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RecentDetection(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    detected_at: datetime
    total_person: int
    compliant_count: int
    violation_count: int
    compliance_rate: float
    overall_status: str


class TrendPoint(BaseModel):
    date: str          # "YYYY-MM-DD"
    label: str         # "01 Oct" (untuk label chart)
    total: int
    violations: int


class DashboardStats(BaseModel):
    total_detections: int
    total_workers: int
    total_compliant: int
    total_violations: int
    compliance_rate: float
    recent: list[RecentDetection]
    trend: list[TrendPoint]