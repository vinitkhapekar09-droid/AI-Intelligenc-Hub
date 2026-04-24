from datetime import datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text

from ..core.database import Base


class ContentItem(Base):
    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("daily_issues.id"), nullable=False, index=True)
    issue_date = Column(Date, nullable=False, index=True)
    rank = Column(Integer, nullable=False, default=0)
    doc_id = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    why_it_matters = Column(Text, nullable=True)
    source = Column(String, nullable=False)
    doc_type = Column(String, nullable=False, index=True)
    url = Column(String, nullable=True)
    published_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
