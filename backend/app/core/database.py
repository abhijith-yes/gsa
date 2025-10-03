"""
Database configuration and models
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.core.config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

class DocumentRequest(Base):
    """Model for document ingestion requests"""
    __tablename__ = "document_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")  # pending, processed, error
    
    # Document summaries
    doc_summaries = Column(JSON)  # List of document summaries
    
    # Analysis results (when available)
    parsed_fields = Column(JSON)
    checklist = Column(JSON)
    brief = Column(Text)
    client_email = Column(Text)
    citations = Column(JSON)

class RedactedDocument(Base):
    """Model for storing redacted documents"""
    __tablename__ = "redacted_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, index=True)
    name = Column(String)
    original_text = Column(Text)  # Store original for reference (should be redacted)
    redacted_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    document_type = Column(String)  # profile, past_performance, pricing, unknown
    word_count = Column(Integer)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
