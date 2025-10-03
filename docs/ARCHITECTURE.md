# GetGSA Architecture

## System Overview

GetGSA is an AI-powered GSA onboarding assistant that uses OpenAI's Assistants API to automate document review and compliance checking. The system is designed with a clean separation of concerns and scalable architecture.

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   OpenAI API    │
│   (HTML/JS)     │◄──►│   (FastAPI)     │◄──►│  (Assistants)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Database      │
                       │   (SQLite)      │
                       └─────────────────┘
```

## Component Details

### 1. Frontend (Single Page Application)
- **Technology**: HTML5, CSS3, JavaScript (ES6+)
- **Location**: `frontend/index.html`
- **Features**:
  - Document input interface
  - Real-time status updates
  - Results visualization
  - Responsive design

### 2. Backend (FastAPI)
- **Technology**: Python 3.9+, FastAPI, SQLAlchemy
- **Location**: `backend/app/`
- **Structure**:
  ```
  app/
  ├── api/           # API endpoints
  ├── core/          # Core configuration and utilities
  ├── models/        # Database models (if needed)
  └── services/      # External service integrations
  ```

### 3. OpenAI Assistants API Integration
- **Service**: `app/services/openai_service.py`
- **Features**:
  - Persistent assistant with GSA rules knowledge
  - Retrieval-augmented generation (RAG)
  - Structured JSON responses
  - Error handling and fallbacks

### 4. Database (SQLite)
- **Technology**: SQLAlchemy ORM with SQLite
- **Models**:
  - `DocumentRequest`: Tracks ingestion requests
  - `RedactedDocument`: Stores redacted document content
- **Location**: `backend/gsa.db` (created automatically)

## Data Flow

### Document Ingestion Flow
1. **User Input**: Documents pasted into frontend
2. **Validation**: Backend validates document size and count
3. **PII Redaction**: Emails, phones, and SSNs are redacted
4. **Storage**: Redacted documents stored in database
5. **Response**: Request ID returned for analysis

### Analysis Flow
1. **Request**: Analysis request with request ID
2. **Document Retrieval**: Backend fetches redacted documents
3. **AI Processing**: Documents sent to OpenAI Assistant
4. **Rule Application**: Assistant applies GSA Rules Pack (R1-R5)
5. **Response Generation**: Structured analysis returned
6. **Storage**: Results stored in database
7. **Response**: Complete analysis returned to frontend

## API Design

### RESTful Endpoints
- `POST /api/v1/ingest` - Document ingestion
- `POST /api/v1/analyze` - Document analysis
- `GET /api/v1/analyze/{request_id}` - Retrieve results
- `GET /api/v1/healthz` - Health check

### Request/Response Models
All endpoints use Pydantic models for validation and serialization:
- Input validation
- Type safety
- Automatic documentation
- Error handling

## Security Architecture

### PII Protection
- **Redaction**: Automatic redaction of emails, phones, SSNs
- **Storage**: Only redacted content stored in database
- **Extraction**: PII extracted before redaction for analysis

### Input Validation
- **Size Limits**: 2MB per document, 20 documents per request
- **Content Validation**: Required fields checked
- **Rate Limiting**: Configurable per-minute limits

### API Security
- **CORS**: Configured for frontend integration
- **Error Handling**: Sensitive information not exposed
- **Input Sanitization**: All inputs validated and sanitized

## Scalability Considerations

### Horizontal Scaling
- **Stateless Backend**: No session state, scales horizontally
- **Database**: SQLite → PostgreSQL for production
- **Load Balancing**: Multiple FastAPI instances possible

### Performance Optimization
- **Async Processing**: FastAPI async/await for I/O operations
- **Caching**: Redis for session/request caching (future)
- **Database Indexing**: Optimized queries with proper indexes

### OpenAI API Scaling
- **Rate Limiting**: Built-in OpenAI rate limiting
- **Retry Logic**: Exponential backoff for API failures
- **Cost Management**: Token usage monitoring

## Deployment Architecture

### Development
```
Developer Machine
├── Frontend (localhost:8000)
├── Backend (uvicorn dev server)
└── SQLite Database
```

### Production (Recommended)
```
Load Balancer
├── Frontend (Static hosting)
├── Backend (Multiple FastAPI instances)
├── Database (PostgreSQL cluster)
└── Redis (Caching layer)
```

## Monitoring and Observability

### Logging
- **Structured Logging**: JSON format for easy parsing
- **Log Levels**: DEBUG, INFO, WARNING, ERROR
- **Request Tracking**: Unique request IDs for tracing

### Health Checks
- **Database**: Connection status checked
- **OpenAI API**: Service availability monitored
- **System**: Memory, disk, CPU monitoring

### Metrics
- **Request Volume**: Documents processed per minute
- **Success Rates**: API endpoint success/failure rates
- **Response Times**: P50, P95, P99 latencies
- **Cost Tracking**: OpenAI API usage and costs

## Error Handling Strategy

### Graceful Degradation
- **AI Failures**: Fallback to rule-based validation
- **Database Issues**: Retry with exponential backoff
- **Network Problems**: Circuit breaker pattern

### User Experience
- **Clear Error Messages**: User-friendly error descriptions
- **Progress Indicators**: Loading states and progress bars
- **Retry Mechanisms**: Automatic retry for transient failures

## Future Enhancements

### Phase 2 Features
- **Multi-tenancy**: Support for multiple organizations
- **Advanced Analytics**: Compliance trends and insights
- **Workflow Management**: Document review workflows
- **Integration APIs**: Connect with existing systems

### Technical Improvements
- **Microservices**: Split into focused services
- **Event Sourcing**: Audit trail for all changes
- **GraphQL**: More flexible API queries
- **Real-time Updates**: WebSocket for live updates

## Configuration Management

### Environment Variables
- **OpenAI API Key**: Secure API access
- **Database URL**: Database connection string
- **Security Keys**: JWT signing and encryption
- **Feature Flags**: Enable/disable features

### Configuration Files
- **Settings**: Centralized configuration management
- **Validation**: Pydantic settings validation
- **Documentation**: Auto-generated from code

## Development Workflow

### Code Organization
- **Separation of Concerns**: Clear boundaries between layers
- **Dependency Injection**: Testable and modular code
- **Type Hints**: Full Python type annotation
- **Documentation**: Inline docstrings and type hints

### Testing Strategy
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **API Tests**: Contract testing for endpoints
- **Performance Tests**: Load and stress testing

### CI/CD Pipeline
- **Code Quality**: Linting, formatting, type checking
- **Testing**: Automated test execution
- **Security**: Vulnerability scanning
- **Deployment**: Automated deployment to staging/production


