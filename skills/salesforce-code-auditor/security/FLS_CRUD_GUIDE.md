# FLS and CRUD Implementation Guide

## Overview

Field-Level Security (FLS) and CRUD (Create, Read, Update, Delete) permissions are fundamental to Salesforce's security model. This guide provides comprehensive implementation patterns.

---

## Understanding FLS and CRUD

### Security Hierarchy

```
Object-Level Security (CRUD)
    └── Can user Create/Read/Update/Delete THIS OBJECT?
    
    Field-Level Security (FLS)
        └── Can user Read/Edit THIS FIELD on an accessible object?
        
        Record-Level Security (Sharing)
            └── Can user access THIS SPECIFIC RECORD?
```

### Key Concepts

| Security Type | Configured In | Enforced By |
|---------------|---------------|-------------|
| CRUD | Profiles, Permission Sets | Developer (Apex) |
| FLS | Profiles, Permission Sets | Developer (Apex) or Platform |
| Sharing | OWD, Sharing Rules | `with sharing` keyword |

---

## CRUD Enforcement

### Schema Methods

```apex
// Check object accessibility
Schema.sObjectType.Account.isAccessible()
Schema.sObjectType.Account.isCreateable()
Schema.sObjectType.Account.isUpdateable()
Schema.sObjectType.Account.isDeletable()
```

### Implementation Pattern

```apex
public with sharing class AccountService {
    
    public Account createAccount(Account acc) {
        // Check CRUD before insert
        if (!Schema.sObjectType.Account.isCreateable()) {
            throw new SecurityException('Insufficient privileges to create Account');
        }
        insert acc;
        return acc;
    }
    
    public Account updateAccount(Account acc) {
        // Check CRUD before update
        if (!Schema.sObjectType.Account.isUpdateable()) {
            throw new SecurityException('Insufficient privileges to update Account');
        }
        update acc;
        return acc;
    }
    
    public void deleteAccount(Id accountId) {
        // Check CRUD before delete
        if (!Schema.sObjectType.Account.isDeletable()) {
            throw new SecurityException('Insufficient privileges to delete Account');
        }
        delete new Account(Id = accountId);
    }
    
    public List<Account> getAccounts(Set<Id> ids) {
        // Check CRUD before read
        if (!Schema.sObjectType.Account.isAccessible()) {
            throw new SecurityException('Insufficient privileges to read Account');
        }
        return [SELECT Id, Name FROM Account WHERE Id IN :ids];
    }
}
```

---

## FLS Enforcement

### Method 1: WITH SECURITY_ENFORCED (Preferred)

```apex
// Throws exception if user lacks access to any field
List<Account> accounts = [
    SELECT Id, Name, Phone, AnnualRevenue, SSN__c
    FROM Account
    WHERE Id IN :accountIds
    WITH SECURITY_ENFORCED
];
```

**Behavior**:
- Checks FLS for ALL fields in query
- Throws `System.QueryException` if any field is not accessible
- Also enforces CRUD (object-level access)

**Pros**:
- Simple, declarative
- Clear failure mode
- Recommended by Salesforce

**Cons**:
- All-or-nothing (fails if ANY field is inaccessible)
- Cannot gracefully handle partial access

---

### Method 2: Security.stripInaccessible() (Flexible)

```apex
// Removes inaccessible fields from results
List<Account> accounts = [SELECT Id, Name, Phone, AnnualRevenue, SSN__c FROM Account];

SObjectAccessDecision decision = Security.stripInaccessible(
    AccessType.READABLE,
    accounts
);

List<Account> sanitizedAccounts = decision.getRecords();

// Check which fields were removed
Map<String, Set<String>> removedFields = decision.getRemovedFields();
if (!removedFields.isEmpty()) {
    System.debug('Fields removed due to FLS: ' + removedFields);
}
```

**Access Types**:
- `AccessType.READABLE` - Check read access
- `AccessType.CREATABLE` - Check create access
- `AccessType.UPDATABLE` - Check update access
- `AccessType.UPSERTABLE` - Check upsert access

**Pros**:
- Graceful degradation
- Returns as much data as user can see
- Good for flexible UIs

**Cons**:
- Silent removal (may hide security issues)
- Extra processing step

---

### Method 3: Manual Field Describe (Granular Control)

```apex
public with sharing class FieldAccessChecker {
    
    public static Boolean isFieldAccessible(String objectName, String fieldName) {
        Schema.SObjectType sObjType = Schema.getGlobalDescribe().get(objectName);
        if (sObjType == null) return false;
        
        Schema.SObjectField field = sObjType.getDescribe().fields.getMap().get(fieldName);
        if (field == null) return false;
        
        return field.getDescribe().isAccessible();
    }
    
    public static Boolean isFieldUpdateable(String objectName, String fieldName) {
        Schema.SObjectType sObjType = Schema.getGlobalDescribe().get(objectName);
        if (sObjType == null) return false;
        
        Schema.SObjectField field = sObjType.getDescribe().fields.getMap().get(fieldName);
        if (field == null) return false;
        
        return field.getDescribe().isUpdateable();
    }
    
    public static Boolean isFieldCreateable(String objectName, String fieldName) {
        Schema.SObjectType sObjType = Schema.getGlobalDescribe().get(objectName);
        if (sObjType == null) return false;
        
        Schema.SObjectField field = sObjType.getDescribe().fields.getMap().get(fieldName);
        if (field == null) return false;
        
        return field.getDescribe().isCreateable();
    }
    
    public static void enforceFieldAccess(
        String objectName, 
        List<String> fields, 
        AccessType accessType
    ) {
        List<String> inaccessibleFields = new List<String>();
        
        for (String fieldName : fields) {
            Boolean hasAccess = false;
            
            switch on accessType {
                when READABLE {
                    hasAccess = isFieldAccessible(objectName, fieldName);
                }
                when CREATABLE {
                    hasAccess = isFieldCreateable(objectName, fieldName);
                }
                when UPDATABLE {
                    hasAccess = isFieldUpdateable(objectName, fieldName);
                }
            }
            
            if (!hasAccess) {
                inaccessibleFields.add(fieldName);
            }
        }
        
        if (!inaccessibleFields.isEmpty()) {
            throw new SecurityException(
                'Insufficient field-level access for: ' + 
                String.join(inaccessibleFields, ', ')
            );
        }
    }
}
```

**Pros**:
- Maximum control
- Custom error handling
- Field-by-field decisions

**Cons**:
- Most verbose
- Must maintain manually
- Potential for mistakes

---

## Decision Matrix

| Scenario | Recommended Method |
|----------|-------------------|
| Standard SOQL query | `WITH SECURITY_ENFORCED` |
| Query with optional sensitive fields | `Security.stripInaccessible` |
| DML operations | Manual CRUD check + `stripInaccessible` |
| Dynamic queries | Manual FLS check per field |
| UI displaying optional fields | `stripInaccessible` + field visibility |
| API returning specific fields | `WITH SECURITY_ENFORCED` |
| Batch processing system data | Consider `without sharing` + justify |

---

## Complete Implementation Example

```apex
public with sharing class SecureAccountService {
    
    // READ - Using WITH SECURITY_ENFORCED
    public List<Account> getAccounts(Set<Id> ids) {
        return [
            SELECT Id, Name, Industry, Phone, AnnualRevenue
            FROM Account
            WHERE Id IN :ids
            WITH SECURITY_ENFORCED
        ];
    }
    
    // READ - Using stripInaccessible for flexibility
    public List<Account> getAccountsFlexible(Set<Id> ids) {
        List<Account> accounts = [
            SELECT Id, Name, Industry, Phone, AnnualRevenue, SSN__c, Salary__c
            FROM Account
            WHERE Id IN :ids
        ];
        
        return Security.stripInaccessible(AccessType.READABLE, accounts).getRecords();
    }
    
    // CREATE - Full security enforcement
    public Account createAccount(Account acc) {
        // 1. Check object-level CREATE permission
        if (!Schema.sObjectType.Account.isCreateable()) {
            throw new SecurityException('Cannot create Account');
        }
        
        // 2. Strip inaccessible fields from input
        SObjectAccessDecision decision = Security.stripInaccessible(
            AccessType.CREATABLE,
            new List<Account>{ acc }
        );
        Account sanitizedAcc = (Account) decision.getRecords()[0];
        
        // 3. Log removed fields
        Map<String, Set<String>> removed = decision.getRemovedFields();
        if (!removed.isEmpty()) {
            System.debug('Fields stripped due to FLS: ' + removed);
        }
        
        // 4. Insert
        insert sanitizedAcc;
        return sanitizedAcc;
    }
    
    // UPDATE - Full security enforcement
    public Account updateAccount(Account acc) {
        // 1. Check object-level UPDATE permission
        if (!Schema.sObjectType.Account.isUpdateable()) {
            throw new SecurityException('Cannot update Account');
        }
        
        // 2. Strip inaccessible fields
        SObjectAccessDecision decision = Security.stripInaccessible(
            AccessType.UPDATABLE,
            new List<Account>{ acc }
        );
        Account sanitizedAcc = (Account) decision.getRecords()[0];
        
        // 3. Update
        update sanitizedAcc;
        return sanitizedAcc;
    }
    
    // DELETE - Check permission
    public void deleteAccount(Id accountId) {
        if (!Schema.sObjectType.Account.isDeletable()) {
            throw new SecurityException('Cannot delete Account');
        }
        delete new Account(Id = accountId);
    }
}
```

---

## Testing FLS and CRUD

```apex
@IsTest
private class SecureAccountServiceTest {
    
    @IsTest
    static void testGetAccounts_WithAccess() {
        Account acc = new Account(Name = 'Test');
        insert acc;
        
        Test.startTest();
        List<Account> results = new SecureAccountService().getAccounts(
            new Set<Id>{ acc.Id }
        );
        Test.stopTest();
        
        System.assertEquals(1, results.size());
    }
    
    @IsTest
    static void testGetAccounts_NoAccess() {
        // Create user with no Account access
        User minimalUser = TestDataFactory.createMinimalUser();
        Account acc = new Account(Name = 'Test');
        insert acc;
        
        System.runAs(minimalUser) {
            Test.startTest();
            try {
                new SecureAccountService().getAccounts(new Set<Id>{ acc.Id });
                System.assert(false, 'Expected SecurityException');
            } catch (System.QueryException e) {
                // Expected - WITH SECURITY_ENFORCED throws QueryException
                System.assert(e.getMessage().contains('security'));
            }
            Test.stopTest();
        }
    }
    
    @IsTest
    static void testCreateAccount_FieldsStripped() {
        // Create user with Account create but no SSN field access
        User limitedUser = TestDataFactory.createUserWithoutSsnAccess();
        
        System.runAs(limitedUser) {
            Account acc = new Account(
                Name = 'Test',
                SSN__c = '123-45-6789' // User doesn't have FLS for this
            );
            
            Test.startTest();
            Account result = new SecureAccountService().createAccount(acc);
            Test.stopTest();
            
            // SSN should be stripped
            Account queried = [SELECT Id, Name, SSN__c FROM Account WHERE Id = :result.Id];
            System.assertEquals(null, queried.SSN__c, 'SSN should not be saved');
        }
    }
}
```

---

## Common Mistakes

### Mistake 1: Checking FLS After Query

```apex
// WRONG - Data already fetched before check
List<Account> accounts = [SELECT Id, SSN__c FROM Account];
if (!Schema.sObjectType.Account.fields.SSN__c.isAccessible()) {
    // Too late! SSN already in memory
}
```

### Mistake 2: Not Checking All Fields

```apex
// WRONG - Only checking one field
if (Schema.sObjectType.Account.fields.Name.isAccessible()) {
    // Query includes other fields without checks
    return [SELECT Id, Name, SSN__c, Salary__c FROM Account];
}
```

### Mistake 3: Using getGlobalDescribe in Loops

```apex
// WRONG - Performance issue
for (Account acc : accounts) {
    // getGlobalDescribe is expensive!
    if (Schema.getGlobalDescribe().get('Account').getDescribe()...) {
    }
}

// RIGHT - Cache the describe
Schema.DescribeSObjectResult accDescribe = Schema.sObjectType.Account;
for (Account acc : accounts) {
    if (accDescribe.fields.Name.getDescribe().isAccessible()) {
    }
}
```
