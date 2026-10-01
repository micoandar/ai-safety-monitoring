import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database.database import init_db
from middleware.rate_limit import RateLimitMiddleware
from middleware.security_headers import SecurityHeadersMiddleware
from routers import dashboard, detection
from services.detector import detector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    logger.info(
        "Config: DEBUG=%s | RATE_LIMIT=%s | TRUST_PROXY=%s",
        settings.DEBUG,
        settings.RATE_LIMIT_ENABLED,
        settings.TRUST_PROXY_HEADERS,
    )

    try:
        init_db()
        logger.info("Database initialized.")
    except Exception as exc:
        logger.error("Gagal inisialisasi database: %s", exc)

    try:
        detector.load()
    except Exception as exc:
        logger.error("Gagal memuat model YOLO: %s", exc)

    yield
    logger.info("Shutting down %s", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Backend API untuk deteksi PPE (helmet, no-helmet, vest, no-vest, person) "
        "menggunakan YOLO11."
    ),
    lifespan=lifespan,
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)

app.include_router(detection.router)
app.include_router(dashboard.router)


@app.get("/", tags=["Root"])
def root() -> dict:
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health() -> dict:
    return {
        "status": "ok",
        "model_loaded": detector.is_loaded,
        "model_path": settings.MODEL_PATH,
    }