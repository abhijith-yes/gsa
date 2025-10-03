"""
Document ingestion endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import uuid
from datetime import datetime

from app.core.database import get_db, DocumentRequest, RedactedDocument
from app.core.security import PIIRedactor, InputValidator
from app.core.config import settings

router = APIRouter()

class Document(BaseModel):
    """Document model for ingestion"""
    name: str = Field(..., description="Document name")
    text: str = Field(..., description="Document text content")

class IngestRequest(BaseModel):
    """Request model for document ingestion"""
    documents: List[Document] = Field(..., description="List of documents to ingest")

class DocumentSummary(BaseModel):
    """Summary of ingested document"""
    name: str
    status: str
    redacted_preview: str
    word_count: int
    pii_found: Dict[str, List[str]]

class IngestResponse(BaseModel):
    """Response model for document ingestion"""
    doc_summaries: List[DocumentSummary]
    request_id: str
    total_documents: int
    total_word_count: int

@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents(
    request: IngestRequest,
    db: Session = Depends(get_db)
):
    """
    Ingest documents for analysis.
    
    - **documents**: List of documents with name and text content
    - Returns request_id for subsequent analysis
    """
    
    # Validate input
    if not request.documents:
        raise HTTPException(status_code=400, detail="No documents provided")
    
    if not InputValidator.validate_document_count(request.documents):
        raise HTTPException(
            status_code=400, 
            detail=f"Too many documents. Maximum {settings.MAX_DOCUMENTS_PER_REQUEST} allowed"
        )
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    
    # Process documents
    doc_summaries = []
    total_word_count = 0
    
    for doc in request.documents:
        # Validate document
        issues = InputValidator.validate_document_content(doc.dict())
        if issues:
            doc_summaries.append(DocumentSummary(
                name=doc.name,
                status="error",
                redacted_preview="",
                word_count=0,
                pii_found={}
            ))
            continue
        
        # Extract PII before redaction
        pii_found = PIIRedactor.extract_pii(doc.text)
        
        # Redact PII
        redacted_text = PIIRedactor.redact_text(doc.text)
        
        # Create preview (first 200 chars)
        preview = redacted_text[:200] + "..." if len(redacted_text) > 200 else redacted_text
        
        # Count words
        word_count = len(redacted_text.split())
        total_word_count += word_count
        
        # Store in database
        redacted_doc = RedactedDocument(
            request_id=request_id,
            name=doc.name,
            original_text=doc.text,  # Store original for reference
            redacted_text=redacted_text,
            word_count=word_count
        )
        db.add(redacted_doc)
        
        doc_summaries.append(DocumentSummary(
            name=doc.name,
            status="stored",
            redacted_preview=preview,
            word_count=word_count,
            pii_found=pii_found
        ))
    
    # Create document request record
    doc_request = DocumentRequest(
        request_id=request_id,
        status="pending",
        doc_summaries=[summary.dict() for summary in doc_summaries]
    )
    db.add(doc_request)
    
    # Commit to database
    db.commit()
    
    return IngestResponse(
        doc_summaries=doc_summaries,
        request_id=request_id,
        total_documents=len(request.documents),
        total_word_count=total_word_count
    )
