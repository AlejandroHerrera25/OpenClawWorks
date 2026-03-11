# Apex Best Practices — Complete Reference

## Overview

This document provides comprehensive best practices for Apex development, covering code structure, performance, security, and maintainability.

---

## Code Organization

### Separation of Concerns

```
┌─────────────────────────────────────────────────────────────┐
│                    Controller Layer                          │
│     (UI Controllers, REST Resources, Batch Entry Points)     │
│     - Handles input/output formatting                        │
│     - Invokes service layer                                  │
│     - No business logic                                      │
├─────────────────────────────────────────────────────────────┤
│                    Service Layer                             │
│     (Business Logic, Transaction Management)                 │
│     - Orchestrates operations                                │
│     - Manages transactions                                   │
│     - Calls selector and domain layers                       │
├─────────────────────────────────────────────────────────────┤
│                    Domain Layer                              │
│     (Business Rules, Validations, Calculations)              │
│     - Object-specific logic                                  │
│     - Trigger handlers                                       │
│     - Field derivations                                      │
├─────────────────────────────────────────────────────────────┤
│                    Selector Layer                            │
│     (Data Access, Queries)                                   │
│     - All SOQL queries                                       │
│     - Query optimization                                     │
│     - Security enforcement                                   │
└─────────────────────────────────────────────────────────────┘
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|----------|
| Class | PascalCase | `AccountService` |
| Interface | IPascalCase or PascalCaseInterface | `IAccountService` |
| Method | camelCase | `processAccounts()` |
| Variable | camelCase | `accountList` |
| Constant | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT` |
| Test Class | ClassNameTest | `AccountServiceTest` |
| Trigger | ObjectNameTrigger | `AccountTrigger` |
| Trigger Handler | ObjectNameTriggerHandler | `AccountTriggerHandler` |
| Selector | ObjectNameSelector | `AccountSelector` |
| Domain | ObjectNameDomain or ObjectNames | `Accounts` |
| DTO | ClassNameDTO | `AccountResponseDTO` |
| Exception | ClassNameException | `AccountServiceException` |

---

## Bulkification Patterns

### Collection-Based Processing

```apex
public class AccountProcessor {
    
    // CORRECT: Bulk-safe processing
    public void processAccounts(List<Account> accounts) {
        // Collect all required IDs
        Set<Id> accountIds = new Set<Id>();
        for (Account acc : accounts) {
            accountIds.add(acc.Id);
        }
        
        // Single query for all related data
        Map<Id, Account> accountsWithContacts = new Map<Id, Account>([
            SELECT Id, Name, 
                   (SELECT Id, Email FROM Contacts)
            FROM Account
            WHERE Id IN :accountIds
        ]);
        
        // Process with map lookup
        List<Task> tasksToCreate = new List<Task>();
        for (Account acc : accounts) {
            Account fullAccount = accountsWithContacts.get(acc.Id);
            if (fullAccount != null) {
                for (Contact con : fullAccount.Contacts) {
                    tasksToCreate.add(createFollowUpTask(con));
                }
            }
        }
        
        // Single DML for all records
        if (!tasksToCreate.isEmpty()) {
            insert tasksToCreate;
        }
    }
    
    private Task createFollowUpTask(Contact con) {
        return new Task(
            Subject = 'Follow up',
            WhoId = con.Id,
            ActivityDate = Date.today().addDays(7)
        );
    }
}
```

### Map-Based Lookups

```apex
// Build maps for efficient lookups
Map<String, Account> accountsByExternalId = new Map<String, Account>();
for (Account acc : [SELECT Id, External_Id__c FROM Account WHERE External_Id__c IN :externalIds]) {
    accountsByExternalId.put(acc.External_Id__c, acc);
}

// Use map instead of querying in loop
for (DataRecord rec : records) {
    Account acc = accountsByExternalId.get(rec.externalId);
    if (acc != null) {
        // Process
    }
}
```

---

## Trigger Best Practices

### Single Trigger Per Object

```apex
// AccountTrigger.trigger
trigger AccountTrigger on Account (before insert, before update, before delete,
                                   after insert, after update, after delete, after undelete) {
    new AccountTriggerHandler().run();
}
```

### Trigger Handler Framework

```apex
// TriggerHandler.cls - Base class
public virtual class TriggerHandler {
    
    // Static flag to prevent recursion
    private static Set<String> runningHandlers = new Set<String>();
    
    // Maximum recursion depth
    @TestVisible
    private static Integer maxRecursionDepth = 1;
    private static Map<String, Integer> recursionCount = new Map<String, Integer>();
    
    public void run() {
        String handlerName = getHandlerName();
        
        // Check recursion
        if (!shouldRun(handlerName)) {
            return;
        }
        
        incrementRecursion(handlerName);
        
        try {
            switch on Trigger.operationType {
                when BEFORE_INSERT { beforeInsert(Trigger.new); }
                when BEFORE_UPDATE { beforeUpdate(Trigger.new, Trigger.oldMap); }
                when BEFORE_DELETE { beforeDelete(Trigger.oldMap); }
                when AFTER_INSERT { afterInsert(Trigger.new); }
                when AFTER_UPDATE { afterUpdate(Trigger.new, Trigger.oldMap); }
                when AFTER_DELETE { afterDelete(Trigger.oldMap); }
                when AFTER_UNDELETE { afterUndelete(Trigger.new); }
            }
        } finally {
            decrementRecursion(handlerName);
        }
    }
    
    protected virtual String getHandlerName() {
        return String.valueOf(this).split(':')[0];
    }
    
    private Boolean shouldRun(String handlerName) {
        Integer count = recursionCount.get(handlerName);
        return count == null || count < maxRecursionDepth;
    }
    
    private void incrementRecursion(String handlerName) {
        Integer count = recursionCount.get(handlerName);
        recursionCount.put(handlerName, count == null ? 1 : count + 1);
    }
    
    private void decrementRecursion(String handlerName) {
        Integer count = recursionCount.get(handlerName);
        if (count != null && count > 0) {
            recursionCount.put(handlerName, count - 1);
        }
    }
    
    // Override in concrete handlers
    protected virtual void beforeInsert(List<SObject> newRecords) {}
    protected virtual void beforeUpdate(List<SObject> newRecords, Map<Id, SObject> oldMap) {}
    protected virtual void beforeDelete(Map<Id, SObject> oldMap) {}
    protected virtual void afterInsert(List<SObject> newRecords) {}
    protected virtual void afterUpdate(List<SObject> newRecords, Map<Id, SObject> oldMap) {}
    protected virtual void afterDelete(Map<Id, SObject> oldMap) {}
    protected virtual void afterUndelete(List<SObject> newRecords) {}
}
```

### Concrete Handler Implementation

```apex
// AccountTriggerHandler.cls
public class AccountTriggerHandler extends TriggerHandler {
    
    private List<Account> newAccounts;
    private Map<Id, Account> oldAccountsMap;
    
    public AccountTriggerHandler() {
        this.newAccounts = (List<Account>) Trigger.new;
        this.oldAccountsMap = (Map<Id, Account>) Trigger.oldMap;
    }
    
    protected override void beforeInsert(List<SObject> newRecords) {
        List<Account> accounts = (List<Account>) newRecords;
        setDefaults(accounts);
        validateAccounts(accounts);
    }
    
    protected override void beforeUpdate(List<SObject> newRecords, Map<Id, SObject> oldMap) {
        List<Account> accounts = (List<Account>) newRecords;
        Map<Id, Account> oldAccounts = (Map<Id, Account>) oldMap;
        validateAccountChanges(accounts, oldAccounts);
    }
    
    protected override void afterInsert(List<SObject> newRecords) {
        List<Account> accounts = (List<Account>) newRecords;
        createRelatedRecords(accounts);
        notifyExternalSystems(accounts);
    }
    
    protected override void afterUpdate(List<SObject> newRecords, Map<Id, SObject> oldMap) {
        List<Account> accounts = (List<Account>) newRecords;
        Map<Id, Account> oldAccounts = (Map<Id, Account>) oldMap;
        handleStatusChanges(accounts, oldAccounts);
    }
    
    // Private implementation methods
    private void setDefaults(List<Account> accounts) {
        for (Account acc : accounts) {
            if (acc.Rating == null) {
                acc.Rating = 'Cold';
            }
        }
    }
    
    private void validateAccounts(List<Account> accounts) {
        for (Account acc : accounts) {
            if (String.isBlank(acc.Name)) {
                acc.addError('Account name is required');
            }
        }
    }
    
    private void validateAccountChanges(List<Account> accounts, Map<Id, Account> oldMap) {
        for (Account acc : accounts) {
            Account oldAcc = oldMap.get(acc.Id);
            if (oldAcc.Status__c == 'Closed' && acc.Status__c != 'Closed') {
                acc.addError('Cannot reopen a closed account');
            }
        }
    }
    
    private void createRelatedRecords(List<Account> accounts) {
        // Bulk create related records
    }
    
    private void notifyExternalSystems(List<Account> accounts) {
        // Queue async notification
    }
    
    private void handleStatusChanges(List<Account> accounts, Map<Id, Account> oldMap) {
        List<Account> statusChanged = new List<Account>();
        for (Account acc : accounts) {
            if (acc.Status__c != oldMap.get(acc.Id).Status__c) {
                statusChanged.add(acc);
            }
        }
        if (!statusChanged.isEmpty()) {
            // Process status changes
        }
    }
}
```

---

## Service Layer Pattern

```apex
public with sharing class AccountService {
    
    private AccountSelector selector;
    
    public AccountService() {
        this.selector = new AccountSelector();
    }
    
    // Constructor injection for testing
    @TestVisible
    private AccountService(AccountSelector selector) {
        this.selector = selector;
    }
    
    public List<Account> getAccountsWithContacts(Set<Id> accountIds) {
        return selector.selectWithContacts(accountIds);
    }
    
    public void activateAccounts(Set<Id> accountIds) {
        List<Account> accounts = selector.selectById(accountIds);
        
        List<Account> toUpdate = new List<Account>();
        for (Account acc : accounts) {
            if (acc.Status__c != 'Active') {
                acc.Status__c = 'Active';
                acc.Activated_Date__c = Date.today();
                toUpdate.add(acc);
            }
        }
        
        if (!toUpdate.isEmpty()) {
            // Check CRUD
            if (!Schema.sObjectType.Account.isUpdateable()) {
                throw new SecurityException('Insufficient privileges');
            }
            update toUpdate;
        }
    }
    
    public AccountDTO createAccount(AccountDTO dto) {
        // Validate
        validateAccountDTO(dto);
        
        // Transform
        Account acc = dto.toSObject();
        
        // Check CRUD
        if (!Schema.sObjectType.Account.isCreateable()) {
            throw new SecurityException('Insufficient privileges');
        }
        
        // Persist
        insert acc;
        
        // Return
        return new AccountDTO(acc);
    }
    
    private void validateAccountDTO(AccountDTO dto) {
        if (String.isBlank(dto.name)) {
            throw new ValidationException('Account name is required');
        }
    }
    
    public class ValidationException extends Exception {}
}
```

---

## Selector Layer Pattern

```apex
public inherited sharing class AccountSelector {
    
    private static final List<Schema.SObjectField> FIELDS = new List<Schema.SObjectField>{
        Account.Id,
        Account.Name,
        Account.Status__c,
        Account.Industry,
        Account.AnnualRevenue
    };
    
    public List<Account> selectById(Set<Id> ids) {
        return [
            SELECT Id, Name, Status__c, Industry, AnnualRevenue
            FROM Account
            WHERE Id IN :ids
            WITH SECURITY_ENFORCED
        ];
    }
    
    public List<Account> selectWithContacts(Set<Id> ids) {
        return [
            SELECT Id, Name, Status__c,
                   (SELECT Id, FirstName, LastName, Email 
                    FROM Contacts
                    ORDER BY LastName)
            FROM Account
            WHERE Id IN :ids
            WITH SECURITY_ENFORCED
        ];
    }
    
    public List<Account> selectByIndustry(String industry) {
        return [
            SELECT Id, Name, Status__c, Industry, AnnualRevenue
            FROM Account
            WHERE Industry = :industry
            WITH SECURITY_ENFORCED
            ORDER BY Name
            LIMIT 1000
        ];
    }
    
    public List<Account> selectByExternalId(Set<String> externalIds) {
        return [
            SELECT Id, Name, External_Id__c
            FROM Account
            WHERE External_Id__c IN :externalIds
            WITH SECURITY_ENFORCED
        ];
    }
    
    public Database.QueryLocator getQueryLocatorForBatch() {
        return Database.getQueryLocator([
            SELECT Id, Name, Status__c
            FROM Account
            WHERE Status__c = 'Pending'
        ]);
    }
}
```

---

## Error Handling

### Custom Exception Hierarchy

```apex
// Base application exception
public virtual class ApplicationException extends Exception {
    public String errorCode { get; private set; }
    
    public ApplicationException(String message, String errorCode) {
        this(message);
        this.errorCode = errorCode;
    }
}

// Specific exception types
public class ValidationException extends ApplicationException {
    public List<String> validationErrors { get; private set; }
    
    public ValidationException(List<String> errors) {
        super('Validation failed: ' + String.join(errors, '; '), 'VALIDATION_ERROR');
        this.validationErrors = errors;
    }
}

public class IntegrationException extends ApplicationException {
    public Integer httpStatusCode { get; private set; }
    public String responseBody { get; private set; }
    
    public IntegrationException(String message, Integer statusCode, String response) {
        super(message, 'INTEGRATION_ERROR');
        this.httpStatusCode = statusCode;
        this.responseBody = response;
    }
}

public class SecurityException extends ApplicationException {
    public SecurityException(String message) {
        super(message, 'SECURITY_ERROR');
    }
}
```

### Error Handling in Services

```apex
public class OrderService {
    
    public OrderResult processOrder(OrderRequest request) {
        Savepoint sp = Database.setSavepoint();
        
        try {
            // Validate
            validateRequest(request);
            
            // Process
            Order order = createOrder(request);
            List<OrderItem> items = createOrderItems(order, request.items);
            
            // External callout
            String confirmationNumber = callInventorySystem(order);
            
            order.Confirmation_Number__c = confirmationNumber;
            update order;
            
            return new OrderResult(order, items, true, null);
            
        } catch (ValidationException e) {
            Database.rollback(sp);
            logError('Validation', e);
            return new OrderResult(null, null, false, e.validationErrors);
            
        } catch (IntegrationException e) {
            Database.rollback(sp);
            logError('Integration', e);
            // Return partial success or queue for retry
            return new OrderResult(null, null, false, new List<String>{e.getMessage()});
            
        } catch (Exception e) {
            Database.rollback(sp);
            logError('Unexpected', e);
            throw new ApplicationException('An unexpected error occurred', 'SYSTEM_ERROR');
        }
    }
    
    private void logError(String category, Exception e) {
        // Log to custom object or external system
        Error_Log__c log = new Error_Log__c(
            Category__c = category,
            Message__c = e.getMessage(),
            Stack_Trace__c = e.getStackTraceString(),
            Timestamp__c = Datetime.now()
        );
        insert log; // Consider async logging
    }
}
```

---

## Async Apex Patterns

### Queueable with Chaining

```apex
public class AccountProcessingQueueable implements Queueable, Database.AllowsCallouts {
    
    private List<Id> accountIds;
    private Integer retryCount;
    private static final Integer MAX_RETRIES = 3;
    
    public AccountProcessingQueueable(List<Id> accountIds) {
        this(accountIds, 0);
    }
    
    private AccountProcessingQueueable(List<Id> accountIds, Integer retryCount) {
        this.accountIds = accountIds;
        this.retryCount = retryCount;
    }
    
    public void execute(QueueableContext context) {
        try {
            // Process accounts
            processAccounts();
            
        } catch (CalloutException e) {
            // Retry on callout failures
            if (retryCount < MAX_RETRIES) {
                System.enqueueJob(new AccountProcessingQueueable(accountIds, retryCount + 1));
            } else {
                logFailure(e);
            }
        }
    }
    
    private void processAccounts() {
        // Implementation
    }
    
    private void logFailure(Exception e) {
        // Log failure after max retries
    }
}
```

### Batch Apex Pattern

```apex
public class AccountCleanupBatch implements Database.Batchable<SObject>, Database.Stateful, Database.AllowsCallouts {
    
    private Integer successCount = 0;
    private Integer failureCount = 0;
    private List<String> errors = new List<String>();
    
    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator([
            SELECT Id, Name, Status__c, Last_Activity_Date__c
            FROM Account
            WHERE Status__c = 'Inactive'
            AND Last_Activity_Date__c < :Date.today().addYears(-2)
        ]);
    }
    
    public void execute(Database.BatchableContext bc, List<Account> scope) {
        List<Account> toUpdate = new List<Account>();
        
        for (Account acc : scope) {
            acc.Status__c = 'Archived';
            acc.Archived_Date__c = Date.today();
            toUpdate.add(acc);
        }
        
        Database.SaveResult[] results = Database.update(toUpdate, false);
        
        for (Integer i = 0; i < results.size(); i++) {
            if (results[i].isSuccess()) {
                successCount++;
            } else {
                failureCount++;
                for (Database.Error err : results[i].getErrors()) {
                    errors.add(toUpdate[i].Id + ': ' + err.getMessage());
                }
            }
        }
    }
    
    public void finish(Database.BatchableContext bc) {
        // Send notification email
        Messaging.SingleEmailMessage mail = new Messaging.SingleEmailMessage();
        mail.setToAddresses(new String[]{'admin@company.com'});
        mail.setSubject('Account Cleanup Batch Complete');
        mail.setPlainTextBody(
            'Success: ' + successCount + '\n' +
            'Failures: ' + failureCount + '\n' +
            'Errors: ' + String.join(errors, '\n')
        );
        Messaging.sendEmail(new Messaging.SingleEmailMessage[]{mail});
    }
}
```

---

## Code Quality Checklist

- [ ] Classes follow single responsibility principle
- [ ] Methods are under 50 lines
- [ ] No hardcoded values (use Custom Labels, Custom Metadata, Custom Settings)
- [ ] All public methods have proper comments
- [ ] Error messages are user-friendly and logged for debugging
- [ ] Cyclomatic complexity is reasonable (< 10 per method)
- [ ] No dead code or commented-out code
- [ ] Consistent naming conventions
- [ ] No magic numbers or strings
- [ ] DRY principle followed (no duplicated logic)
