# Anti-Patterns Catalog — Complete Reference

## Overview

This document catalogs common anti-patterns found in Salesforce development that indicate code quality, security, performance, or architecture issues.

---

## Performance Anti-Patterns

### PERF-001: SOQL in Loop

**Severity**: CRITICAL
**Category**: Governor Limits
**Impact**: Transaction failure due to SOQL limit (100 queries)

**Pattern**:
```apex
// ANTI-PATTERN
for (Account acc : accounts) {
    List<Contact> contacts = [SELECT Id FROM Contact WHERE AccountId = :acc.Id];
}
```

**Solution**:
```apex
// CORRECT PATTERN
Map<Id, List<Contact>> contactsByAccount = new Map<Id, List<Contact>>();
Set<Id> accountIds = new Map<Id, Account>(accounts).keySet();

for (Contact c : [SELECT Id, AccountId FROM Contact WHERE AccountId IN :accountIds]) {
    if (!contactsByAccount.containsKey(c.AccountId)) {
        contactsByAccount.put(c.AccountId, new List<Contact>());
    }
    contactsByAccount.get(c.AccountId).add(c);
}

for (Account acc : accounts) {
    List<Contact> contacts = contactsByAccount.get(acc.Id);
    // Process
}
```

**Detection**: Look for `[SELECT` inside `for`, `while`, `do` blocks

---

### PERF-002: DML in Loop

**Severity**: CRITICAL
**Category**: Governor Limits
**Impact**: Transaction failure due to DML limit (150 statements)

**Pattern**:
```apex
// ANTI-PATTERN
for (Account acc : accounts) {
    acc.Status__c = 'Processed';
    update acc;
}
```

**Solution**:
```apex
// CORRECT PATTERN
List<Account> toUpdate = new List<Account>();
for (Account acc : accounts) {
    acc.Status__c = 'Processed';
    toUpdate.add(acc);
}
if (!toUpdate.isEmpty()) {
    update toUpdate;
}
```

**Detection**: Look for `insert`, `update`, `delete`, `upsert` inside loops

---

### PERF-003: Callout in Loop

**Severity**: CRITICAL
**Category**: Governor Limits
**Impact**: Transaction failure, poor performance

**Pattern**:
```apex
// ANTI-PATTERN
for (Account acc : accounts) {
    HttpRequest req = new HttpRequest();
    req.setEndpoint('callout:External/api/' + acc.Id);
    Http http = new Http();
    HttpResponse res = http.send(req);
}
```

**Solution**:
```apex
// CORRECT PATTERN - Batch callouts or single bulk request
public class AccountCalloutQueueable implements Queueable, Database.AllowsCallouts {
    private List<Account> accounts;
    
    public void execute(QueueableContext context) {
        // Make callout for batch of accounts
    }
}
```

---

### PERF-004: Unbounded Query

**Severity**: HIGH
**Category**: Governor Limits / LDV
**Impact**: Query timeout, excessive heap usage

**Pattern**:
```apex
// ANTI-PATTERN
List<Account> allAccounts = [SELECT Id, Name FROM Account];
// or
List<Account> accounts = [SELECT Id, Name FROM Account WHERE Industry = :industry];
// Without LIMIT on non-selective query
```

**Solution**:
```apex
// CORRECT PATTERN
List<Account> accounts = [
    SELECT Id, Name 
    FROM Account 
    WHERE Industry = :industry
    AND CreatedDate >= :startDate
    LIMIT 10000
];
```

---

### PERF-005: Non-Selective Query

**Severity**: HIGH
**Category**: LDV
**Impact**: Query timeout on large tables

**Pattern**:
```apex
// ANTI-PATTERN - Non-indexed field
List<Account> accounts = [SELECT Id FROM Account WHERE Custom_Text__c = :value];

// ANTI-PATTERN - Negative filter
List<Account> accounts = [SELECT Id FROM Account WHERE Status__c != 'Closed'];

// ANTI-PATTERN - Leading wildcard
List<Account> accounts = [SELECT Id FROM Account WHERE Name LIKE '%Corp'];
```

**Solution**:
- Request custom index on frequently filtered fields
- Avoid negative filters on large tables
- Use trailing wildcards only: `LIKE 'Corp%'`

---

### PERF-006: Synchronous Callout in Trigger

**Severity**: HIGH
**Category**: Architecture / Performance
**Impact**: Transaction failure, poor user experience

**Pattern**:
```apex
// ANTI-PATTERN - Direct callout in trigger
trigger AccountTrigger on Account (after insert) {
    for (Account acc : Trigger.new) {
        Http http = new Http();
        // This will fail - callouts not allowed in triggers
    }
}
```

**Solution**:
```apex
// CORRECT PATTERN - Async callout
trigger AccountTrigger on Account (after insert) {
    AccountIntegrationService.syncAccountsAsync(Trigger.newMap.keySet());
}

public class AccountIntegrationService {
    @future(callout=true)
    public static void syncAccountsAsync(Set<Id> accountIds) {
        // Make callouts
    }
}
```

---

## Security Anti-Patterns

### SEC-001: SOQL Injection

**Severity**: CRITICAL
**Category**: Security
**Impact**: Data breach, unauthorized data access

**Pattern**:
```apex
// ANTI-PATTERN - Direct concatenation
String query = 'SELECT Id FROM Account WHERE Name = \'' + userInput + '\'';
List<Account> accounts = Database.query(query);
```

**Attack Vector**:
```
userInput = "' OR Name != '"
Resulting query: SELECT Id FROM Account WHERE Name = '' OR Name != ''
// Returns ALL accounts!
```

**Solution**:
```apex
// CORRECT PATTERN - Bind variable
String searchTerm = userInput;
List<Account> accounts = [SELECT Id FROM Account WHERE Name = :searchTerm];

// CORRECT PATTERN - Escape if dynamic query needed
String safeTerm = String.escapeSingleQuotes(userInput);
String query = 'SELECT Id FROM Account WHERE Name = \'' + safeTerm + '\'';
```

---

### SEC-002: Missing FLS Check

**Severity**: HIGH
**Category**: Security
**Impact**: Unauthorized field access

**Pattern**:
```apex
// ANTI-PATTERN - No FLS check
List<Account> accounts = [SELECT Id, Name, AnnualRevenue, Secret_Field__c FROM Account];
return accounts; // Returns all fields regardless of user permissions
```

**Solution**:
```apex
// CORRECT PATTERN - WITH SECURITY_ENFORCED
List<Account> accounts = [
    SELECT Id, Name, AnnualRevenue, Secret_Field__c 
    FROM Account
    WITH SECURITY_ENFORCED
];

// CORRECT PATTERN - stripInaccessible
List<Account> accounts = [SELECT Id, Name, AnnualRevenue, Secret_Field__c FROM Account];
return Security.stripInaccessible(AccessType.READABLE, accounts).getRecords();
```

---

### SEC-003: Missing CRUD Check

**Severity**: HIGH
**Category**: Security
**Impact**: Unauthorized DML operations

**Pattern**:
```apex
// ANTI-PATTERN - No CRUD check
public void createAccount(Account acc) {
    insert acc; // No permission check
}
```

**Solution**:
```apex
// CORRECT PATTERN
public void createAccount(Account acc) {
    if (!Schema.sObjectType.Account.isCreateable()) {
        throw new SecurityException('Insufficient privileges to create Account');
    }
    insert acc;
}
```

---

### SEC-004: Hardcoded Credentials

**Severity**: CRITICAL
**Category**: Security
**Impact**: Credential exposure, security breach

**Pattern**:
```apex
// ANTI-PATTERN - Credentials in code
HttpRequest req = new HttpRequest();
req.setHeader('Authorization', 'Bearer sk_live_abc123xyz');
req.setHeader('X-API-Key', 'secret_key_12345');
```

**Solution**:
```apex
// CORRECT PATTERN - Named Credentials
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:MyNamedCredential/api/endpoint');
// Authentication handled automatically

// CORRECT PATTERN - Protected Custom Setting
String apiKey = Integration_Settings__c.getOrgDefaults().API_Key__c;
```

---

### SEC-005: XSS Vulnerability

**Severity**: HIGH
**Category**: Security
**Impact**: Script injection, session hijacking

**Pattern (Visualforce)**:
```html
<!-- ANTI-PATTERN - No encoding -->
<apex:outputText value="{!userInput}" escape="false"/>
<script>var data = '{!userInput}';</script>
```

**Pattern (LWC)**:
```javascript
// ANTI-PATTERN - innerHTML with user data
this.template.querySelector('div').innerHTML = userInput;
```

**Solution (Visualforce)**:
```html
<!-- CORRECT PATTERN -->
<apex:outputText value="{!userInput}" escape="true"/>
<script>var data = '{!JSENCODE(userInput)}';</script>
```

**Solution (LWC)**:
```javascript
// CORRECT PATTERN - Use data binding
// Template: {sanitizedContent}
// Locker Service handles escaping
```

---

### SEC-006: Missing Sharing Declaration

**Severity**: HIGH
**Category**: Security
**Impact**: Unauthorized record access

**Pattern**:
```apex
// ANTI-PATTERN - No sharing keyword (defaults vary by context)
public class AccountService {
    public List<Account> getAccounts() {
        return [SELECT Id, Name FROM Account];
    }
}
```

**Solution**:
```apex
// CORRECT PATTERN - Explicit sharing
public with sharing class AccountService {
    public List<Account> getAccounts() {
        return [SELECT Id, Name FROM Account];
    }
}

// For utility classes
public inherited sharing class AccountUtils {
    // Inherits from calling context
}
```

---

## Architecture Anti-Patterns

### ARCH-001: God Class

**Severity**: HIGH
**Category**: Maintainability
**Impact**: Difficult to test, maintain, and understand

**Pattern**:
```apex
// ANTI-PATTERN - Class does too much
public class AccountManager {
    // Hundreds of lines...
    public void createAccount() { }
    public void updateAccount() { }
    public void deleteAccount() { }
    public void sendEmail() { }
    public void callExternalSystem() { }
    public void generateReport() { }
    public void processPayment() { }
    // ... 50+ methods
}
```

**Solution**:
```apex
// CORRECT PATTERN - Single Responsibility
public class AccountService { /* Account operations */ }
public class AccountEmailService { /* Email operations */ }
public class AccountIntegrationService { /* Integration operations */ }
public class AccountReportService { /* Reporting operations */ }
public class PaymentService { /* Payment operations */ }
```

---

### ARCH-002: Business Logic in Trigger

**Severity**: HIGH
**Category**: Maintainability
**Impact**: Difficult to test, reuse, and maintain

**Pattern**:
```apex
// ANTI-PATTERN - Logic in trigger body
trigger AccountTrigger on Account (before insert, after insert) {
    if (Trigger.isBefore && Trigger.isInsert) {
        for (Account acc : Trigger.new) {
            if (acc.Industry == 'Technology') {
                acc.Priority__c = 'High';
            }
            // More logic...
        }
    }
    if (Trigger.isAfter && Trigger.isInsert) {
        List<Task> tasks = new List<Task>();
        // More logic...
    }
}
```

**Solution**:
```apex
// CORRECT PATTERN - Delegate to handler
trigger AccountTrigger on Account (before insert, after insert) {
    new AccountTriggerHandler().run();
}

public class AccountTriggerHandler extends TriggerHandler {
    protected override void beforeInsert() {
        setPriorities((List<Account>) Trigger.new);
    }
    
    protected override void afterInsert() {
        createFollowUpTasks((List<Account>) Trigger.new);
    }
}
```

---

### ARCH-003: Circular Dependency

**Severity**: CRITICAL
**Category**: Architecture
**Impact**: Runtime errors, deployment failures

**Pattern**:
```apex
// ANTI-PATTERN - Circular dependency
public class ClassA {
    public void methodA() {
        ClassB b = new ClassB();
        b.methodB();
    }
}

public class ClassB {
    public void methodB() {
        ClassA a = new ClassA();
        a.methodA(); // Creates circular dependency!
    }
}
```

**Solution**:
- Extract common logic to third class
- Use interfaces and dependency injection
- Restructure to eliminate bidirectional dependency

---

### ARCH-004: Multiple Triggers on Object

**Severity**: HIGH
**Category**: Architecture
**Impact**: Non-deterministic execution, debugging difficulty

**Pattern**:
```apex
// ANTI-PATTERN - Multiple triggers
trigger AccountTrigger1 on Account (before insert) {
    // Logic 1
}

trigger AccountTrigger2 on Account (before insert) {
    // Logic 2 - Order is NOT guaranteed!
}
```

**Solution**:
```apex
// CORRECT PATTERN - Single trigger
trigger AccountTrigger on Account (before insert, after insert, before update, after update) {
    new AccountTriggerHandler().run();
}
```

---

### ARCH-005: Mixed Concerns in Controller

**Severity**: MEDIUM
**Category**: Architecture
**Impact**: Poor testability, code duplication

**Pattern**:
```apex
// ANTI-PATTERN - Everything in controller
public class AccountController {
    @AuraEnabled
    public static Account getAccount(Id accountId) {
        // Query logic
        Account acc = [SELECT Id, Name, 
            (SELECT Id FROM Contacts), 
            (SELECT Id FROM Opportunities)
            FROM Account WHERE Id = :accountId];
        
        // Business logic
        if (acc.Contacts.size() > 10) {
            acc.Type = 'Enterprise';
            update acc;
        }
        
        // Integration logic
        Http http = new Http();
        // Callout...
        
        return acc;
    }
}
```

**Solution**:
```apex
// CORRECT PATTERN - Separation of concerns
public class AccountController {
    @AuraEnabled
    public static Account getAccount(Id accountId) {
        return new AccountService().getAccountWithDetails(accountId);
    }
}

public class AccountService {
    private AccountSelector selector = new AccountSelector();
    
    public Account getAccountWithDetails(Id accountId) {
        Account acc = selector.selectWithRelated(accountId);
        processAccountType(acc);
        return acc;
    }
}

public class AccountSelector {
    public Account selectWithRelated(Id accountId) {
        return [
            SELECT Id, Name, (SELECT Id FROM Contacts)
            FROM Account WHERE Id = :accountId
            WITH SECURITY_ENFORCED
        ];
    }
}
```

---

## Test Anti-Patterns

### TEST-001: No Assertions

**Severity**: HIGH
**Category**: Test Quality
**Impact**: False positive test coverage

**Pattern**:
```apex
// ANTI-PATTERN - No assertions
@IsTest
static void testCreateAccount() {
    Account acc = new Account(Name = 'Test');
    insert acc;
    // Test passes without verifying anything!
}
```

**Solution**:
```apex
// CORRECT PATTERN - Meaningful assertions
@IsTest
static void testCreateAccount() {
    Account acc = new Account(Name = 'Test');
    insert acc;
    
    System.assertNotEquals(null, acc.Id, 'Account should have Id after insert');
    
    Account queried = [SELECT Id, Name FROM Account WHERE Id = :acc.Id];
    System.assertEquals('Test', queried.Name, 'Account name should match');
}
```

---

### TEST-002: Hardcoded IDs

**Severity**: HIGH
**Category**: Test Quality
**Impact**: Tests fail in different orgs

**Pattern**:
```apex
// ANTI-PATTERN - Hardcoded ID
@IsTest
static void testUpdateAccount() {
    Account acc = [SELECT Id FROM Account WHERE Id = '001000000000001'];
    // This fails in any org without this specific record!
}
```

**Solution**:
```apex
// CORRECT PATTERN - Create test data
@IsTest
static void testUpdateAccount() {
    Account acc = TestDataFactory.createAccount(true);
    // Use dynamically created test data
}
```

---

### TEST-003: SeeAllData=true

**Severity**: MEDIUM
**Category**: Test Quality
**Impact**: Non-deterministic tests, org dependency

**Pattern**:
```apex
// ANTI-PATTERN - SeeAllData
@IsTest(seeAllData=true)
private class AccountServiceTest {
    // Tests depend on org data - unreliable!
}
```

**Solution**:
```apex
// CORRECT PATTERN - Create all test data
@IsTest
private class AccountServiceTest {
    @TestSetup
    static void setup() {
        // Create all required test data
    }
}
```

---

### TEST-004: No Bulk Testing

**Severity**: HIGH
**Category**: Test Quality
**Impact**: Code fails in production with bulk data

**Pattern**:
```apex
// ANTI-PATTERN - Single record test
@IsTest
static void testTrigger() {
    Account acc = new Account(Name = 'Test');
    insert acc;
    // Only tests single record - misses bulk issues!
}
```

**Solution**:
```apex
// CORRECT PATTERN - Bulk test
@IsTest
static void testTrigger_Bulk() {
    List<Account> accounts = TestDataFactory.createAccounts(200, false);
    
    Test.startTest();
    insert accounts; // Tests bulk operation
    Test.stopTest();
    
    List<Account> inserted = [SELECT Id, Status__c FROM Account WHERE Id IN :accounts];
    System.assertEquals(200, inserted.size(), 'All accounts should be inserted');
}
```

---

## Code Quality Anti-Patterns

### QUAL-001: Magic Numbers

**Severity**: LOW
**Category**: Maintainability
**Impact**: Unclear code, difficult maintenance

**Pattern**:
```apex
// ANTI-PATTERN
if (account.AnnualRevenue > 1000000) {
    account.Type = 'Enterprise';
} else if (account.AnnualRevenue > 100000) {
    account.Type = 'Mid-Market';
}
```

**Solution**:
```apex
// CORRECT PATTERN - Named constants
private static final Decimal ENTERPRISE_THRESHOLD = 1000000;
private static final Decimal MIDMARKET_THRESHOLD = 100000;

if (account.AnnualRevenue > ENTERPRISE_THRESHOLD) {
    account.Type = 'Enterprise';
} else if (account.AnnualRevenue > MIDMARKET_THRESHOLD) {
    account.Type = 'Mid-Market';
}
```

---

### QUAL-002: Deep Nesting

**Severity**: MEDIUM
**Category**: Maintainability
**Impact**: Hard to read and maintain

**Pattern**:
```apex
// ANTI-PATTERN - Deep nesting
if (account != null) {
    if (account.Industry == 'Technology') {
        if (account.AnnualRevenue != null) {
            if (account.AnnualRevenue > 1000000) {
                if (account.NumberOfEmployees > 100) {
                    // Finally do something
                }
            }
        }
    }
}
```

**Solution**:
```apex
// CORRECT PATTERN - Early returns
if (account == null) return;
if (account.Industry != 'Technology') return;
if (account.AnnualRevenue == null || account.AnnualRevenue <= 1000000) return;
if (account.NumberOfEmployees == null || account.NumberOfEmployees <= 100) return;

// Do something with qualified account
```

---

### QUAL-003: Dead Code

**Severity**: LOW
**Category**: Maintainability
**Impact**: Confusion, increased complexity

**Pattern**:
```apex
// ANTI-PATTERN - Unreachable/unused code
public class AccountService {
    public void processAccount(Account acc) {
        // Active code
    }
    
    // Old method - never called
    public void processAccountOld(Account acc) {
        // Dead code
    }
    
    /*
    public void commentedOutMethod() {
        // More dead code
    }
    */
}
```

**Solution**: Remove dead code, use version control for history

---

### QUAL-004: Long Method

**Severity**: MEDIUM
**Category**: Maintainability
**Impact**: Hard to understand, test, and maintain

**Pattern**:
```apex
// ANTI-PATTERN - Method with 200+ lines
public void processAccounts(List<Account> accounts) {
    // Lines 1-50: Validation
    // Lines 51-100: Data retrieval
    // Lines 101-150: Business logic
    // Lines 151-200: DML operations
    // Lines 201-250: Notifications
}
```

**Solution**:
```apex
// CORRECT PATTERN - Extracted methods
public void processAccounts(List<Account> accounts) {
    validateAccounts(accounts);
    Map<Id, RelatedData> data = retrieveRelatedData(accounts);
    List<Account> processed = applyBusinessLogic(accounts, data);
    saveAccounts(processed);
    sendNotifications(processed);
}
```
