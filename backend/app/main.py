from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.exc import SQLAlchemyError
from .api.routes import router
from .core.config import settings
from .core.database import Base, engine
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from .core.limiter import limiter


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize schema in local/dev flows when explicitly enabled."""
    if not settings.AUTO_CREATE_SCHEMA:
        print("[startup] AUTO_CREATE_SCHEMA disabled; skipping schema creation.")
        yield
        return

    try:
        Base.metadata.create_all(bind=engine)
        print("[startup] Database schema ready.")
    except SQLAlchemyError as e:
        print(f"[startup] Database unavailable, continuing without schema init: {e}")
    yield


app = FastAPI(title="AI Intelligence Hub", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# WHY CORS middleware?
# Frontend runs on a different port/domain than FastAPI.
# Without this, browsers block requests between them.
# In production, replace "*" with your actual domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


# Expose /metrics endpoint for Prometheus to scrape
Instrumentator().instrument(app).expose(app)
