from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.exc import SQLAlchemyError
from .api.routes import router
from .core.database import Base, engine
from .models.user import User
from .models.subscriber import Subscriber
from .models.conversation import Conversation


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create tables if DB is reachable; keep API booting in local dev otherwise."""
    try:
        Base.metadata.create_all(bind=engine)
        print("[startup] Database schema ready.")
    except SQLAlchemyError as e:
        print(f"[startup] Database unavailable, continuing without schema init: {e}")
    yield


app = FastAPI(title="Daily AI Digest", version="1.0.0", lifespan=lifespan)

# WHY CORS middleware?
# Frontend runs on a different port/domain than FastAPI.
# Without this, browsers block requests between them.
# In production, replace "*" with your actual domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


# Expose /metrics endpoint for Prometheus to scrape
Instrumentator().instrument(app).expose(app)
