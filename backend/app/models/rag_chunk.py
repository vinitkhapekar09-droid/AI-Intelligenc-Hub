from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Integer, JSON, String, Text

from ..core.database import Base


class RagChunk(Base):
    __tablename__ = "rag_chunks"

    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(String, unique=True, nullable=False, index=True)
    doc_id = Column(String, nullable=False, index=True)
    issue_date = Column(Date, nullable=False, index=True)
    doc_type = Column(String, nullable=False, index=True)
    source = Column(String, nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
