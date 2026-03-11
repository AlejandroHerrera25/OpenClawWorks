# Salesforce Governor Limits — Complete Reference

## Overview

Governor limits are Salesforce's mechanism for ensuring that no single tenant monopolizes shared resources in the multi-tenant environment. Understanding and respecting these limits is **critical** for building scalable Salesforce applications.

---

## Synchronous Apex Limits

| Limit | Value | Notes |
|-------|-------|-------|
| Total SOQL queries | 100 | Per transaction |
| Total records retrieved by SOQL | 50,000 | Per transaction |
| Total SOSL queries | 20 | Per transaction |
| Total records retrieved by SOSL | 2,000 | Per transaction |
| Total DML statements | 150 | Per transaction |
| Total records processed by DML | 10,000 | Per transaction |
| Total callouts (HTTP/Web services) | 100 | Per transaction |
| Maximum callout timeout | 120 seconds | Total for all callouts |
| Maximum CPU time | 10,000 ms | Per transaction |
| Maximum heap size | 6 MB | Per transaction |
| Maximum stack depth | 16 | Recursive calls |
| Maximum query rows in Database.getQueryLocator | 50,000,000 | For batch Apex |
| Maximum number of records returned by inline SOQL | 50,000 | - |
| Maximum number of @future methods | 50 | Per transaction |
| Maximum number of queueable jobs | 50 | Per transaction |
| Maximum number of batch Apex jobs queued/active | 5 | Concurrent |
| Maximum number of scheduled Apex | 100 | Per org |
| Maximum query locators open | 10 | Per transaction |
| Maximum publishImmediately platform events | 150 | Per transaction |
| Maximum email invocations | 10 | Per transaction |
| Maximum push notifications | 20 | Per transaction |

---

## Asynchronous Apex Limits

| Limit | Batch | Queueable | Future | Scheduled |
|-------|-------|-----------|--------|----------|
| SOQL queries | 200 | 200 | 200 | 200 |
| Records retrieved | 50,000 | 50,000 | 50,000 | 50,000 |
| DML statements | 150 | 150 | 150 | 150 |
| Records processed by DML | 10,000 | 10,000 | 10,000 | 10,000 |
| Callouts | 100 | 100 | 100 | 100 |
| CPU time | 60,000 ms | 60,000 ms | 60,000 ms | 60,000 ms |
| Heap size | 12 MB | 12 MB | 12 MB | 12 MB |

---

## Platform Event Limits

| Limit | Value |
|-------|-------|
| Maximum event message size | 1 MB |
| Maximum events published per hour | Varies by edition |
| Maximum CometD clients | 2,000 |
| Maximum subscriptions per CometD client | 40 |
| Event retention | 72 hours |

---

## Certified Managed Package Limits

Certified managed packages get their own set of governor limits, effectively doubling available resources for:
- SOQL queries
- DML statements
- Callouts

---

## Limit Detection Patterns

### SOQL in Loops — CRITICAL

**Anti-Pattern**:
```apex
// CRITICAL: SOQL inside loop
for (Account acc : accounts) {
    List<Contact> contacts = [SELECT Id FROM Contact WHERE AccountId = :acc.Id];
    // Process contacts
}
```

**Correct Pattern**:
```apex
// CORRECT: Query outside loop with relationship or map
Map<Id, List<Contact>> contactsByAccount = new Map<Id, List<Contact>>();
for (Contact c : [SELECT Id, AccountId FROM Contact WHERE AccountId IN :accountIds]) {
    if (!contactsByAccount.containsKey(c.AccountId)) {
        contactsByAccount.put(c.AccountId, new List<Contact>());
    }
    contactsByAccount.get(c.AccountId).add(c);
}
```

### DML in Loops — CRITICAL

**Anti-Pattern**:
```apex
// CRITICAL: DML inside loop
for (Account acc : accounts) {
    acc.Status__c = 'Processed';
    update acc;
}
```

**Correct Pattern**:
```apex
// CORRECT: Collect and bulkify
List<Account> toUpdate = new List<Account>();
for (Account acc : accounts) {
    acc.Status__c = 'Processed';
    toUpdate.add(acc);
}
update toUpdate;
```

### Heap Size Management

**Anti-Pattern**:
```apex
// RISK: Loading all records into memory
List<ContentVersion> allFiles = [SELECT Id, VersionData FROM ContentVersion];
```

**Correct Pattern**:
```apex
// CORRECT: Process in batches or use streaming
for (ContentVersion cv : [SELECT Id, Title FROM ContentVersion LIMIT 1000]) {
    // Process without loading binary data unless necessary
}
```

### CPU Time Management

**High CPU Operations**:
- Complex string manipulation
- JSON parsing of large payloads
- Nested loops
- Regex operations
- Reflection operations

**Optimization Techniques**:
1. Move to async processing
2. Use Platform Cache
3. Optimize algorithms (O(n) vs O(n²))
4. Use native methods over custom implementations

---

## Limit Monitoring in Code

```apex
public class LimitMonitor {
    public static void logLimits(String checkpoint) {
        System.debug('=== Limits at: ' + checkpoint + ' ===');
        System.debug('SOQL Queries: ' + Limits.getQueries() + '/' + Limits.getLimitQueries());
        System.debug('Query Rows: ' + Limits.getQueryRows() + '/' + Limits.getLimitQueryRows());
        System.debug('DML Statements: ' + Limits.getDmlStatements() + '/' + Limits.getLimitDmlStatements());
        System.debug('DML Rows: ' + Limits.getDmlRows() + '/' + Limits.getLimitDmlRows());
        System.debug('CPU Time: ' + Limits.getCpuTime() + '/' + Limits.getLimitCpuTime());
        System.debug('Heap Size: ' + Limits.getHeapSize() + '/' + Limits.getLimitHeapSize());
        System.debug('Callouts: ' + Limits.getCallouts() + '/' + Limits.getLimitCallouts());
    }
    
    public static Boolean isApproachingLimit(String limitType, Decimal threshold) {
        switch on limitType {
            when 'SOQL' {
                return (Decimal)Limits.getQueries() / Limits.getLimitQueries() > threshold;
            }
            when 'DML' {
                return (Decimal)Limits.getDmlStatements() / Limits.getLimitDmlStatements() > threshold;
            }
            when 'CPU' {
                return (Decimal)Limits.getCpuTime() / Limits.getLimitCpuTime() > threshold;
            }
            when 'HEAP' {
                return (Decimal)Limits.getHeapSize() / Limits.getLimitHeapSize() > threshold;
            }
            when else {
                return false;
            }
        }
    }
}
```

---

## Flow-Specific Limits

| Limit | Value |
|-------|-------|
| Maximum flow interviews per transaction | 50 |
| Maximum executed elements per interview | 2,000 |
| Maximum executed elements per flow | 2,000 |
| Maximum assignments per interview | 2,000 |
| Maximum loop iterations | 2,000 |

---

## Large Data Volume (LDV) Considerations

### Selective Queries
Queries must be selective when table has > 1,000,000 records:
- Filter on indexed fields
- Use custom indexes
- Avoid negative filters (!=, NOT IN)
- Avoid leading wildcards in LIKE

### Skinny Tables
Consider skinny tables for:
- Frequently queried fields
- Large objects with many fields
- Report optimization

### Archive Strategy
- BigObjects for historical data
- External objects for large datasets
- Data archival policies

---

## Audit Checklist for Governor Limits

- [ ] No SOQL queries inside loops
- [ ] No DML operations inside loops
- [ ] No callouts inside loops
- [ ] Queries are bulkified with IN clauses
- [ ] DML operations use collections
- [ ] Async processing for heavy operations
- [ ] Heap size managed for large data
- [ ] CPU-intensive operations optimized
- [ ] Query selectivity verified for LDV
- [ ] Limit monitoring implemented for critical paths
- [ ] Batch processing for large datasets
- [ ] Platform cache utilized where appropriate
