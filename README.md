# GetGSA: AI + RAG (Assistants API Version)

A minimal working product that helps automate **GSA onboarding review** by ingesting documents, classifying them, extracting key fields, applying GSA Rules Pack (R1–R5) with retrieval-augmented generation (RAG), and producing compliance checklists, negotiation briefs, and client email drafts.

##  Quick Start

### Prerequisites
- Python 3.9+
- [uv](https://docs.astral.sh/uv/) (modern Python package manager)
- OpenAI API key

### Installation

1. **Install uv** (if not already installed):
```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

2. **Clone and setup backend:**
```bash
cd backend
uv pip install -r requirements.txt
cp env.example .env
# Edit .env with your OpenAI API key
```

**For development (includes testing tools):**
```bash
cd backend
uv pip install -r requirements.txt
uv pip install pytest pytest-asyncio black flake8
```

3. **Run the backend:**
```bash
make run
```

4. **Open the frontend:**
```bash
cd frontend
open index.html
```

### Usage

1. **Ingest Documents:** Paste your GSA onboarding documents in the text area
2. **Analyze:** Click "Analyze" to get compliance results
3. **Review Results:** Check the parsed fields, compliance checklist, negotiation brief, and client email

## 📋 Features

- **Document Classification:** Automatically categorizes documents (profile, past performance, pricing)
- **Field Extraction:** Extracts UEI, DUNS, NAICS, POC info, and pricing data
- **GSA Rules Compliance:** Applies R1-R5 rules with RAG-powered validation
- **PII Protection:** Automatically redacts emails and phone numbers
- **AI-Generated Outputs:**
  - Compliance checklist with rule citations
  - Negotiation preparation brief
  - Client email draft

##  Architecture

### System Overview
GetGSA uses a modern microservices architecture with AI-powered document analysis:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend       │    │   OpenAI API    │
│   (HTML/JS)     │◄──►│   (FastAPI)      │◄──►│  (GPT-4/Assistants) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   SQLite DB      │
                       │ (Documents/Meta) │
                       └──────────────────┘
```

### Core Components

**Backend (FastAPI)**
- **API Layer**: REST endpoints for document ingestion and analysis
- **Service Layer**: OpenAI integration with GPT-4 and Assistants API
- **Data Layer**: SQLite for storing redacted documents and metadata
- **Security Layer**: PII redaction, rate limiting, input validation

**AI Engine**
- **Primary**: GPT-4 with structured JSON output for field extraction
- **Fallback**: Mock analysis for development/testing
- **Rules Engine**: Built-in GSA compliance rules (R1-R5)
- **Abstention**: AI indicates uncertainty when confidence < 70%

**Frontend**
- Single-page application with drag-drop document upload
- Real-time analysis progress indicators
- Structured results display with downloadable outputs

### Data Flow

1. **Document Ingestion**
   - User uploads documents via frontend
   - Backend validates and stores in SQLite
   - PII redaction applied automatically
   - Request ID generated for tracking

2. **AI Analysis**
   - GPT-4 processes documents with structured prompts
   - Field extraction: UEI, DUNS, NAICS, pricing, performance
   - Compliance checking against GSA rules (R1-R5)
   - Generates checklist, brief, and client email

3. **Results Delivery**
   - Structured JSON response with all analysis components
   - Frontend renders formatted results
   - User can download individual components

### AI Optimization

**Smart Field Extraction**
- Uses GPT-4's natural language understanding instead of regex patterns
- Handles varied document formats and structures
- Extracts contextual information with high accuracy
- Falls back to mock analysis for development/testing

**Intelligent Analysis**
- Context-aware compliance checking
- Rule-based validation with human-readable explanations
- Confidence scoring for uncertain extractions
- Professional tone in generated communications

## Project Structure

```
gsa/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core business logic
│   │   ├── models/         # Database models
│   │   └── services/       # External services (OpenAI)
│   ├── tests/              # Backend tests
│   └── requirements.txt
├── frontend/               # HTML/JS frontend
│   └── index.html
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md
│   ├── SECURITY.md
│   └── PROMPTS.md
├── tests/                  # Integration tests
├── Makefile               # Build commands
└── README.md
```

## 🧪 Testing

Run the test suite:
```bash
make test
```

## Security

- PII redaction for emails and phone numbers
- Input size limits (2MB max)
- Rate limiting
- AI abstention when uncertain

##  Documentation

- [Architecture](docs/ARCHITECTURE.md) - System design and data flow
- [Security](docs/SECURITY.md) - Security considerations and PII handling
- [Prompts](docs/PROMPTS.md) - AI prompts and guardrails

##  GSA Rules Pack

The system applies these rules:
- **R1:** Identity & Registry requirements
- **R2:** NAICS & SIN mapping
- **R3:** Past performance minimums
- **R4:** Pricing & catalog requirements
- **R5:** Submission hygiene (PII redaction)

## 📞 Support

For issues or questions, please check the documentation or create an issue in the repository.
