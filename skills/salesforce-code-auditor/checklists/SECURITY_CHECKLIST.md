# Security Audit Checklist

## Overview
This checklist is used to systematically review Salesforce code for security vulnerabilities and compliance with security best practices.

---

## CRITICAL Security Issues (Severity 1)

### SOQL/SOSL Injection
- [ ] **INJ-001**: No direct string concatenation in SOQL queries
- [ ] **INJ-002**: Bind variables used for user-supplied values
- [ ] **INJ-003**: `String.escapeSingleQuotes()` used when bind variables not possible
- [ ] **INJ-004**: Dynamic SOQL validated against schema before execution
- [ ] **INJ-005**: User input sanitized before use in queries

**Detection Pattern**:
```apex
// VULNERABLE
String query = 'SELECT Id FROM Account WHERE Name = \'' + userInput + '\'';
Database.query(query);

// SECURE
String query = 'SELECT Id FROM Account WHERE Name = :userInput';
Database.query(query);
```

### Cross-Site Scripting (XSS)
- [ ] **XSS-001**: No innerHTML assignment with user data in LWC
- [ ] **XSS-002**: `HTMLENCODE()` used in Visualforce for HTML context
- [ ] **XSS-003**: `JSENCODE()` used in Visualforce for JavaScript context
- [ ] **XSS-004**: `URLENCODE()` used for URL parameters
- [ ] **XSS-005**: Aura `$A.util.escapeHtml()` used where needed

### Hardcoded Credentials
- [ ] **CRED-001**: No API keys in source code
- [ ] **CRED-002**: No passwords in source code
- [ ] **CRED-003**: No tokens in source code
- [ ] **CRED-004**: Named Credentials used for external authentication
- [ ] **CRED-005**: Protected Custom Settings used for sensitive config

### Sensitive Data Exposure
- [ ] **DATA-001**: PII not logged to debug logs
- [ ] **DATA-002**: Sensitive fields encrypted at rest (Shield)
- [ ] **DATA-003**: API responses don't include unnecessary sensitive data
- [ ] **DATA-004**: Error messages don't expose system internals

---

## HIGH Security Issues (Severity 2)

### CRUD Enforcement
- [ ] **CRUD-001**: `isCreateable()` checked before insert
- [ ] **CRUD-002**: `isUpdateable()` checked before update
- [ ] **CRUD-003**: `isDeletable()` checked before delete
- [ ] **CRUD-004**: `isAccessible()` checked before read
- [ ] **CRUD-005**: CRUD checks use `Schema.sObjectType`

**Detection Pattern**:
```apex
// Check before DML
if (!Schema.sObjectType.Account.isCreateable()) {
    throw new SecurityException('Insufficient privileges');
}
insert account;
```

### FLS Enforcement
- [ ] **FLS-001**: `WITH SECURITY_ENFORCED` used in SOQL queries
- [ ] **FLS-002**: `Security.stripInaccessible()` used when flexibility needed
- [ ] **FLS-003**: Field-level `isAccessible()` checked for display
- [ ] **FLS-004**: Field-level `isUpdateable()` checked before field update
- [ ] **FLS-005**: Field-level `isCreateable()` checked before field creation

**Detection Pattern**:
```apex
// Preferred
List<Account> accounts = [
    SELECT Id, Name, Phone
    FROM Account
    WITH SECURITY_ENFORCED
];

// Alternative
SObjectAccessDecision decision = Security.stripInaccessible(
    AccessType.READABLE, accounts
);
```

### Sharing Rules
- [ ] **SHARE-001**: Controllers use `with sharing`
- [ ] **SHARE-002**: `without sharing` has documented justification
- [ ] **SHARE-003**: Utility classes use `inherited sharing`
- [ ] **SHARE-004**: Batch classes have explicit sharing declaration
- [ ] **SHARE-005**: Record access tested with different profiles

### CSRF Protection
- [ ] **CSRF-001**: `apex:form` used for form submission
- [ ] **CSRF-002**: `@RemoteAction` CSRF not disabled without justification
- [ ] **CSRF-003**: Custom REST endpoints validate origin
- [ ] **CSRF-004**: State-changing operations require POST method

---

## MEDIUM Security Issues (Severity 3)

### Input Validation
- [ ] **VAL-001**: All user inputs validated on server side
- [ ] **VAL-002**: Input length limits enforced
- [ ] **VAL-003**: Input format validated (email, phone, etc.)
- [ ] **VAL-004**: Numeric ranges validated
- [ ] **VAL-005**: Required fields enforced

### Access Control
- [ ] **ACC-001**: Custom permissions checked for feature access
- [ ] **ACC-002**: Permission sets used for granular access
- [ ] **ACC-003**: Record ownership considered in logic
- [ ] **ACC-004**: Hierarchical access properly implemented

### Secure Communication
- [ ] **COMM-001**: All external callouts use HTTPS
- [ ] **COMM-002**: Certificate validation not bypassed
- [ ] **COMM-003**: TLS 1.2+ enforced
- [ ] **COMM-004**: Sensitive data not in URL parameters

### Session Security
- [ ] **SESS-001**: Session settings properly configured
- [ ] **SESS-002**: Clickjack protection enabled
- [ ] **SESS-003**: CSP headers configured
- [ ] **SESS-004**: Session timeout appropriate

---

## LOW Security Issues (Severity 4)

### Logging and Monitoring
- [ ] **LOG-001**: Security events logged
- [ ] **LOG-002**: Failed authentication attempts tracked
- [ ] **LOG-003**: Sensitive data masked in logs
- [ ] **LOG-004**: Log retention policy defined

### Code Quality (Security Impact)
- [ ] **QUAL-001**: No commented-out code with credentials
- [ ] **QUAL-002**: Debug statements removed from production
- [ ] **QUAL-003**: Test classes don't contain real credentials
- [ ] **QUAL-004**: Documentation doesn't expose security details

---

## Compliance Checkpoints

### SOX Compliance
- [ ] Audit trail for financial data changes
- [ ] Segregation of duties enforced
- [ ] Access reviews documented

### GDPR Compliance
- [ ] Data subject access supported
- [ ] Right to erasure implementable
- [ ] Data portability supported
- [ ] Consent tracking in place

### HIPAA Compliance (if applicable)
- [ ] PHI access logged
- [ ] Minimum necessary access enforced
- [ ] Encryption at rest enabled
- [ ] BAA requirements met

---

## Security Scan Integration

### Salesforce Code Analyzer
```bash
# Run security-focused scan
sf scanner run --target ./force-app --category Security --format json
```

### PMD Rules
- ApexCRUDViolation
- ApexSharingViolations
- ApexSOQLInjection
- ApexXSSFromURLParam
- ApexXSSFromEscapeFalse

### Checkmarx/Veracode Integration
- Schedule regular scans
- Review findings weekly
- Track remediation progress
