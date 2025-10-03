"""
Security utilities for PII redaction and validation
"""

import re
from typing import List, Dict, Any
from app.core.config import settings

class PIIRedactor:
    """Handles PII redaction for documents"""
    
    # Email patterns
    EMAIL_PATTERNS = [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        r'\b[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9.-]+\s*\.\s*[A-Z|a-z]{2,}\b'
    ]
    
    # Phone patterns (US format)
    PHONE_PATTERNS = [
        r'\b\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
        r'\b[0-9]{3}[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
        r'\b\+?1[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'
    ]
    
    # SSN patterns (if present)
    SSN_PATTERNS = [
        r'\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b',
        r'\b[0-9]{9}\b'
    ]
    
    @classmethod
    def redact_text(cls, text: str) -> str:
        """Redact PII from text"""
        redacted = text
        
        # Redact emails
        for pattern in cls.EMAIL_PATTERNS:
            redacted = re.sub(pattern, '[EMAIL_REDACTED]', redacted, flags=re.IGNORECASE)
        
        # Redact phone numbers
        for pattern in cls.PHONE_PATTERNS:
            redacted = re.sub(pattern, '[PHONE_REDACTED]', redacted)
        
        # Redact SSNs
        for pattern in cls.SSN_PATTERNS:
            redacted = re.sub(pattern, '[SSN_REDACTED]', redacted)
        
        return redacted
    
    @classmethod
    def extract_pii(cls, text: str) -> Dict[str, List[str]]:
        """Extract PII for analysis (before redaction)"""
        pii = {
            'emails': [],
            'phones': [],
            'ssns': []
        }
        
        # Extract emails
        for pattern in cls.EMAIL_PATTERNS:
            matches = re.findall(pattern, text, flags=re.IGNORECASE)
            pii['emails'].extend(matches)
        
        # Extract phones
        for pattern in cls.PHONE_PATTERNS:
            matches = re.findall(pattern, text)
            pii['phones'].extend(matches)
        
        # Extract SSNs
        for pattern in cls.SSN_PATTERNS:
            matches = re.findall(pattern, text)
            pii['ssns'].extend(matches)
        
        # Remove duplicates
        for key in pii:
            pii[key] = list(set(pii[key]))
        
        return pii

class InputValidator:
    """Validates input documents and requests"""
    
    @classmethod
    def validate_document_size(cls, text: str) -> bool:
        """Check if document size is within limits"""
        size_mb = len(text.encode('utf-8')) / (1024 * 1024)
        return size_mb <= settings.MAX_DOCUMENT_SIZE_MB
    
    @classmethod
    def validate_document_count(cls, documents: List[Dict[str, Any]]) -> bool:
        """Check if number of documents is within limits"""
        return len(documents) <= settings.MAX_DOCUMENTS_PER_REQUEST
    
    @classmethod
    def validate_document_content(cls, document: Dict[str, Any]) -> List[str]:
        """Validate document content and return any issues"""
        issues = []
        
        # Check required fields
        if 'name' not in document or not document['name'].strip():
            issues.append("Document name is required")
        
        if 'text' not in document or not document['text'].strip():
            issues.append("Document text is required")
        
        # Check size
        if not cls.validate_document_size(document.get('text', '')):
            issues.append(f"Document size exceeds {settings.MAX_DOCUMENT_SIZE_MB}MB limit")
        
        return issues