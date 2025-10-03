from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Union

from app.core.database import get_db, DocumentRequest, RedactedDocument
from app.services.openai_service import GSAAssistantService

router = APIRouter()

class AnalyzeRequest(BaseModel):
    request_id: str = Field(..., description="Request ID from ingestion")

class ComplianceProblem(BaseModel):
    code: str = Field(..., description="Problem code")
    rule_id: str = Field(..., description="GSA rule ID (R1-R5)")
    evidence: str = Field(..., description="Evidence of the problem")

class ComplianceChecklist(BaseModel):
    required_ok: bool = Field(..., description="Whether basic requirements are met")
    problems: List[ComplianceProblem] = Field(default=[], description="List of compliance problems")

class ParsedFields(BaseModel):
    uei: Optional[str] = None
    duns: Optional[str] = None
    naics: List[str] = Field(default=[])
    sam_status: Optional[str] = None
    poc_email: Optional[str] = None
    poc_phone: Optional[str] = None
    entity_name: Optional[str] = None
    past_performance: List[Dict[str, Any]] = Field(default=[])
    pricing: Union[Dict[str, Any], List[Dict[str, Any]]] = Field(default={})

class RuleCitation(BaseModel):
    rule_id: str = Field(..., description="Rule ID (R1-R5)")
    chunk: str = Field(..., description="Relevant rule text")

class AnalyzeResponse(BaseModel):
    parsed: ParsedFields
    checklist: ComplianceChecklist
    brief: str
    client_email: str
    citations: List[RuleCitation]
    request_id: str
    status: str = "completed"

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_documents(
    request: AnalyzeRequest,
    db: Session = Depends(get_db)
):
    
    # Find the document request
    doc_request = db.query(DocumentRequest).filter(
        DocumentRequest.request_id == request.request_id
    ).first()
    
    if not doc_request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if doc_request.status == "error":
        raise HTTPException(status_code=400, detail="Previous ingestion had errors")
    
    # Get the redacted documents
    redacted_docs = db.query(RedactedDocument).filter(
        RedactedDocument.request_id == request.request_id
    ).all()
    
    if not redacted_docs:
        raise HTTPException(status_code=404, detail="No documents found for this request")
    
    # Prepare documents for analysis (use original text for better field extraction)
    documents = []
    for doc in redacted_docs:
        documents.append({
            "name": doc.name,
            "text": doc.original_text
        })
    
    # Initialize OpenAI service
    try:
        openai_service = GSAAssistantService()
        
        # Analyze documents
        analysis_result = openai_service.analyze_documents(request.request_id, documents)
        
        if "error" in analysis_result:
            # Update request status
            doc_request.status = "error"
            db.commit()
            raise HTTPException(status_code=500, detail=analysis_result["error"])
        
        # Update request with analysis results
        doc_request.status = "processed"
        doc_request.parsed_fields = analysis_result.get("parsed", {})
        doc_request.checklist = analysis_result.get("checklist", {})
        doc_request.brief = analysis_result.get("brief", "")
        doc_request.client_email = analysis_result.get("client_email", "")
        doc_request.citations = analysis_result.get("citations", [])
        
        db.commit()
        
        # Return structured response
        return AnalyzeResponse(
            parsed=ParsedFields(**analysis_result.get("parsed", {})),
            checklist=ComplianceChecklist(**analysis_result.get("checklist", {})),
            brief=analysis_result.get("brief", ""),
            client_email=analysis_result.get("client_email", ""),
            citations=[RuleCitation(**citation) for citation in analysis_result.get("citations", [])],
            request_id=request.request_id,
            status="completed"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        # Update request status
        doc_request.status = "error"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/analyze/{request_id}")
async def get_analysis_results(
    request_id: str,
    db: Session = Depends(get_db)
):
    """Get analysis results for a completed request"""
    
    doc_request = db.query(DocumentRequest).filter(
        DocumentRequest.request_id == request_id
    ).first()
    
    if not doc_request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if doc_request.status != "processed":
        return {
            "request_id": request_id,
            "status": doc_request.status,
            "message": "Analysis not yet completed"
        }
    
    return AnalyzeResponse(
        parsed=ParsedFields(**doc_request.parsed_fields or {}),
        checklist=ComplianceChecklist(**doc_request.checklist or {}),
        brief=doc_request.brief or "",
        client_email=doc_request.client_email or "",
        citations=[RuleCitation(**citation) for citation in doc_request.citations or []],
        request_id=request_id,
        status="completed"
    )
