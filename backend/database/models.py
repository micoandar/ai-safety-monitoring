from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.database import Base


class Detection(Base):
    __tablename__ = "detections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    total_person: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    compliant_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    violation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    compliance_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    overall_status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    objects: Mapped[list["DetectionObject"]] = relationship(
        "DetectionObject",
        back_populates="detection",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return (
            f"<Detection id={self.id} status={self.overall_status} "
            f"persons={self.total_person} violations={self.violation_count}>"
        )


class DetectionObject(Base):
    __tablename__ = "detection_objects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    detection_id: Mapped[int] = mapped_column(
        ForeignKey("detections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    class_name: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    x1: Mapped[float] = mapped_column(Float, nullable=False)
    y1: Mapped[float] = mapped_column(Float, nullable=False)
    x2: Mapped[float] = mapped_column(Float, nullable=False)
    y2: Mapped[float] = mapped_column(Float, nullable=False)

    detection: Mapped[Detection] = relationship(
        "Detection",
        back_populates="objects",
    )

    def __repr__(self) -> str:
        return (
            f"<DetectionObject id={self.id} class={self.class_name} "
            f"conf={self.confidence:.2f}>"
        )