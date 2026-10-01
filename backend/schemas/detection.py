from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BBox(BaseModel):
    x1: float = Field(..., description="Koordinat kiri-atas (x)")
    y1: float = Field(..., description="Koordinat kiri-atas (y)")
    x2: float = Field(..., description="Koordinat kanan-bawah (x)")
    y2: float = Field(..., description="Koordinat kanan-bawah (y)")


class DetectionObject(BaseModel):
    class_id: int = Field(..., description="ID class dari model")
    class_name: str = Field(
        ...,
        description="Nama class (helmet, no-helmet, no-vest, person, vest)",
    )
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: BBox


class ImageMeta(BaseModel):
    width: int
    height: int
    filename: str | None = None


class DetectionSummary(BaseModel):
    total_objects: int
    total_person: int
    counts_by_class: dict[str, int]


class SafetyAnalysis(BaseModel):
    total_person: int
    compliant_count: int
    violation_count: int
    compliance_rate: float = Field(..., ge=0.0, le=100.0)
    overall_status: str
    violation_types: list[str] = Field(default_factory=list)


class DetectionResponse(BaseModel):
    success: bool = True
    id: int | None = Field(None, description="ID record deteksi di database")
    image: ImageMeta
    detections: list[DetectionObject]
    summary: DetectionSummary
    safety: SafetyAnalysis
    inference_time_ms: float


# ============================================================
# Schemas untuk history & detail (Phase 3)
# ============================================================


class DetectionObjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    class_name: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float


class DetectionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    detected_at: datetime
    total_person: int
    compliant_count: int
    violation_count: int
    compliance_rate: float
    overall_status: str


class DetectionDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    detected_at: datetime
    total_person: int
    compliant_count: int
    violation_count: int
    compliance_rate: float
    overall_status: str
    objects: list[DetectionObjectRead]


class PaginatedDetections(BaseModel):
    total: int = Field(..., description="Total record di database")
    page: int
    page_size: int
    total_pages: int
    items: list[DetectionListItem]
    
class FrameDetectionResponse(BaseModel):
    success: bool = True
    detections: list[DetectionObject]
    summary: DetectionSummary
    safety: SafetyAnalysis
    inference_time_ms: float