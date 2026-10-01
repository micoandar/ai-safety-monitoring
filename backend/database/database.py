from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import get_settings

settings = get_settings()

if not settings.DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL belum diset. Isi file .env (lihat .env.example)."
    )

# pool_pre_ping → deteksi koneksi mati sebelum query (penting untuk MySQL cloud)
# pool_recycle → recycle koneksi lama (>5 menit) agar tidak di-drop server
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: satu session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Buat tabel bila belum ada. Untuk production sebaiknya pakai Alembic."""
    from database import models  # noqa: F401  (pastikan model ter-register)

    Base.metadata.create_all(bind=engine)