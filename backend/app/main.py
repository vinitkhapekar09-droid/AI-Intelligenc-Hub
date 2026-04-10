from fastapi import FastAPI
from .api.routes import router
from .core.database import Base, engine
from .models import subscriber  # Ensure models are imported for table creation

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Daily AI Digest", version="1.0.0")

app.include_router(router)
