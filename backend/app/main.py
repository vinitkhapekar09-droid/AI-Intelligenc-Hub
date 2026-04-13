from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.exc import SQLAlchemyError

from .api.routes import router
from .core.database import Base, engine

app = FastAPI(title="Daily AI Digest", version="1.0.0")

app.include_router(router)


@app.on_event("startup")
def init_database() -> None:
    """Create tables if DB is reachable; keep API booting in local dev otherwise."""
    try:
        Base.metadata.create_all(bind=engine)
        print("[startup] Database schema ready.")
    except SQLAlchemyError as e:
        print(f"[startup] Database unavailable, continuing without schema init: {e}")


# Expose /metrics endpoint for Prometheus to scrape
Instrumentator().instrument(app).expose(app)
