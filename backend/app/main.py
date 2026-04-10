from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from app.api.routes import router
from app.core.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Daily AI Digest", version="1.0.0")

app.include_router(router)

# Expose /metrics endpoint for Prometheus to scrape
Instrumentator().instrument(app).expose(app)
