# GetGSA Security Documentation

## Security Overview

GetGSA implements comprehensive security measures to protect sensitive government contracting information while maintaining the functionality needed for GSA onboarding document review.

## PII (Personally Identifiable Information) Protection

### Automatic Redaction

The system automatically identifies and redacts the following PII elements:

#### Email Addresses
- **Patterns Detected**:
  - Standard format: `user@domain.com`
  - Variations: `user@domain.co.uk`, `user.name@domain.com`
  - Spaced formats: `user @ domain . com`
- **Redaction**: `[EMAIL_REDACTED]`
- **Implementation**: Regex-based pattern matching with case-insensitive search

#### Phone Numbers
- **Patterns Detected**:
  - US format: `(555) 123-4567`
  - International: `+1-555-123-4567`
  - Dash format: `555-123-4567`
  - Dot format: `555.123.4567`
- **Redaction**: `[PHONE_REDACTED]`
- **Implementation**: Multiple regex patterns for different formats

#### Social Security Numbers
- **Patterns Detected**:
  - Standard format: `123-45-6789`
  - Continuous: `123456789`
- **Redaction**: `[SSN_REDACTED]`
- **Implementation**: Pattern matching with validation

### PII Extraction and Analysis

Before redaction, the system:
1. **Extracts PII**: Identifies and catalogs all PII found
2. **Logs for Analysis**: Records PII types and counts (not content)
3. **Redacts Content**: Replaces PII with redaction markers
4. **Stores Redacted**: Only redacted content is stored in database

### Example PII Processing

**Input Document**:
```
Contact: jane.doe@acmerobotics.com
Phone: (555) 123-4567
SSN: 123-45-6789
```

**PII Extraction**:
```json
{
  "emails": ["jane.doe@acmerobotics.com"],
  "phones": ["(555) 123-4567"],
  "ssns": ["123-45-6789"]
}
```

**Redacted Content**:
```
Contact: [EMAIL_REDACTED]
Phone: [PHONE_REDACTED]
SSN: [SSN_REDACTED]
```

## Data Storage Security

### Database Security
- **Redacted Content Only**: Original documents with PII are never stored
- **Encryption at Rest**: SQLite database files encrypted (production)
- **Access Control**: Database access restricted to application only
- **Audit Logging**: All database operations logged

### File System Security
- **Temporary Files**: Securely deleted after processing
- **Access Permissions**: Restricted file system permissions
- **No Persistent Storage**: Original documents not saved to disk

## API Security

### Input Validation
- **Size Limits**: Maximum 2MB per document, 20 documents per request
- **Content Validation**: All inputs validated against schemas
- **SQL Injection Prevention**: Parameterized queries only
- **XSS Protection**: Input sanitization and output encoding

### Rate Limiting
- **Per-Client Limits**: 60 requests per minute per client
- **Document Limits**: Maximum document count per request
- **Size Limits**: Maximum total request size
- **Implementation**: Token bucket algorithm

### CORS Configuration
- **Origin Control**: Configurable allowed origins
- **Method Restrictions**: Only necessary HTTP methods allowed
- **Header Control**: Restricted header access
- **Credential Handling**: Secure credential management

## OpenAI API Security

### API Key Management
- **Environment Variables**: Keys stored in environment variables
- **No Hardcoding**: API keys never hardcoded in source
- **Rotation Support**: Easy key rotation capability
- **Access Logging**: API key usage monitored

### Data Transmission
- **HTTPS Only**: All communications encrypted in transit
- **Redacted Data**: Only redacted documents sent to OpenAI
- **No PII Transmission**: PII never sent to external services
- **Request Validation**: All API requests validated

### Response Handling
- **Error Sanitization**: Error messages don't expose sensitive data
- **Response Validation**: All responses validated before processing
- **Timeout Handling**: Request timeouts to prevent hanging
- **Retry Logic**: Secure retry mechanisms with backoff

## Authentication and Authorization

### Current Implementation
- **Public API**: Currently no authentication (development)
- **IP Whitelisting**: Can be configured for production
- **API Keys**: Can be added for client authentication

### Production Recommendations
- **JWT Tokens**: Stateless authentication
- **Role-Based Access**: Different permission levels
- **Session Management**: Secure session handling
- **Multi-Factor Authentication**: Additional security layer

## Network Security

### HTTPS/TLS
- **Encryption in Transit**: All communications encrypted
- **Certificate Management**: Valid SSL certificates
- **TLS Version**: Minimum TLS 1.2
- **Cipher Suites**: Strong encryption algorithms

### Firewall Configuration
- **Port Restrictions**: Only necessary ports open
- **IP Restrictions**: Source IP filtering
- **DDoS Protection**: Rate limiting and traffic shaping
- **Intrusion Detection**: Network monitoring

## Compliance and Auditing

### Audit Trail
- **Request Logging**: All API requests logged
- **Response Logging**: Analysis results logged
- **Error Logging**: Security-related errors tracked
- **User Actions**: All user actions recorded

### Data Retention
- **Redacted Documents**: Retained per policy requirements
- **Analysis Results**: Stored for audit purposes
- **Logs**: Retained for security monitoring
- **Automatic Cleanup**: Old data automatically purged

### Compliance Standards
- **FISMA**: Federal Information Security Management Act
- **NIST**: National Institute of Standards and Technology
- **FedRAMP**: Federal Risk and Authorization Management Program
- **SOC 2**: Security and availability controls

## Incident Response

### Security Monitoring
- **Real-time Alerts**: Suspicious activity detection
- **Log Analysis**: Automated log monitoring
- **Anomaly Detection**: Unusual pattern recognition
- **Threat Intelligence**: External threat feeds

### Response Procedures
- **Incident Classification**: Severity level determination
- **Escalation Process**: Clear escalation procedures
- **Communication Plan**: Stakeholder notification
- **Recovery Procedures**: System restoration steps

### Breach Response
- **Immediate Containment**: Stop ongoing breach
- **Assessment**: Determine scope and impact
- **Notification**: Regulatory and user notifications
- **Documentation**: Detailed incident documentation

## Development Security

### Secure Coding Practices
- **Input Validation**: All inputs validated
- **Output Encoding**: All outputs properly encoded
- **Error Handling**: Secure error messages
- **Code Review**: Security-focused code reviews

### Dependency Management
- **Vulnerability Scanning**: Regular dependency scans
- **Version Pinning**: Specific dependency versions
- **Security Updates**: Timely security patches
- **License Compliance**: Open source license tracking

### Testing Security
- **Penetration Testing**: Regular security assessments
- **Vulnerability Scanning**: Automated security scans
- **Code Analysis**: Static and dynamic analysis
- **Security Testing**: Security-focused test cases

## Production Deployment Security

### Infrastructure Security
- **Server Hardening**: Secure server configuration
- **Network Segmentation**: Isolated network segments
- **Access Control**: Restricted server access
- **Monitoring**: Comprehensive system monitoring

### Backup and Recovery
- **Encrypted Backups**: All backups encrypted
- **Offsite Storage**: Secure offsite backup storage
- **Recovery Testing**: Regular recovery drills
- **Data Integrity**: Backup verification

### Operational Security
- **Change Management**: Controlled system changes
- **Access Reviews**: Regular access reviews
- **Security Training**: Staff security education
- **Incident Drills**: Regular security exercises

## Security Configuration

### Environment Variables
```bash
# Security Settings
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Limits
MAX_DOCUMENT_SIZE_MB=2
MAX_DOCUMENTS_PER_REQUEST=20
RATE_LIMIT_PER_MINUTE=60

# Security Features
ENABLE_PII_REDACTION=true
ENABLE_AUDIT_LOGGING=true
```

### Security Headers
```python
# Recommended security headers
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000",
    "Content-Security-Policy": "default-src 'self'"
}
```

## Security Checklist

### Pre-Deployment
- [ ] All PII redaction tested
- [ ] Input validation implemented
- [ ] Rate limiting configured
- [ ] HTTPS enabled
- [ ] Security headers set
- [ ] Error handling secure
- [ ] Dependencies updated
- [ ] Security tests passing

### Post-Deployment
- [ ] Monitoring enabled
- [ ] Logging configured
- [ ] Backup procedures tested
- [ ] Incident response plan ready
- [ ] Security updates scheduled
- [ ] Access controls verified
- [ ] Audit trail working
- [ ] Recovery procedures tested

## Contact Information

For security-related questions or to report security issues:

- **Security Team**: security@getgsa.com
- **Incident Response**: incident@getgsa.com
- **General Inquiries**: info@getgsa.com

**Note**: This security documentation should be reviewed and updated regularly to reflect current security practices and compliance requirements.


