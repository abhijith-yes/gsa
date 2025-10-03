from openai import OpenAI
from typing import Dict, List, Any, Optional
import json
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class GSAAssistantService:
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.assistant_id = settings.OPENAI_ASSISTANT_ID
        
        # If no assistant ID provided, create one
        if not self.assistant_id:
            self.assistant_id = self._create_assistant()
    
    def _make_assistant_call(self, method_name, *args, **kwargs):
        extra_headers = kwargs.get('extra_headers', {})
        extra_headers['OpenAI-Beta'] = 'assistants=v2'
        kwargs['extra_headers'] = extra_headers
        
        method = getattr(self.client.beta.assistants, method_name)
        return method(*args, **kwargs)
    
    def _create_assistant(self) -> str:
        instructions = """
You are a GSA compliance assistant specialized in onboarding document review.

Your tasks:
1. Classify documents into: profile, past_performance, pricing, unknown
2. Extract key fields: UEI, DUNS, NAICS codes, SAM status, POC info, pricing data
3. Apply GSA Rules Pack (R1-R5) using retrieval-augmented generation
4. Generate compliance checklist with rule citations
5. Write negotiation preparation brief
6. Draft polite client email with missing items

Rules:
- If confidence < 70% for any classification or extraction, return "IDK/needs human"
- Always cite specific rule IDs (R1, R2, R3, R4, R5) in your analysis
- Be professional and constructive in feedback
- Focus on actionable items for clients

Response format: JSON with fields:
- parsed: extracted fields
- checklist: compliance status with problems array
- brief: negotiation preparation text
- client_email: client communication draft
- citations: rule citations with chunks
"""
        
        # Create the assistant
        assistant = self._make_assistant_call(
            "create",
            name="GetGSA Assistant",
            instructions=instructions,
            model="gpt-4-1106-preview",
            tools=[{"type": "retrieval"}],
            response_format={"type": "json_object"}
        )
        
        logger.info(f"Created GSA assistant with ID: {assistant.id}")
        return assistant.id
    
    def _load_rules_pack(self) -> Optional[str]:
        
        rules_content = """
R1 – Identity & Registry Requirements:
- Required: UEI (12 characters, alphanumeric)
- Required: DUNS number (9 digits)
- SAM.gov registration must be active
- Entity name must match SAM registration

R2 – NAICS & SIN Mapping:
- 541511 (Custom Computer Programming Services) → SIN 54151S
- 541512 (Computer Systems Design Services) → SIN 54151S  
- 541513 (Computer Facilities Management Services) → SIN 54151S
- 541519 (Other Computer Related Services) → SIN 54151S
- All NAICS codes must map to valid SINs

R3 – Past Performance Requirements:
- At least 1 past performance project ≥ $25,000 within 36 months
- Must be relevant to proposed NAICS codes
- Include project title, client, value, duration, and scope
- Past performance must demonstrate technical capability

R4 – Pricing & Catalog Requirements:
- Provide labor categories with rates
- Include labor hour estimates
- Show total project value
- Pricing must be competitive and realistic
- Include any discounts or special rates

R5 – Submission Hygiene:
- All PII must be redacted (emails, phones, SSNs)
- Documents must be clearly labeled
- File formats must be supported (PDF, DOC, TXT)
- No password-protected files
- Maximum file size limits apply
"""
        
        # Create a temporary file for the rules
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(rules_content)
            temp_file = f.name
        
        # Upload to OpenAI
        with open(temp_file, 'rb') as f:
            file_response = self.client.files.create(
                file=f,
                purpose='assistants'
            )
        
        # Clean up temp file
        import os
        os.unlink(temp_file)
        
        return file_response.id
    
    def analyze_documents(self, request_id: str, documents: List[Dict[str, str]]) -> Dict[str, Any]:
        
        # Check if we have a valid API key
        logger.info(f"API Key check: {settings.OPENAI_API_KEY[:10]}...")
        if settings.OPENAI_API_KEY == "dummy-key-for-development":
            logger.info("Using mock analysis due to dummy API key")
            return self._get_mock_analysis_result(request_id, documents)
        
        # Try GPT-based analysis first
        try:
            return self._get_gpt_analysis_result(request_id, documents)
        except Exception as e:
            logger.error(f"GPT analysis failed: {e}")
            logger.info("Falling back to mock analysis")
            return self._get_mock_analysis_result(request_id, documents)
    
    def _get_gpt_analysis_result(self, request_id: str, documents: List[Dict[str, str]]) -> Dict[str, Any]:
        
        # Prepare documents for analysis
        doc_texts = []
        for doc in documents:
            doc_texts.append(f"Document: {doc['name']}\n{doc['text']}\n")
        
        analysis_prompt = f"""
You are a GSA compliance expert analyzing onboarding documents. Extract and analyze the following information with high precision:

DOCUMENTS TO ANALYZE:
{chr(10).join(doc_texts)}

CRITICAL EXTRACTION GUIDELINES:
- Look for emails in ANY format: "email@domain.com", "john@company.com", "Contact: user@example.org"
- Find phone numbers in formats: "(555) 123-4567", "555-123-4567", "555.123.4567", "+1-555-123-4567"
- Extract UEI as 12-character alphanumeric codes
- Extract DUNS as 9-digit numbers
- Find NAICS codes as 6-digit numbers
- Look for company names in headers, titles, or business information sections
- Extract past performance projects with values, clients, and durations
- Find pricing information in tables, lists, or structured data

Please provide a comprehensive analysis in the following JSON format:

{{
  "parsed": {{
    "uei": "extracted UEI (12 characters) or null if not found",
    "duns": "extracted DUNS (9 digits) or null if not found", 
    "naics": ["list", "of", "NAICS", "codes"],
    "sam_status": "active/inactive/pending/unknown",
    "poc_email": "primary contact email (extract actual email address) or null",
    "poc_phone": "primary contact phone (extract actual phone number) or null",
    "entity_name": "company/organization name or null",
    "past_performance": [
      {{
        "title": "project title",
        "client": "client name", 
        "value": numeric_value,
        "duration": "project duration",
        "scope": "project description"
      }}
    ],
    "pricing": [
      {{
        "labor_category": "job title",
        "rate": numeric_rate,
        "hours": numeric_hours,
        "unit": "Hour/Day/etc"
      }}
    ]
  }},
  "checklist": {{
    "required_ok": true/false,
    "problems": [
      {{
        "code": "problem_identifier",
        "rule_id": "R1/R2/R3/R4/R5",
        "evidence": "specific evidence from documents"
      }}
    ]
  }},
  "brief": "2-3 paragraph executive summary of findings, strengths, and recommendations",
  "client_email": "professional email draft to client with findings and next steps",
  "citations": [
    {{
      "rule_id": "R1/R2/R3/R4/R5",
      "chunk": "relevant rule text or evidence"
    }}
  ]
}}

GSA RULES TO APPLY:
R1 - Identity & Registry: UEI (12 chars), DUNS (9 digits), SAM active
R2 - NAICS & SIN Mapping: Valid NAICS codes mapped to SINs  
R3 - Past Performance: At least 1 project ≥ $25,000 within 36 months
R4 - Pricing: Labor categories, rates, realistic pricing
R5 - Submission Hygiene: PII redacted, proper formatting

IMPORTANT: Extract ACTUAL email addresses and phone numbers from the text. Do not return "Not found" unless you've thoroughly searched all document content. Look for contact information in headers, footers, signature blocks, and contact sections.
"""
        
        try:
            # Use direct GPT-4 API call for better control
            response = self.client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {"role": "system", "content": "You are a GSA compliance expert. Always respond with valid JSON only."},
                    {"role": "user", "content": analysis_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            response_content = response.choices[0].message.content
            
            # Parse JSON response
            try:
                analysis_result = json.loads(response_content)
                logger.info("GPT analysis completed successfully")
                return analysis_result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse GPT response as JSON: {e}")
                logger.error(f"Response content: {response_content}")
                raise Exception("Invalid JSON response from GPT")
                
        except Exception as e:
            logger.error(f"GPT API call failed: {e}")
            raise e
    
    def _get_mock_analysis_result(self, request_id: str, documents: List[Dict[str, str]]) -> Dict[str, Any]:
        
        # Extract basic info from documents
        all_text = " ".join([doc.get('text', '') for doc in documents])
        
        # Simple field extraction for mock analysis
        import re
        
        # Extract UEI
        uei_match = re.search(r'UEI[:\s]*([A-Z0-9]{12})', all_text, re.IGNORECASE)
        uei = uei_match.group(1) if uei_match else None
        
        # Extract DUNS
        duns_match = re.search(r'DUNS[:\s]*(\d{9})', all_text, re.IGNORECASE)
        duns = duns_match.group(1) if duns_match else None
        
        # Extract NAICS codes
        naics_matches = re.findall(r'NAICS[:\s]*([0-9, ]+)', all_text, re.IGNORECASE)
        naics = []
        if naics_matches:
            naics_text = naics_matches[0]
            naics = [code.strip() for code in re.findall(r'\d{6}', naics_text)]
        
        # Extract SAM status
        sam_match = re.search(r'SAM[:\s]*Status[:\s]*([A-Za-z]+)', all_text, re.IGNORECASE)
        sam_status = sam_match.group(1).lower() if sam_match else "unknown"
        
        # Extract POC email
        poc_email_match = re.search(r'POC[:\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', all_text, re.IGNORECASE)
        poc_email = poc_email_match.group(1) if poc_email_match else None
        
        # Extract POC phone
        poc_phone_match = re.search(r'POC[:\s]*\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})', all_text)
        poc_phone = f"({poc_phone_match.group(1)}) {poc_phone_match.group(2)}-{poc_phone_match.group(3)}" if poc_phone_match else None
        
        # Extract entity name
        entity_name = None
        for doc in documents:
            if doc.get('name', '').lower() in ['profile', 'company profile', 'company']:
                lines = doc.get('text', '').split('\n')
                for line in lines[:3]:  # Check first 3 lines
                    if line.strip() and not any(keyword in line.lower() for keyword in ['uei', 'duns', 'naics']):
                        entity_name = line.strip()
                        break
        
        # Mock field extraction
        parsed_fields = {
            "uei": uei,
            "duns": duns,
            "naics": naics,
            "sam_status": sam_status,
            "poc_email": poc_email,
            "poc_phone": poc_phone,
            "entity_name": entity_name,
            "past_performance": [
                {
                    "title": "Sample Project Alpha",
                    "client": "Sample Client Corp",
                    "value": 75000,
                    "duration": "8 months",
                    "scope": "Custom software development and system integration"
                }
            ],
            "pricing": [
                {
                    "labor_category": "Senior Software Engineer",
                    "rate": 125.00,
                    "hours": 200,
                    "unit": "Hour"
                },
                {
                    "labor_category": "Project Manager",
                    "rate": 110.00,
                    "hours": 100,
                    "unit": "Hour"
                }
            ]
        }
        
        # Enhanced compliance checklist
        checklist = {
            "required_ok": True,
            "problems": []
        }
        
        # Check for common issues
        if not parsed_fields["uei"]:
            checklist["problems"].append({
                "code": "missing_uei",
                "rule_id": "R1",
                "evidence": "UEI not found in documents"
            })
            checklist["required_ok"] = False
        elif len(parsed_fields["uei"]) != 12:
            checklist["problems"].append({
                "code": "invalid_uei_format",
                "rule_id": "R1", 
                "evidence": f"UEI '{parsed_fields['uei']}' is not 12 characters"
            })
            checklist["required_ok"] = False
        
        if not parsed_fields["duns"]:
            checklist["problems"].append({
                "code": "missing_duns", 
                "rule_id": "R1",
                "evidence": "DUNS number not found in documents"
            })
            checklist["required_ok"] = False
        elif len(parsed_fields["duns"]) != 9:
            checklist["problems"].append({
                "code": "invalid_duns_format",
                "rule_id": "R1",
                "evidence": f"DUNS '{parsed_fields['duns']}' is not 9 digits"
            })
            checklist["required_ok"] = False
        
        if parsed_fields["sam_status"] not in ["active", "pending"]:
            checklist["problems"].append({
                "code": "sam_inactive",
                "rule_id": "R1",
                "evidence": f"SAM status is '{parsed_fields['sam_status']}' (should be active)"
            })
            checklist["required_ok"] = False
        
        if not parsed_fields["naics"]:
            checklist["problems"].append({
                "code": "missing_naics",
                "rule_id": "R2",
                "evidence": "No NAICS codes found in documents"
            })
            checklist["required_ok"] = False
        
        # Generate intelligent brief based on analysis
        strengths = []
        weaknesses = []
        
        if parsed_fields["uei"]:
            strengths.append(f"✅ UEI present: {parsed_fields['uei']}")
        if parsed_fields["duns"]:
            strengths.append(f"✅ DUNS present: {parsed_fields['duns']}")
        if parsed_fields["naics"]:
            strengths.append(f"✅ NAICS codes identified: {', '.join(parsed_fields['naics'])}")
        if parsed_fields["sam_status"] in ["active", "pending"]:
            strengths.append(f"✅ SAM status: {parsed_fields['sam_status']}")
        
        if checklist["problems"]:
            for problem in checklist["problems"]:
                weaknesses.append(f"❌ {problem['rule_id']}: {problem['evidence']}")
        
        brief = f"""GSA Onboarding Analysis Report - Request {request_id}

EXECUTIVE SUMMARY:
This analysis reviews the submitted GSA onboarding documents for compliance with federal contracting requirements (Rules R1-R5).

COMPLIANCE STATUS: {'✅ COMPLIANT' if checklist['required_ok'] else '❌ NON-COMPLIANT'}

STRENGTHS:
{chr(10).join(strengths) if strengths else '- Documents submitted successfully'}

ISSUES IDENTIFIED:
{chr(10).join(weaknesses) if weaknesses else '- No compliance issues found'}

RECOMMENDATIONS:
1. Ensure all required fields (UEI, DUNS, SAM status) are complete and accurate
2. Verify past performance projects meet the $25,000 minimum threshold (R3)
3. Confirm pricing is competitive and labor categories align with NAICS codes (R4)
4. Review document formatting and ensure all PII is properly redacted (R5)

NEXT STEPS:
- Address any identified compliance issues
- Prepare additional documentation if required
- Schedule follow-up review if needed

Note: This is an enhanced mock analysis. Set your OpenAI API key for full AI-powered analysis with advanced rule interpretation.
"""
        
        # Generate personalized client email
        entity_name = parsed_fields["entity_name"] or "Valued Client"
        status_message = "compliant" if checklist["required_ok"] else "non-compliant"
        
        email_body = f"""Dear {entity_name},

Thank you for submitting your GSA onboarding documents for review.

ANALYSIS COMPLETE - Status: {status_message.upper()}

We have completed our comprehensive analysis of your submission. {'Congratulations!' if checklist['required_ok'] else 'We have identified some areas that need attention.'}

SUMMARY OF FINDINGS:"""
        
        if checklist["required_ok"]:
            email_body += f"""

✅ STRENGTHS:
{chr(10).join(strengths) if strengths else '- Documents submitted successfully'}

Your submission appears to meet the basic GSA requirements. We recommend proceeding with the next steps in the onboarding process."""
        else:
            email_body += f"""

❌ ISSUES REQUIRING ATTENTION:
{chr(10).join(weaknesses)}

✅ STRENGTHS:
{chr(10).join(strengths) if strengths else '- Documents submitted successfully'}"""
        
        email_body += f"""

NEXT STEPS:
1. {'Review and address the issues listed above' if not checklist['required_ok'] else 'Proceed with final submission'}
2. Ensure all required fields are complete and accurate
3. Verify past performance meets GSA requirements (minimum $25,000 per project)
4. Confirm pricing aligns with market rates and labor categories

TIMELINE:
- Please respond within 5 business days with any corrections
- We will schedule a follow-up review once issues are addressed
- Final approval typically takes 2-3 weeks after all requirements are met

For questions or clarifications, please don't hesitate to contact us at your convenience.

Best regards,
GSA Review Team
Federal Contracting Division

Note: This is an enhanced mock analysis. Set your OpenAI API key for full AI-powered analysis with advanced rule interpretation.
"""
        
        client_email = email_body
        
        citations = [
            {
                "rule_id": "R1",
                "chunk": "Required: UEI (12 characters, alphanumeric), DUNS (9 digits), SAM status active"
            },
            {
                "rule_id": "R3", 
                "chunk": "At least 1 past performance project ≥ $25,000 within 36 months"
            }
        ]
        
        return {
            "parsed": parsed_fields,
            "checklist": checklist,
            "brief": brief.strip(),
            "client_email": client_email.strip(),
            "citations": citations
        }
    
    def get_assistant_info(self) -> Dict[str, Any]:
        try:
            assistant = self.client.beta.assistants.retrieve(
                self.assistant_id,
                extra_headers={"OpenAI-Beta": "assistants=v2"}
            )
            return {
                "id": assistant.id,
                "name": assistant.name,
                "model": assistant.model,
                "created_at": assistant.created_at
            }
        except Exception as e:
            logger.error(f"Error retrieving assistant info: {e}")
            return {"error": str(e)}
