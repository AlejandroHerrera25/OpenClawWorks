# Bulkification Guide

## Overview

Bulkification is the practice of designing code to handle multiple records efficiently. This is critical in Salesforce due to governor limits and the multi-tenant architecture.

---

## Why Bulkification Matters

### Governor Limits Context

| Limit | Value | Why It Matters |
|-------|-------|---------------|
| SOQL Queries | 100 | 1 query per record = fail at 100 records |
| DML Statements | 150 | 1 DML per record = fail at 150 records |
| Query Rows | 50,000 | Unbounded queries can hit this limit |
| CPU Time | 10,000ms | Inefficient loops consume CPU |

### Real-World Impact

- **Data Loader**: Processes 200 records per batch
- **Bulk API**: Can send thousands of records
- **Triggers**: Fire on up to 200 records at once
- **Flows**: Can process bulk operations

---

## Core Bulkification Patterns

### Pattern 1: Query Outside Loops

**Anti-Pattern**:
```apex
// FAILS at 100 accounts
for (Account acc : accounts) {
    List<Contact> contacts = [
        SELECT Id FROM Contact WHERE AccountId = :acc.Id
    ];
    processContacts(contacts);
}
```

**Bulkified**:
```apex
// Works for any number of accounts
Set<Id> accountIds = new Map<Id, Account>(accounts).keySet();

Map<Id, List<Contact>> contactsByAccountId = new Map<Id, List<Contact>>();
for (Contact c : [
    SELECT Id, AccountId 
    FROM Contact 
    WHERE AccountId IN :accountIds
]) {
    if (!contactsByAccountId.containsKey(c.AccountId)) {
        contactsByAccountId.put(c.AccountId, new List<Contact>());
    }
    contactsByAccountId.get(c.AccountId).add(c);
}

for (Account acc : accounts) {
    List<Contact> contacts = contactsByAccountId.get(acc.Id);
    if (contacts != null) {
        processContacts(contacts);
    }
}
```

---

### Pattern 2: Collect-Then-DML

**Anti-Pattern**:
```apex
// FAILS at 150 accounts
for (Account acc : accounts) {
    acc.Status__c = 'Processed';
    update acc;
}
```

**Bulkified**:
```apex
// Works for any number of accounts
for (Account acc : accounts) {
    acc.Status__c = 'Processed';
}
update accounts; // Single DML for all records
```

**With Conditional Updates**:
```apex
List<Account> accountsToUpdate = new List<Account>();

for (Account acc : accounts) {
    if (acc.Status__c != 'Processed') {
        acc.Status__c = 'Processed';
        accountsToUpdate.add(acc);
    }
}

if (!accountsToUpdate.isEmpty()) {
    update accountsToUpdate;
}
```

---

### Pattern 3: Map-Based Lookups

**Anti-Pattern**:
```apex
// Linear search - O(n²) complexity
for (Contact con : contacts) {
    for (Account acc : accounts) {
        if (con.AccountId == acc.Id) {
            processMatch(con, acc);
            break;
        }
    }
}
```

**Bulkified**:
```apex
// Map lookup - O(n) complexity
Map<Id, Account> accountMap = new Map<Id, Account>(accounts);

for (Contact con : contacts) {
    Account acc = accountMap.get(con.AccountId);
    if (acc != null) {
        processMatch(con, acc);
    }
}
```

---

### Pattern 4: Set-Based Filtering

**Anti-Pattern**:
```apex
// Inefficient filtering
List<Contact> filtered = new List<Contact>();
for (Contact con : contacts) {
    Boolean found = false;
    for (Id accId : targetAccountIds) {
        if (con.AccountId == accId) {
            found = true;
            break;
        }
    }
    if (found) {
        filtered.add(con);
    }
}
```

**Bulkified**:
```apex
// Set-based filtering - O(1) lookup
Set<Id> targetAccountIdSet = new Set<Id>(targetAccountIds);

List<Contact> filtered = new List<Contact>();
for (Contact con : contacts) {
    if (targetAccountIdSet.contains(con.AccountId)) {
        filtered.add(con);
    }
}
```

---

### Pattern 5: Relationship Queries

**Anti-Pattern**:
```apex
// Two separate queries
List<Account> accounts = [SELECT Id, Name FROM Account WHERE Id IN :accountIds];
List<Contact> contacts = [SELECT Id, AccountId FROM Contact WHERE AccountId IN :accountIds];
// Then manually associate
```

**Bulkified**:
```apex
// Single query with relationship
List<Account> accountsWithContacts = [
    SELECT Id, Name,
           (SELECT Id, FirstName, LastName FROM Contacts)
    FROM Account
    WHERE Id IN :accountIds
];

for (Account acc : accountsWithContacts) {
    for (Contact con : acc.Contacts) {
        // Process contact in context of account
    }
}
```

---

## Trigger Bulkification

### Complete Trigger Handler Pattern

```apex
public class AccountTriggerHandler extends TriggerHandler {
    
    private List<Account> newAccounts;
    private Map<Id, Account> oldAccountsMap;
    
    public AccountTriggerHandler() {
        this.newAccounts = (List<Account>) Trigger.new;
        this.oldAccountsMap = (Map<Id, Account>) Trigger.oldMap;
    }
    
    protected override void afterInsert() {
        // Bulk-safe: collect all IDs first
        Set<Id> accountIds = new Map<Id, Account>(newAccounts).keySet();
        
        // Bulk-safe: single query for all related data
        Map<Id, Integer> opportunityCounts = getOpportunityCounts(accountIds);
        
        // Bulk-safe: collect updates
        List<Account> accountsToUpdate = new List<Account>();
        
        for (Account acc : newAccounts) {
            Integer oppCount = opportunityCounts.get(acc.Id);
            if (oppCount != null && oppCount > 5) {
                accountsToUpdate.add(new Account(
                    Id = acc.Id,
                    High_Value__c = true
                ));
            }
        }
        
        // Bulk-safe: single DML
        if (!accountsToUpdate.isEmpty()) {
            update accountsToUpdate;
        }
    }
    
    private Map<Id, Integer> getOpportunityCounts(Set<Id> accountIds) {
        Map<Id, Integer> counts = new Map<Id, Integer>();
        
        for (AggregateResult ar : [
            SELECT AccountId, COUNT(Id) cnt
            FROM Opportunity
            WHERE AccountId IN :accountIds
            GROUP BY AccountId
        ]) {
            counts.put((Id)ar.get('AccountId'), (Integer)ar.get('cnt'));
        }
        
        return counts;
    }
}
```

---

## Service Layer Bulkification

### Bulk-Safe Service Methods

```apex
public with sharing class AccountService {
    
    private AccountSelector selector;
    
    public AccountService() {
        this.selector = new AccountSelector();
    }
    
    /**
     * Process multiple accounts in a single call
     * Bulk-safe: designed for 1 to 10,000+ records
     */
    public void activateAccounts(Set<Id> accountIds) {
        if (accountIds == null || accountIds.isEmpty()) {
            return; // Early exit for empty input
        }
        
        // Bulk query
        List<Account> accounts = selector.selectById(accountIds);
        
        // Bulk process
        List<Account> toUpdate = new List<Account>();
        for (Account acc : accounts) {
            if (acc.Status__c != 'Active') {
                toUpdate.add(new Account(
                    Id = acc.Id,
                    Status__c = 'Active',
                    Activated_Date__c = Date.today()
                ));
            }
        }
        
        // Bulk DML
        if (!toUpdate.isEmpty()) {
            update toUpdate;
        }
    }
    
    /**
     * Create accounts with related contacts
     * Uses Unit of Work pattern for bulk safety
     */
    public void createAccountsWithContacts(List<AccountDTO> dtos) {
        if (dtos == null || dtos.isEmpty()) {
            return;
        }
        
        // Prepare bulk collections
        List<Account> accountsToInsert = new List<Account>();
        Map<Integer, List<Contact>> contactsByIndex = new Map<Integer, List<Contact>>();
        
        for (Integer i = 0; i < dtos.size(); i++) {
            AccountDTO dto = dtos[i];
            
            Account acc = new Account(
                Name = dto.name,
                Industry = dto.industry
            );
            accountsToInsert.add(acc);
            
            if (dto.contacts != null && !dto.contacts.isEmpty()) {
                List<Contact> contacts = new List<Contact>();
                for (ContactDTO conDto : dto.contacts) {
                    contacts.add(new Contact(
                        FirstName = conDto.firstName,
                        LastName = conDto.lastName
                    ));
                }
                contactsByIndex.put(i, contacts);
            }
        }
        
        // Bulk insert accounts
        insert accountsToInsert;
        
        // Associate contacts with accounts and bulk insert
        List<Contact> contactsToInsert = new List<Contact>();
        for (Integer i = 0; i < accountsToInsert.size(); i++) {
            List<Contact> contacts = contactsByIndex.get(i);
            if (contacts != null) {
                for (Contact con : contacts) {
                    con.AccountId = accountsToInsert[i].Id;
                    contactsToInsert.add(con);
                }
            }
        }
        
        if (!contactsToInsert.isEmpty()) {
            insert contactsToInsert;
        }
    }
}
```

---

## Bulkification Checklist

### Before Writing Code
- [ ] Method accepts collection, not single record
- [ ] Returns collection when appropriate
- [ ] Handles empty input gracefully

### Query Patterns
- [ ] All queries outside loops
- [ ] Using IN clause for bulk filtering
- [ ] Using relationship queries when appropriate
- [ ] Using aggregate queries for counts/sums

### DML Patterns
- [ ] All DML outside loops
- [ ] Using collections for bulk DML
- [ ] Early exit for empty collections
- [ ] Partial success handling considered

### Data Structures
- [ ] Maps for lookups
- [ ] Sets for membership tests
- [ ] Lists for ordered processing
- [ ] Proper null handling

### Testing
- [ ] Tested with 1 record
- [ ] Tested with 200+ records
- [ ] No governor limit exceptions
- [ ] Performance acceptable at scale
