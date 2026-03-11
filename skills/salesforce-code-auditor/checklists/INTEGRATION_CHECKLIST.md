# Integration Audit Checklist

## Overview
This checklist covers integration-specific quality, security, and reliability checks.

---

## Authentication & Authorization

### Credential Management
- [ ] **AUTH-001**: Named Credentials used for external authentication
- [ ] **AUTH-002**: No hardcoded credentials in code
- [ ] **AUTH-003**: API keys stored in Protected Custom Settings
- [ ] **AUTH-004**: Certificates managed in Certificate and Key Management
- [ ] **AUTH-005**: OAuth flows use proper grant types

### Permission Configuration
- [ ] **PERM-001**: Connected App configured for integrations
- [ ] **PERM-002**: Appropriate OAuth scopes defined
- [ ] **PERM-003**: IP restrictions configured where needed
- [ ] **PERM-004**: API user has appropriate permissions
- [ ] **PERM-005**: Session policies configured

---

## HTTP Callout Quality

### Request Configuration
- [ ] **REQ-001**: Timeout configured (not default)
- [ ] **REQ-002**: Content-Type header set
- [ ] **REQ-003**: Accept header set
- [ ] **REQ-004**: User-Agent header for identification
- [ ] **REQ-005**: Correlation/Request ID for tracing

### Response Handling
- [ ] **RESP-001**: Status code checked
- [ ] **RESP-002**: 2xx range validated for success
- [ ] **RESP-003**: Error responses parsed
- [ ] **RESP-004**: Response body validated
- [ ] **RESP-005**: Unexpected content types handled

---

## Error Handling

### Exception Handling
- [ ] **ERR-001**: CalloutException caught
- [ ] **ERR-002**: JSONException caught for parsing
- [ ] **ERR-003**: Timeout scenarios handled
- [ ] **ERR-004**: Network failures handled gracefully
- [ ] **ERR-005**: Rate limit responses (429) handled

### Retry Logic
- [ ] **RETRY-001**: Retry implemented for transient failures
- [ ] **RETRY-002**: Exponential backoff used
- [ ] **RETRY-003**: Maximum retry count defined
- [ ] **RETRY-004**: Idempotency considered for retries
- [ ] **RETRY-005**: Circuit breaker for persistent failures

---

## Resilience Patterns

### Circuit Breaker
- [ ] **CB-001**: Circuit breaker implemented for external services
- [ ] **CB-002**: Failure threshold defined
- [ ] **CB-003**: Reset timeout configured
- [ ] **CB-004**: Half-open state handled
- [ ] **CB-005**: Circuit state monitored/logged

### Fallback Strategies
- [ ] **FALL-001**: Graceful degradation implemented
- [ ] **FALL-002**: Cached data used when service unavailable
- [ ] **FALL-003**: Queue for later processing
- [ ] **FALL-004**: User notification for failures
- [ ] **FALL-005**: Alternative service considered

---

## Async Processing

### Callout Patterns
- [ ] **ASYNC-001**: No callouts in triggers (use async)
- [ ] **ASYNC-002**: @future(callout=true) for simple async
- [ ] **ASYNC-003**: Queueable for complex async with chaining
- [ ] **ASYNC-004**: Batch for high-volume processing
- [ ] **ASYNC-005**: Platform Events for event-driven integration

### Async Best Practices
- [ ] **ASYNC-BP-001**: Check context before queueing (`!System.isFuture()`)
- [ ] **ASYNC-BP-002**: Handle async limits (50 futures, 50 queueables)
- [ ] **ASYNC-BP-003**: State passed correctly to async jobs
- [ ] **ASYNC-BP-004**: Async job failures logged
- [ ] **ASYNC-BP-005**: Monitoring for stuck jobs

---

## Data Transformation

### Request Transformation
- [ ] **TRANS-001**: DTO classes for request/response
- [ ] **TRANS-002**: JSON serialization tested
- [ ] **TRANS-003**: Date/DateTime format matches API
- [ ] **TRANS-004**: Null handling consistent
- [ ] **TRANS-005**: Character encoding correct (UTF-8)

### Response Transformation
- [ ] **PARSE-001**: Response parsed safely
- [ ] **PARSE-002**: Missing fields handled
- [ ] **PARSE-003**: Type mismatches handled
- [ ] **PARSE-004**: Large responses handled
- [ ] **PARSE-005**: Validation on parsed data

---

## Logging & Monitoring

### Integration Logging
- [ ] **LOG-001**: Request/response logged
- [ ] **LOG-002**: Sensitive data masked in logs
- [ ] **LOG-003**: Correlation ID for tracing
- [ ] **LOG-004**: Timing/latency logged
- [ ] **LOG-005**: Error details captured

### Monitoring
- [ ] **MON-001**: Success/failure metrics tracked
- [ ] **MON-002**: Latency metrics tracked
- [ ] **MON-003**: Error rate alerts configured
- [ ] **MON-004**: Circuit breaker state monitored
- [ ] **MON-005**: Retry count monitored

---

## Security

### Transport Security
- [ ] **SEC-001**: HTTPS enforced (no HTTP)
- [ ] **SEC-002**: TLS 1.2+ required
- [ ] **SEC-003**: Certificate validation enabled
- [ ] **SEC-004**: Certificate pinning considered
- [ ] **SEC-005**: Sensitive headers protected

### Data Security
- [ ] **DATA-001**: Sensitive data encrypted in transit
- [ ] **DATA-002**: PII/PHI handled per compliance
- [ ] **DATA-003**: Response data sanitized
- [ ] **DATA-004**: Audit trail for data exchange
- [ ] **DATA-005**: Data retention policies followed

---

## Testing

### Mock Testing
- [ ] **TEST-001**: HttpCalloutMock implemented
- [ ] **TEST-002**: Success scenarios tested
- [ ] **TEST-003**: Error scenarios tested (4xx, 5xx)
- [ ] **TEST-004**: Timeout scenarios tested
- [ ] **TEST-005**: Retry logic tested
- [ ] **TEST-006**: Circuit breaker tested

### Integration Testing
- [ ] **INT-001**: Sandbox integration tested
- [ ] **INT-002**: Data volume testing performed
- [ ] **INT-003**: Concurrent request testing
- [ ] **INT-004**: Error recovery tested
- [ ] **INT-005**: Rollback scenarios tested

---

## Governor Limits

### Callout Limits
- [ ] **LIMIT-001**: Callout count tracked (max 100)
- [ ] **LIMIT-002**: Total callout time tracked (max 120s)
- [ ] **LIMIT-003**: Response size handled (max 6MB sync)
- [ ] **LIMIT-004**: Batch callouts for high volume
- [ ] **LIMIT-005**: Async for non-critical callouts

### Best Practices
- [ ] **BP-001**: Batch multiple records per callout
- [ ] **BP-002**: Minimize callout frequency
- [ ] **BP-003**: Cache responses where appropriate
- [ ] **BP-004**: Use continuation for long-running callouts
- [ ] **BP-005**: Monitor limit consumption

---

## API Design (Inbound)

### REST Resource Design
- [ ] **REST-001**: RESTful URL patterns
- [ ] **REST-002**: Appropriate HTTP methods (GET, POST, PUT, DELETE)
- [ ] **REST-003**: Proper status codes returned
- [ ] **REST-004**: Consistent response format
- [ ] **REST-005**: Error response format documented

### API Security
- [ ] **API-SEC-001**: Authentication required
- [ ] **API-SEC-002**: Authorization checked
- [ ] **API-SEC-003**: Input validation performed
- [ ] **API-SEC-004**: Rate limiting considered
- [ ] **API-SEC-005**: CORS configured if needed

---

## Documentation

### API Documentation
- [ ] **DOC-001**: Endpoint documentation complete
- [ ] **DOC-002**: Request/response examples provided
- [ ] **DOC-003**: Error codes documented
- [ ] **DOC-004**: Authentication requirements documented
- [ ] **DOC-005**: Rate limits documented

### Operational Documentation
- [ ] **OPS-001**: Runbook for common issues
- [ ] **OPS-002**: Escalation procedures documented
- [ ] **OPS-003**: Monitoring dashboards documented
- [ ] **OPS-004**: Disaster recovery procedures
- [ ] **OPS-005**: Contact information for external teams
