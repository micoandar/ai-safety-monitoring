import logging
import math

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from config import get_settings
from database.database import get_db
from database.models import Detection, DetectionObject as DetectionObjectModel
from schemas.detection import (
    BBox,
    DetectionDetail,
    DetectionListItem,
    DetectionObject,
    DetectionResponse,
    DetectionSummary,
    FrameDetectionResponse,
    ImageMeta,
    PaginatedDetections,
    SafetyAnalysis,
)
from services import safety_analyzer
from services.detector import DetectorError, decode_image, detector

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/detection", tags=["Detection"])
settings = get_settings()

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/bmp",
}


def _persist_detection(
    db: Session,
    safety_result,
    detections: list[dict],
) -> Detection:
    """Simpan hasil deteksi + objek ke MySQL."""
    record = Detection(
        total_person=safety_result.total_person,
        compliant_count=safety_result.compliant_count,
        violation_count=safety_result.violation_count,
        compliance_rate=safety_result.compliance_rate,
        overall_status=safety_result.overall_status,
    )
    db.add(record)
    db.flush()

    for d in detections:
        db.add(
            DetectionObjectModel(
                detection_id=record.id,
                class_name=d["class_name"],
                confidence=d["confidence"],
                x1=d["bbox"]["x1"],
                y1=d["bbox"]["y1"],
                x2=d["bbox"]["x2"],
                y2=d["bbox"]["y2"],
            )
        )

    db.commit()
    db.refresh(record)
    return record


@router.post(
    "/image",
    response_model=DetectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Deteksi PPE pada gambar yang di-upload",
)
async def detect_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> DetectionResponse:
    # 1. Validasi tipe file
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Format file tidak didukung: {file.content_type}",
        )

    # 2. Baca file & validasi ukuran
    raw = await file.read()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File kosong.",
        )
    if len(raw) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Ukuran file melebihi batas {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )

    # 3. Decode image
    image = decode_image(raw)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File gambar tidak valid atau rusak.",
        )

    # 4. Inference
    try:
        result = detector.predict(image)
    except DetectorError as exc:
        logger.error("Detector error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    # 5. Summary
    counts: dict[str, int] = {}
    for det in result["detections"]:
        counts[det["class_name"]] = counts.get(det["class_name"], 0) + 1

    # 6. Safety analysis
    safety_result = safety_analyzer.analyze(result["detections"])

    # 7. Persist ke DB
    try:
        record = _persist_detection(db, safety_result, result["detections"])
    except Exception as exc:
        logger.error("Gagal menyimpan deteksi ke DB: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gagal menyimpan hasil deteksi ke database.",
        )

    return DetectionResponse(
        success=True,
        id=record.id,
        image=ImageMeta(
            width=result["width"],
            height=result["height"],
            filename=file.filename,
        ),
        detections=[
            DetectionObject(
                class_id=d["class_id"],
                class_name=d["class_name"],
                confidence=d["confidence"],
                bbox=BBox(**d["bbox"]),
            )
            for d in result["detections"]
        ],
        summary=DetectionSummary(
            total_objects=len(result["detections"]),
            total_person=counts.get("person", 0),
            counts_by_class=counts,
        ),
        safety=SafetyAnalysis(**safety_result.to_dict()),
        inference_time_ms=result["inference_time_ms"],
    )


@router.post(
    "/frame",
    response_model=FrameDetectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Deteksi PPE pada frame webcam (tidak disimpan ke database)",
)
async def detect_frame(file: UploadFile = File(...)) -> FrameDetectionResponse:
    # 1. Validasi tipe file
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Format file tidak didukung: {file.content_type}",
        )

    # 2. Baca file & validasi ukuran
    raw = await file.read()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Frame kosong.",
        )
    if len(raw) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Frame melebihi batas {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )

    # 3. Decode image
    image = decode_image(raw)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Frame tidak valid atau rusak.",
        )

    # 4. Inference
    try:
        result = detector.predict(image)
    except DetectorError as exc:
        logger.error("Detector error (frame): %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    # 5. Summary
    counts: dict[str, int] = {}
    for det in result["detections"]:
        counts[det["class_name"]] = counts.get(det["class_name"], 0) + 1

    # 6. Safety analysis
    safety_result = safety_analyzer.analyze(result["detections"])

    # TIDAK disimpan ke database (spec: webcam tidak persist setiap frame)
    return FrameDetectionResponse(
        success=True,
        detections=[
            DetectionObject(
                class_id=d["class_id"],
                class_name=d["class_name"],
                confidence=d["confidence"],
                bbox=BBox(**d["bbox"]),
            )
            for d in result["detections"]
        ],
        summary=DetectionSummary(
            total_objects=len(result["detections"]),
            total_person=counts.get("person", 0),
            counts_by_class=counts,
        ),
        safety=SafetyAnalysis(**safety_result.to_dict()),
        inference_time_ms=result["inference_time_ms"],
    )


@router.get(
    "/history",
    response_model=PaginatedDetections,
    summary="Riwayat deteksi (paginasi)",
)
def get_history(
    page: int = Query(1, ge=1, description="Halaman (mulai dari 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Jumlah item per halaman"),
    db: Session = Depends(get_db),
) -> PaginatedDetections:
    total = db.scalar(select(func.count()).select_from(Detection)) or 0

    stmt = (
        select(Detection)
        .order_by(Detection.detected_at.desc(), Detection.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = db.scalars(stmt).all()

    total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 0

    return PaginatedDetections(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=[DetectionListItem.model_validate(r) for r in rows],
    )


@router.get(
    "/{detection_id}",
    response_model=DetectionDetail,
    summary="Detail satu deteksi",
)
def get_detection_detail(
    detection_id: int,
    db: Session = Depends(get_db),
) -> DetectionDetail:
    stmt = (
        select(Detection)
        .options(selectinload(Detection.objects))
        .where(Detection.id == detection_id)
    )
    record = db.scalars(stmt).first()
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deteksi dengan id {detection_id} tidak ditemukan.",
        )
    return DetectionDetail.model_validate(record)


@router.delete(
    "/{detection_id}",
    status_code=status.HTTP_200_OK,
    summary="Hapus satu deteksi",
)
def delete_detection(
    detection_id: int,
    db: Session = Depends(get_db),
) -> dict:
    record = db.get(Detection, detection_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deteksi dengan id {detection_id} tidak ditemukan.",
        )
    db.delete(record)
    db.commit()
    return {"success": True, "message": f"Deteksi id {detection_id} dihapus."}