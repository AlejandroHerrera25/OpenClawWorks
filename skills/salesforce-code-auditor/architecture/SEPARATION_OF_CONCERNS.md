# Separation of Concerns — Architecture Guide

## Overview

Separation of Concerns (SoC) is a design principle for separating code into distinct sections, each handling a specific aspect of the application. In Salesforce, this translates to a layered architecture.

---

## The Layered Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                         UI Layer                                      │
│              (LWC, Aura, Visualforce, Flows)                          │
│     Responsibility: User interaction, display, input handling         │
└────────────────────────────────┬──────────────────────────────────┘
                                 │
                                 ▼
┌───────────────────────────────────────────────────────────────────┐
│                     Controller Layer                                  │
│              (Apex Controllers, REST Resources)                       │
│     Responsibility: Input validation, response formatting,            │
│                     authentication, authorization                     │
└────────────────────────────────┬──────────────────────────────────┘
                                 │
                                 ▼
┌───────────────────────────────────────────────────────────────────┐
│                      Service Layer                                    │
│              (Business Logic, Transaction Management)                 │
│     Responsibility: Business rules, orchestration, use cases          │
└───────────────┬──────────────────────────────────┬───────────────┘
                │                                  │
                ▼                                  ▼
┌───────────────────────────────┐  ┌───────────────────────────────┐
│       Domain Layer            │  │      Selector Layer            │
│   (Object-Specific Logic)     │  │   (Data Access/Queries)        │
│   - Validations               │  │   - SOQL queries                │
│   - Calculations              │  │   - Security enforcement        │
│   - Trigger handlers          │  │   - Field standardization       │
└───────────────────────────────┘  └───────────────────────────────┘
```

---

## Layer Responsibilities

### Controller Layer

**Purpose**: Handle HTTP requests, format responses, basic input validation.

**Should Do**:
- Receive input from UI or external systems
- Validate input format (not business rules)
- Call service layer
- Format response for UI consumption
- Handle authentication/authorization at API level

**Should NOT Do**:
- Contain business logic
- Execute SOQL queries directly
- Perform DML operations directly
- Know about database schema details

**Example**:
```apex
public with sharing class AccountController {
    
    @AuraEnabled(cacheable=true)
    public static List<AccountDTO> getAccounts(String industry) {
        // Validate input
        if (String.isBlank(industry)) {
            throw new AuraHandledException('Industry is required');
        }
        
        // Delegate to service
        List<Account> accounts = new AccountService().getAccountsByIndustry(industry);
        
        // Transform to DTO for UI
        List<AccountDTO> dtos = new List<AccountDTO>();
        for (Account acc : accounts) {
            dtos.add(new AccountDTO(acc));
        }
        return dtos;
    }
}
```

---

### Service Layer

**Purpose**: Orchestrate business operations, manage transactions.

**Should Do**:
- Implement business use cases
- Coordinate between domain and selector layers
- Manage transaction boundaries
- Handle complex business logic spanning multiple objects
- Call external integrations

**Should NOT Do**:
- Handle UI concerns
- Execute SOQL directly (use selectors)
- Know about HTTP request/response
- Contain object-specific validation (use domain)

**Example**:
```apex
public with sharing class AccountService {
    
    private AccountSelector accountSelector;
    private ContactSelector contactSelector;
    
    public AccountService() {
        this.accountSelector = new AccountSelector();
        this.contactSelector = new ContactSelector();
    }
    
    public void activateAccountsWithPrimaryContacts(Set<Id> accountIds) {
        // Get data through selectors
        List<Account> accounts = accountSelector.selectById(accountIds);
        
        // Apply domain logic
        Accounts domain = new Accounts(accounts);
        domain.validateForActivation();
        domain.activate();
        
        // Get related data
        List<Contact> primaryContacts = contactSelector.selectPrimaryByAccountId(accountIds);
        
        // Process related data
        Contacts contactDomain = new Contacts(primaryContacts);
        contactDomain.sendActivationNotification();
        
        // Single transaction for all updates
        update accounts;
    }
}
```

---

### Selector Layer

**Purpose**: Centralize all database queries.

**Should Do**:
- Execute SOQL/SOSL queries
- Enforce security (FLS, sharing)
- Return consistent field sets
- Provide query locators for batch processing

**Should NOT Do**:
- Contain business logic
- Perform DML operations
- Transform data for UI

**Example**:
```apex
public inherited sharing class AccountSelector {
    
    public List<Account> selectById(Set<Id> ids) {
        return [
            SELECT Id, Name, Industry, Status__c, AnnualRevenue
            FROM Account
            WHERE Id IN :ids
            WITH SECURITY_ENFORCED
        ];
    }
    
    public List<Account> selectByIndustry(String industry) {
        return [
            SELECT Id, Name, Industry, Status__c
            FROM Account
            WHERE Industry = :industry
            WITH SECURITY_ENFORCED
            ORDER BY Name
            LIMIT 1000
        ];
    }
    
    public Database.QueryLocator getQueryLocatorForBatch(String status) {
        return Database.getQueryLocator([
            SELECT Id, Name, Status__c
            FROM Account
            WHERE Status__c = :status
        ]);
    }
}
```

---

### Domain Layer

**Purpose**: Encapsulate object-specific business rules.

**Should Do**:
- Validate object data
- Calculate derived fields
- Enforce object-specific business rules
- Handle trigger logic

**Should NOT Do**:
- Execute queries (use selectors)
- Know about other objects' logic
- Handle UI concerns
- Manage transactions (use services)

**Example**:
```apex
public class Accounts {
    
    private List<Account> records;
    
    public Accounts(List<Account> records) {
        this.records = records;
    }
    
    public void validateForActivation() {
        for (Account acc : records) {
            if (String.isBlank(acc.Industry)) {
                throw new DomainException('Industry required for activation');
            }
            if (acc.AnnualRevenue == null || acc.AnnualRevenue <= 0) {
                throw new DomainException('Annual revenue required for activation');
            }
        }
    }
    
    public void activate() {
        for (Account acc : records) {
            acc.Status__c = 'Active';
            acc.Activated_Date__c = Date.today();
        }
    }
    
    public void setDefaults() {
        for (Account acc : records) {
            if (acc.Status__c == null) {
                acc.Status__c = 'New';
            }
            if (acc.Rating == null) {
                acc.Rating = 'Cold';
            }
        }
    }
    
    public class DomainException extends Exception {}
}
```

---

## Benefits of Separation

### 1. Testability

Each layer can be tested in isolation:

```apex
@IsTest
private class AccountServiceTest {
    
    @IsTest
    static void testActivateAccounts() {
        // Mock selector
        AccountSelectorMock mockSelector = new AccountSelectorMock();
        mockSelector.accounts = TestDataFactory.createAccounts(5, true);
        
        // Test service with mock
        AccountService service = new AccountService(mockSelector, new ContactSelectorMock());
        
        Test.startTest();
        service.activateAccountsWithPrimaryContacts(/* ids */);
        Test.stopTest();
        
        // Assert
        System.assert(mockSelector.wasSelectByIdCalled, 'Should query accounts');
    }
}
```

### 2. Reusability

Services can be called from multiple contexts:

```apex
// From LWC controller
public class AccountController {
    @AuraEnabled
    public static void activateSelected(List<Id> ids) {
        new AccountService().activateAccountsWithPrimaryContacts(new Set<Id>(ids));
    }
}

// From Trigger
public class AccountTriggerHandler {
    public void afterUpdate() {
        Set<Id> toActivate = getAccountsNeedingActivation();
        new AccountService().activateAccountsWithPrimaryContacts(toActivate);
    }
}

// From Batch
public class AccountActivationBatch implements Database.Batchable<SObject> {
    public void execute(Database.BatchableContext bc, List<Account> scope) {
        Set<Id> ids = new Map<Id, Account>(scope).keySet();
        new AccountService().activateAccountsWithPrimaryContacts(ids);
    }
}
```

### 3. Maintainability

Changes are localized:

- Query change → Update selector only
- Business rule change → Update service/domain only
- UI format change → Update controller only

---

## Anti-Patterns to Avoid

### God Controller
```apex
// BAD: Everything in controller
public class AccountController {
    @AuraEnabled
    public static void doEverything(String data) {
        // Parsing
        // Querying
        // Business logic
        // DML
        // Integration
        // Formatting
        // All in one method!
    }
}
```

### Cross-Layer Concerns
```apex
// BAD: Selector with business logic
public class AccountSelector {
    public List<Account> selectActiveHighValue() {
        List<Account> accounts = [SELECT Id FROM Account WHERE Status__c = 'Active'];
        
        // BAD: Business logic in selector
        List<Account> filtered = new List<Account>();
        for (Account acc : accounts) {
            if (acc.AnnualRevenue > 1000000) {
                filtered.add(acc);
            }
        }
        return filtered;
    }
}
```

### Service Calling Controller
```apex
// BAD: Wrong direction of dependency
public class AccountService {
    public void process() {
        // BAD: Service shouldn't know about controller
        AccountController controller = new AccountController();
        controller.formatOutput();
    }
}
```

---

## Migration Strategy

For existing codebases:

1. **Start with new code** - Apply patterns to new features
2. **Extract selectors first** - Move queries out of controllers/services
3. **Create services next** - Move business logic from controllers
4. **Introduce domain last** - Extract object-specific logic
5. **Refactor triggers** - Move to handler framework
