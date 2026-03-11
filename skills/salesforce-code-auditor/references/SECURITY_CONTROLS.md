# Salesforce Security Controls — Complete Reference

## Overview

Salesforce security is built on multiple layers: Organization, Object, Field, and Record level. Understanding and properly implementing these controls is **mandatory** for enterprise applications.

---

## Security Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Organization Level                        │
│         (Login IP Ranges, Login Hours, Password Policies)    │
├─────────────────────────────────────────────────────────────┤
│                    License/Permission Set Level              │
│              (User Licenses, Permission Set Licenses)        │
├─────────────────────────────────────────────────────────────┤
│                    Object Level (CRUD)                       │
│         (Create, Read, Update, Delete on Objects)            │
├─────────────────────────────────────────────────────────────┤
│                    Field Level Security (FLS)                │
│              (Visible, Read-Only per Field)                  │
├─────────────────────────────────────────────────────────────┤
│                    Record Level (Sharing)                    │
│     (OWD, Sharing Rules, Manual Sharing, Apex Sharing)       │
└─────────────────────────────────────────────────────────────┘
```

---

## CRUD (Object-Level Security)

### Checking CRUD in Apex

**Modern Approach (Spring '20+)**:
```apex
// Check before DML operations
if (!Schema.sObjectType.Account.isCreateable()) {
    throw new SecurityException('Insufficient privileges to create Account');
}

if (!Schema.sObjectType.Account.isUpdateable()) {
    throw new SecurityException('Insufficient privileges to update Account');
}

if (!Schema.sObjectType.Account.isDeletable()) {
    throw new SecurityException('Insufficient privileges to delete Account');
}

if (!Schema.sObjectType.Account.isAccessible()) {
    throw new SecurityException('Insufficient privileges to read Account');
}
```

### WITH SECURITY_ENFORCED (Preferred)

```apex
// Automatically enforces FLS and CRUD
List<Account> accounts = [
    SELECT Id, Name, Phone, Industry
    FROM Account
    WHERE Industry = 'Technology'
    WITH SECURITY_ENFORCED
];
```

### Security.stripInaccessible (Flexible)

```apex
// Strip fields user can't access
List<Account> accounts = [SELECT Id, Name, Phone, AnnualRevenue FROM Account];
SObjectAccessDecision decision = Security.stripInaccessible(
    AccessType.READABLE,
    accounts
);
List<Account> sanitizedAccounts = decision.getRecords();

// Check which fields were removed
Map<String, Set<String>> removedFields = decision.getRemovedFields();
```

---

## FLS (Field-Level Security)

### Checking FLS Programmatically

```apex
public class FLSChecker {
    
    public static Boolean isFieldAccessible(String objectName, String fieldName) {
        Schema.SObjectType sObjType = Schema.getGlobalDescribe().get(objectName);
        if (sObjType == null) return false;
        
        Schema.DescribeFieldResult fieldDescribe = 
            sObjType.getDescribe().fields.getMap().get(fieldName)?.getDescribe();
        
        return fieldDescribe != null && fieldDescribe.isAccessible();
    }
    
    public static Boolean isFieldUpdateable(String objectName, String fieldName) {
        Schema.SObjectType sObjType = Schema.getGlobalDescribe().get(objectName);
        if (sObjType == null) return false;
        
        Schema.DescribeFieldResult fieldDescribe = 
            sObjType.getDescribe().fields.getMap().get(fieldName)?.getDescribe();
        
        return fieldDescribe != null && fieldDescribe.isUpdateable();
    }
    
    public static Boolean isFieldCreateable(String objectName, String fieldName) {
        Schema.SObjectType sObjType = Schema.getGlobalDescribe().get(objectName);
        if (sObjType == null) return false;
        
        Schema.DescribeFieldResult fieldDescribe = 
            sObjType.getDescribe().fields.getMap().get(fieldName)?.getDescribe();
        
        return fieldDescribe != null && fieldDescribe.isCreateable();
    }
    
    public static void enforceFieldAccess(String objectName, List<String> fields, AccessType accessType) {
        List<String> inaccessibleFields = new List<String>();
        
        for (String field : fields) {
            Boolean hasAccess = false;
            switch on accessType {
                when READABLE {
                    hasAccess = isFieldAccessible(objectName, field);
                }
                when CREATABLE {
                    hasAccess = isFieldCreateable(objectName, field);
                }
                when UPDATABLE {
                    hasAccess = isFieldUpdateable(objectName, field);
                }
            }
            if (!hasAccess) {
                inaccessibleFields.add(field);
            }
        }
        
        if (!inaccessibleFields.isEmpty()) {
            throw new SecurityException(
                'Insufficient field-level access for: ' + String.join(inaccessibleFields, ', ')
            );
        }
    }
}
```

---

## Record-Level Security (Sharing)

### Organization-Wide Defaults (OWD)

| Setting | Description |
|---------|-------------|
| Private | Only owner and users above in hierarchy |
| Public Read Only | All users can read, only owner can edit |
| Public Read/Write | All users can read and edit |
| Controlled by Parent | Inherits from master-detail parent |
| Public Full Access | All users can read, edit, delete, transfer |

### Sharing Keywords in Apex

```apex
// Enforces sharing rules (default for most contexts)
public with sharing class MyClass {
    // User's sharing rules are enforced
}

// Bypasses sharing rules (use with caution)
public without sharing class MyClass {
    // Runs in system mode for record access
    // STILL respects CRUD and FLS!
}

// Inherits sharing from calling context
public inherited sharing class MyClass {
    // Recommended for utility classes
}
```

### When to Use Each

| Context | Recommendation |
|---------|---------------|
| Controllers | `with sharing` (always) |
| Service Classes | `with sharing` or `inherited sharing` |
| Utility Classes | `inherited sharing` |
| Batch Apex | `without sharing` only if needed for full data access |
| System Operations | `without sharing` with explicit justification |
| Test Classes | `@IsTest` (inherits from class under test) |

### Programmatic Sharing

```apex
// Create a sharing record
Account_Share share = new Account_Share();
share.ParentId = accountId;
share.UserOrGroupId = userId;
share.AccessLevel = 'Edit'; // Read, Edit, All
share.RowCause = Schema.Account_Share.RowCause.Manual;
insert share;
```

---

## SOQL Injection Prevention

### Vulnerable Code — CRITICAL

```apex
// CRITICAL VULNERABILITY: Direct string concatenation
String query = 'SELECT Id, Name FROM Account WHERE Name = \'' + userInput + '\'';
List<Account> accounts = Database.query(query);
```

### Secure Patterns

**Pattern 1: Bind Variables (Preferred)**
```apex
String searchName = userInput;
List<Account> accounts = [
    SELECT Id, Name 
    FROM Account 
    WHERE Name = :searchName
];
```

**Pattern 2: String.escapeSingleQuotes**
```apex
// For dynamic queries where bind variables aren't possible
String safeName = String.escapeSingleQuotes(userInput);
String query = 'SELECT Id, Name FROM Account WHERE Name = \'' + safeName + '\'';
List<Account> accounts = Database.query(query);
```

**Pattern 3: Dynamic SOQL with Type Checking**
```apex
public class SecureQueryBuilder {
    
    public static List<SObject> secureQuery(
        String objectName, 
        List<String> fields, 
        String whereClause,
        Map<String, Object> bindVars
    ) {
        // Validate object exists and is accessible
        Schema.SObjectType sObjType = Schema.getGlobalDescribe().get(objectName);
        if (sObjType == null || !sObjType.getDescribe().isAccessible()) {
            throw new SecurityException('Object not accessible: ' + objectName);
        }
        
        // Validate all fields
        Map<String, Schema.SObjectField> fieldMap = sObjType.getDescribe().fields.getMap();
        List<String> validFields = new List<String>();
        
        for (String field : fields) {
            Schema.SObjectField sField = fieldMap.get(field.toLowerCase());
            if (sField != null && sField.getDescribe().isAccessible()) {
                validFields.add(field);
            }
        }
        
        if (validFields.isEmpty()) {
            throw new SecurityException('No accessible fields specified');
        }
        
        // Build query with validated components
        String query = 'SELECT ' + String.join(validFields, ', ') + 
                      ' FROM ' + String.escapeSingleQuotes(objectName);
        
        if (String.isNotBlank(whereClause)) {
            query += ' WHERE ' + whereClause;
        }
        
        return Database.queryWithBinds(query, bindVars, AccessLevel.USER_MODE);
    }
}
```

---

## Cross-Site Scripting (XSS) Prevention

### Visualforce

```html
<!-- VULNERABLE: Direct output -->
{!userInput}

<!-- SECURE: Automatic encoding (default in most contexts) -->
<apex:outputText value="{!userInput}" escape="true"/>

<!-- SECURE: JavaScript context -->
<script>
    var data = '{!JSENCODE(userInput)}';
</script>

<!-- SECURE: HTML attribute context -->
<div title="{!HTMLENCODE(userInput)}"></div>

<!-- SECURE: URL context -->
<a href="{!URLENCODE(userInput)}">Link</a>
```

### Lightning Web Components

LWC has automatic XSS protection through Locker Service, but still requires care:

```javascript
// VULNERABLE: innerHTML assignment
this.template.querySelector('div').innerHTML = userInput;

// SECURE: Use data binding
// In template: {userInput}
// Locker Service automatically escapes

// SECURE: For dynamic HTML, use lightning-formatted-rich-text
// <lightning-formatted-rich-text value={richTextContent}></lightning-formatted-rich-text>
```

### Apex REST Responses

```apex
@RestResource(urlMapping='/api/data/*')
global with sharing class MyRestResource {
    
    @HttpGet
    global static String getData() {
        // Set proper content type
        RestContext.response.addHeader('Content-Type', 'application/json');
        
        // Return JSON (automatically safe for most contexts)
        return JSON.serialize(data);
    }
}
```

---

## CSRF Protection

### Visualforce

Visualforce automatically includes CSRF tokens in forms. Ensure:
- Always use `<apex:form>` for forms
- Never disable `@RemoteAction` CSRF protection without justification

```apex
@RemoteAction
// CSRF protection is ON by default
public static String secureAction(String param) {
    // Implementation
}

// Only disable when specifically needed for unauthenticated endpoints
@RemoteAction(csrf=false)
public static String publicEndpoint(String param) {
    // Must have alternative security measures
}
```

### Lightning Components

Lightning handles CSRF automatically through its framework. No additional action needed for standard @AuraEnabled methods.

---

## Encryption

### Platform Encryption

```apex
// Shield Platform Encryption is configured declaratively
// Fields marked as encrypted are automatically handled

// For custom encryption needs:
Blob key = Crypto.generateAesKey(256);
Blob data = Blob.valueOf('Sensitive Data');
Blob encrypted = Crypto.encryptWithManagedIV('AES256', key, data);
Blob decrypted = Crypto.decryptWithManagedIV('AES256', key, encrypted);
```

### Storing Sensitive Data

```apex
// Use Protected Custom Settings for sensitive configuration
// Or use Named Credentials for external system credentials

// NEVER hardcode credentials
// BAD:
String apiKey = 'sk_live_abc123'; // CRITICAL VULNERABILITY

// GOOD:
String apiKey = My_Settings__c.getOrgDefaults().API_Key__c;
// Or use Named Credentials
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:MyNamedCredential/api/endpoint');
```

---

## Security Audit Checklist

### CRUD Checks
- [ ] All DML operations preceded by CRUD checks
- [ ] Custom objects have proper CRUD enforcement
- [ ] Standard objects respect user permissions

### FLS Checks  
- [ ] WITH SECURITY_ENFORCED used in queries OR
- [ ] Security.stripInaccessible used for flexibility
- [ ] Field describe checks before displaying sensitive fields

### Sharing
- [ ] Controllers use `with sharing`
- [ ] `without sharing` has documented justification
- [ ] Record-level access tested with different user profiles

### Injection Prevention
- [ ] No direct string concatenation in SOQL/SOSL
- [ ] Bind variables used where possible
- [ ] escapeSingleQuotes used for dynamic queries
- [ ] User input validated before use

### XSS Prevention
- [ ] Visualforce uses proper encoding functions
- [ ] LWC doesn't use innerHTML with user data
- [ ] REST responses use proper content types

### CSRF Protection
- [ ] Forms use apex:form or lightning components
- [ ] CSRF not disabled without justification

### Sensitive Data
- [ ] No hardcoded credentials
- [ ] API keys in Protected Custom Settings or Named Credentials
- [ ] Encryption used for sensitive fields
- [ ] Debug logs don't contain sensitive data
