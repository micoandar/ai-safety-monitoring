from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Detection
from schemas.dashboard import DashboardStats, RecentDetection, TrendPoint

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get(
    "/stats",
    response_model=DashboardStats,
    summary="Statistik agregat dashboard",
)
def get_dashboard_stats(db: Session = Depends(get_db)) -> DashboardStats:
    # ----- Aggregate totals -----
    total_detections = db.scalar(select(func.count()).select_from(Detection)) or 0
    total_workers = (
        db.scalar(select(func.coalesce(func.sum(Detection.total_person), 0))) or 0
    )
    total_compliant = (
        db.scalar(select(func.coalesce(func.sum(Detection.compliant_count), 0))) or 0
    )
    total_violations = (
        db.scalar(select(func.coalesce(func.sum(Detection.violation_count), 0))) or 0
    )

    compliance_rate = 0.0
    if total_workers > 0:
        compliance_rate = round((total_compliant / total_workers) * 100, 2)

    # ----- Recent (5 terakhir) -----
    recent_stmt = (
        select(Detection)
        .order_by(Detection.detected_at.desc(), Detection.id.desc())
        .limit(5)
    )
    recent_rows = db.scalars(recent_stmt).all()

    # ----- Trend 7 hari terakhir -----
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=6)

    trend_stmt = (
        select(
            func.date(Detection.detected_at).label("day"),
            func.count().label("total"),
            func.coalesce(func.sum(Detection.violation_count), 0).label("violations"),
        )
        .where(func.date(Detection.detected_at) >= start_date)
        .group_by(func.date(Detection.detected_at))
        .order_by(func.date(Detection.detected_at))
    )
    rows = db.execute(trend_stmt).all()

    trend_map: dict[str, dict] = {}
    for r in rows:
        key = r.day.strftime("%Y-%m-%d") if hasattr(r.day, "strftime") else str(r.day)
        trend_map[key] = {"total": int(r.total), "violations": int(r.violations)}

    trend: list[TrendPoint] = []
    for i in range(7):
        day = start_date + timedelta(days=i)
        key = day.strftime("%Y-%m-%d")
        entry = trend_map.get(key, {"total": 0, "violations": 0})
        trend.append(
            TrendPoint(
                date=key,
                label=day.strftime("%d %b"),
                total=entry["total"],
                violations=entry["violations"],
            )
        )

    return DashboardStats(
        total_detections=int(total_detections),
        total_workers=int(total_workers),
        total_compliant=int(total_compliant),
        total_violations=int(total_violations),
        compliance_rate=compliance_rate,
        recent=[RecentDetection.model_validate(r) for r in recent_rows],
        trend=trend,
    )