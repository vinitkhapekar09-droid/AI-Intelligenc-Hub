from fastapi import FastAPI
from app.api.routes import router
from app.core.database import Base, engine
from app.models import subscriber  # Ensure models are imported for table creation

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Daily AI Digest", version="1.0.0")

app.include_router(router)
