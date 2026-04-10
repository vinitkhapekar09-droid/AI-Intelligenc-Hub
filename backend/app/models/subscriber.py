from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime, timezone
from ..core.database import Base


class Subscriber(Base):
    __tablename__ = "subscribers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    subscribed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
