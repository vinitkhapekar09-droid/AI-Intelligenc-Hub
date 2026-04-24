from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Integer, String, Text

from ..core.database import Base


class DailyIssue(Base):
    __tablename__ = "daily_issues"

    id = Column(Integer, primary_key=True, index=True)
    issue_date = Column(Date, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="published")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    published_at = Column(DateTime, default=datetime.utcnow, nullable=False)
