# Query Optimization Guide

## Overview

Efficient SOQL queries are critical for Salesforce application performance, especially in Large Data Volume (LDV) environments. This guide provides comprehensive optimization techniques.

---

## Query Selectivity

### What is Selectivity?

A query is **selective** when it can efficiently use an index to find records. Non-selective queries perform full table scans, which fail on large tables.

### Selectivity Thresholds

| Filter Type | Threshold |
|-------------|----------|
| Standard indexed field | < 30% of total records |
| Custom indexed field | < 30% of total records |
| Non-indexed field | < 10% of total records (or 333,333 records) |

### Indexed Fields (Always Selective When Filtered)

- `Id`
- `Name`
- `OwnerId`
- `CreatedDate`
- `LastModifiedDate`
- `SystemModstamp`
- `RecordTypeId`
- `CreatedById`
- `LastModifiedById`
- Lookup fields (relationship fields)
- Master-Detail fields
- External ID fields (custom fields marked as External ID)
- Unique fields

---

## Non-Selective Patterns to Avoid

### 1. Negative Filters

```apex
// NON-SELECTIVE - Negative operators
List<Account> accounts = [SELECT Id FROM Account WHERE Status__c != 'Closed'];
List<Account> accounts = [SELECT Id FROM Account WHERE Status__c NOT IN ('Closed', 'Inactive')];
List<Account> accounts = [SELECT Id FROM Account WHERE NOT Status__c = 'Closed'];

// SELECTIVE - Positive filter
List<Account> accounts = [SELECT Id FROM Account WHERE Status__c IN ('Open', 'Pending', 'Active')];
```

### 2. Leading Wildcards

```apex
// NON-SELECTIVE - Leading wildcard
List<Account> accounts = [SELECT Id FROM Account WHERE Name LIKE '%Corp'];
List<Account> accounts = [SELECT Id FROM Account WHERE Name LIKE '%Corp%'];

// SELECTIVE - Trailing wildcard only
List<Account> accounts = [SELECT Id FROM Account WHERE Name LIKE 'Acme%'];
```

### 3. Null Checks on Non-Indexed Fields

```apex
// NON-SELECTIVE (if field not indexed)
List<Account> accounts = [SELECT Id FROM Account WHERE Custom_Field__c = null];
List<Account> accounts = [SELECT Id FROM Account WHERE Custom_Field__c != null];

// SELECTIVE - Filter on indexed field + null check
List<Account> accounts = [
    SELECT Id FROM Account 
    WHERE CreatedDate = TODAY  // Selective
    AND Custom_Field__c = null // Now acceptable
];
```

### 4. Complex OR Conditions

```apex
// POTENTIALLY NON-SELECTIVE
List<Account> accounts = [
    SELECT Id FROM Account 
    WHERE Industry = 'Tech' 
    OR Rating = 'Hot'  // OR can break selectivity
];

// MORE SELECTIVE - Separate queries or IN clause
List<Account> accounts = [
    SELECT Id FROM Account 
    WHERE Industry IN ('Tech', 'Finance')
    AND Rating = 'Hot'
];
```

---

## Optimization Techniques

### 1. Use Indexed Fields First

```apex
// GOOD - Filter on indexed field first
List<Account> accounts = [
    SELECT Id, Name, Industry
    FROM Account
    WHERE CreatedDate = TODAY  // Indexed
    AND Industry = 'Technology'  // Secondary filter
];
```

### 2. Selective Relationship Queries

```apex
// Query parent through lookup (indexed)
List<Contact> contacts = [
    SELECT Id, Name, Account.Name
    FROM Contact
    WHERE AccountId = :accountId  // Lookup is indexed
];

// Query children efficiently
List<Account> accounts = [
    SELECT Id, Name, 
           (SELECT Id, Name FROM Contacts WHERE IsActive__c = true)
    FROM Account
    WHERE Id IN :accountIds
];
```

### 3. Use LIMIT Appropriately

```apex
// Always use LIMIT when result set size is known/bounded
List<Account> accounts = [
    SELECT Id, Name
    FROM Account
    WHERE Industry = 'Technology'
    ORDER BY CreatedDate DESC
    LIMIT 100
];

// For pagination
List<Account> accounts = [
    SELECT Id, Name
    FROM Account
    WHERE CreatedDate >= :startDate
    ORDER BY CreatedDate ASC
    LIMIT 100
    OFFSET 200
];  // Note: OFFSET has performance implications for large values
```

### 4. Select Only Required Fields

```apex
// BAD - Selecting all fields
List<Account> accounts = [SELECT Id, Name, Industry, Phone, Website, 
    BillingStreet, BillingCity, BillingState, BillingPostalCode,
    ShippingStreet, ShippingCity, ShippingState, ShippingPostalCode,
    Description, NumberOfEmployees, AnnualRevenue, ...
    FROM Account];

// GOOD - Select only what you need
List<Account> accounts = [SELECT Id, Name, Industry FROM Account];
```

### 5. Use Aggregate Queries

```apex
// BAD - Querying all records to count
List<Account> accounts = [SELECT Id FROM Account WHERE Industry = 'Tech'];
Integer count = accounts.size();  // Wastes query rows

// GOOD - Use COUNT()
Integer count = [SELECT COUNT() FROM Account WHERE Industry = 'Tech'];

// GOOD - Use aggregate functions
List<AggregateResult> results = [
    SELECT Industry, COUNT(Id) cnt, SUM(AnnualRevenue) total
    FROM Account
    WHERE CreatedDate = THIS_YEAR
    GROUP BY Industry
];
```

### 6. Use Semi-Joins and Anti-Joins

```apex
// SEMI-JOIN - Records that have related records
List<Account> accountsWithOpps = [
    SELECT Id, Name
    FROM Account
    WHERE Id IN (SELECT AccountId FROM Opportunity WHERE StageName = 'Closed Won')
];

// ANTI-JOIN - Records without related records
List<Account> accountsWithoutOpps = [
    SELECT Id, Name
    FROM Account
    WHERE Id NOT IN (SELECT AccountId FROM Opportunity)
];
```

---

## Large Data Volume (LDV) Strategies

### 1. Request Custom Indexes

For fields frequently filtered but not indexed by default:
- Submit a case to Salesforce Support
- Provide query patterns and data volumes
- Custom indexes improve selectivity

### 2. Use Skinny Tables

For reporting on large objects:
- Skinny tables contain subset of fields
- Created by Salesforce Support
- Dramatically improve report performance

### 3. Implement Archival Strategy

```apex
// Archive old records to BigObject
public class DataArchiver implements Database.Batchable<SObject> {
    
    public Database.QueryLocator start(Database.BatchableContext bc) {
        Date cutoffDate = Date.today().addYears(-2);
        return Database.getQueryLocator([
            SELECT Id, Name, CreatedDate, /* other fields */
            FROM Activity_Log__c
            WHERE CreatedDate < :cutoffDate
        ]);
    }
    
    public void execute(Database.BatchableContext bc, List<Activity_Log__c> scope) {
        // Insert to BigObject
        List<Archived_Activity__b> archives = new List<Archived_Activity__b>();
        for (Activity_Log__c log : scope) {
            archives.add(new Archived_Activity__b(
                Original_Id__c = log.Id,
                Name__c = log.Name,
                Created_Date__c = log.CreatedDate
            ));
        }
        Database.insertImmediate(archives);
        
        // Delete originals
        delete scope;
    }
    
    public void finish(Database.BatchableContext bc) {
        // Notification
    }
}
```

### 4. Use Query Plan Tool

In Developer Console:
1. Open Query Editor
2. Check "Use Tooling API"
3. Enter query
4. Click "Query Plan" (not "Execute")

Analyze:
- **Cost**: Lower is better (< 1 is selective)
- **Cardinality**: Estimated records
- **Fields**: Which index used
- **Leading operation type**: "TableScan" = non-selective

---

## Query Pattern Examples

### Date Range Queries

```apex
// SELECTIVE - Using indexed CreatedDate
List<Account> accounts = [
    SELECT Id, Name
    FROM Account
    WHERE CreatedDate >= :startDate
    AND CreatedDate <= :endDate
];

// SELECTIVE - Using date literals
List<Account> accounts = [
    SELECT Id, Name
    FROM Account
    WHERE CreatedDate = THIS_QUARTER
];
```

### User-Based Queries

```apex
// SELECTIVE - OwnerId is indexed
List<Account> myAccounts = [
    SELECT Id, Name
    FROM Account
    WHERE OwnerId = :UserInfo.getUserId()
];

// SELECTIVE - Team-based
List<Account> teamAccounts = [
    SELECT Id, Name
    FROM Account
    WHERE OwnerId IN (SELECT Id FROM User WHERE Team__c = :teamId)
];
```

### Record Type Queries

```apex
// SELECTIVE - RecordTypeId is indexed
Id businessRecordTypeId = Schema.SObjectType.Account.getRecordTypeInfosByDeveloperName()
    .get('Business_Account').getRecordTypeId();
    
List<Account> businessAccounts = [
    SELECT Id, Name
    FROM Account
    WHERE RecordTypeId = :businessRecordTypeId
];
```

### External ID Queries

```apex
// SELECTIVE - External ID fields are indexed
List<Account> accounts = [
    SELECT Id, Name
    FROM Account
    WHERE External_System_Id__c = :externalId
];
```

---

## Query Performance Checklist

- [ ] Query filters on indexed field first
- [ ] No SOQL in loops
- [ ] Using LIMIT where appropriate
- [ ] No leading wildcards in LIKE
- [ ] No negative filters on large tables
- [ ] Selecting only required fields
- [ ] Using aggregate queries for counts/sums
- [ ] Semi-joins instead of separate queries
- [ ] Query Plan analyzed for LDV scenarios
- [ ] WITH SECURITY_ENFORCED for FLS
