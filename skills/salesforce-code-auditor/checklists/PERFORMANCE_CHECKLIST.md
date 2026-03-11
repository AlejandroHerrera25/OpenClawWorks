# Performance Audit Checklist

## Overview
This checklist ensures Salesforce code meets performance requirements and stays within governor limits.

---

## CRITICAL Performance Issues (Severity 1)

### SOQL in Loops
- [ ] **SOQL-LOOP-001**: No SOQL queries inside `for` loops
- [ ] **SOQL-LOOP-002**: No SOQL queries inside `while` loops
- [ ] **SOQL-LOOP-003**: No SOQL queries inside `do-while` loops
- [ ] **SOQL-LOOP-004**: Related records queried via relationship queries
- [ ] **SOQL-LOOP-005**: Maps used for lookup instead of re-querying

**Detection Pattern**:
```apex
// CRITICAL: SOQL in loop
for (Account acc : accounts) {
    List<Contact> contacts = [SELECT Id FROM Contact WHERE AccountId = :acc.Id]; // BAD
}

// CORRECT: Query outside loop
Map<Id, List<Contact>> contactsByAccount = new Map<Id, List<Contact>>();
for (Contact c : [SELECT Id, AccountId FROM Contact WHERE AccountId IN :accountIds]) {
    if (!contactsByAccount.containsKey(c.AccountId)) {
        contactsByAccount.put(c.AccountId, new List<Contact>());
    }
    contactsByAccount.get(c.AccountId).add(c);
}
```

### DML in Loops
- [ ] **DML-LOOP-001**: No `insert` inside loops
- [ ] **DML-LOOP-002**: No `update` inside loops
- [ ] **DML-LOOP-003**: No `delete` inside loops
- [ ] **DML-LOOP-004**: No `upsert` inside loops
- [ ] **DML-LOOP-005**: Collections used for bulk DML

**Detection Pattern**:
```apex
// CRITICAL: DML in loop
for (Account acc : accounts) {
    acc.Status__c = 'Active';
    update acc; // BAD
}

// CORRECT: Bulk DML
List<Account> toUpdate = new List<Account>();
for (Account acc : accounts) {
    acc.Status__c = 'Active';
    toUpdate.add(acc);
}
update toUpdate;
```

### Recursive Triggers
- [ ] **RECUR-001**: Static variable used to prevent recursion
- [ ] **RECUR-002**: Trigger handler framework with recursion control
- [ ] **RECUR-003**: Maximum recursion depth defined
- [ ] **RECUR-004**: `Trigger.isExecuting` checked appropriately
- [ ] **RECUR-005**: Cross-object trigger chains analyzed

---

## HIGH Performance Issues (Severity 2)

### Query Optimization
- [ ] **QUERY-001**: Selective filters on indexed fields
- [ ] **QUERY-002**: No leading wildcards in LIKE clauses
- [ ] **QUERY-003**: LIMIT clause used where appropriate
- [ ] **QUERY-004**: Only required fields selected (no SELECT *)
- [ ] **QUERY-005**: Relationship queries used vs separate queries
- [ ] **QUERY-006**: Aggregate queries for counts/sums
- [ ] **QUERY-007**: OFFSET used carefully (performance degrades)

**Indexed Fields** (query these for selectivity):
- Id
- Name
- OwnerId
- CreatedDate
- LastModifiedDate
- RecordTypeId
- Custom fields marked as External ID
- Custom indexed fields

### Callouts in Triggers
- [ ] **CALL-001**: No synchronous callouts in triggers
- [ ] **CALL-002**: `@future(callout=true)` used for async callouts
- [ ] **CALL-003**: Queueable used for complex async operations
- [ ] **CALL-004**: Callout timeouts configured
- [ ] **CALL-005**: Maximum callouts per transaction tracked

### CPU Time
- [ ] **CPU-001**: Nested loops minimized
- [ ] **CPU-002**: String concatenation uses StringBuilder pattern
- [ ] **CPU-003**: Regex operations optimized
- [ ] **CPU-004**: JSON parsing efficient for large payloads
- [ ] **CPU-005**: Algorithm complexity analyzed (O(n) vs O(n²))

---

## MEDIUM Performance Issues (Severity 3)

### Heap Size
- [ ] **HEAP-001**: Large collections processed in batches
- [ ] **HEAP-002**: Binary data (Blob) handled carefully
- [ ] **HEAP-003**: Query results streamed where possible
- [ ] **HEAP-004**: Unused variables set to null
- [ ] **HEAP-005**: Large strings built efficiently

### Async Processing
- [ ] **ASYNC-001**: Batch Apex used for large data volumes
- [ ] **ASYNC-002**: Queueable used for chained operations
- [ ] **ASYNC-003**: `@future` used for simple async needs
- [ ] **ASYNC-004**: Platform Events for event-driven architecture
- [ ] **ASYNC-005**: Scheduled Apex for time-based processing

### Caching
- [ ] **CACHE-001**: Platform Cache used for frequently accessed data
- [ ] **CACHE-002**: Session cache for user-specific data
- [ ] **CACHE-003**: Org cache for shared data
- [ ] **CACHE-004**: Cache TTL configured appropriately
- [ ] **CACHE-005**: Cache invalidation strategy defined

### LWC Performance
- [ ] **LWC-001**: Wire service used for reactive data
- [ ] **LWC-002**: `cacheable=true` for read operations
- [ ] **LWC-003**: `refreshApex()` used sparingly
- [ ] **LWC-004**: Lazy loading for large datasets
- [ ] **LWC-005**: Debouncing for search inputs
- [ ] **LWC-006**: Virtual scrolling for long lists

---

## LOW Performance Issues (Severity 4)

### Code Efficiency
- [ ] **EFF-001**: Early returns used to avoid unnecessary processing
- [ ] **EFF-002**: Maps used instead of linear searches
- [ ] **EFF-003**: Sets used for membership checks
- [ ] **EFF-004**: Ternary operators used where clearer
- [ ] **EFF-005**: Method size kept reasonable (< 50 lines)

### Debug Logging
- [ ] **DEBUG-001**: Debug statements minimized in production
- [ ] **DEBUG-002**: No `System.debug()` in loops
- [ ] **DEBUG-003**: Debug levels appropriate
- [ ] **DEBUG-004**: Trace flags managed

---

## Governor Limit Tracking

### Per-Transaction Limits (Synchronous)

| Limit | Maximum | Check Method |
|-------|---------|-------------|
| SOQL Queries | 100 | `Limits.getQueries()` |
| Query Rows | 50,000 | `Limits.getQueryRows()` |
| DML Statements | 150 | `Limits.getDmlStatements()` |
| DML Rows | 10,000 | `Limits.getDmlRows()` |
| CPU Time | 10,000 ms | `Limits.getCpuTime()` |
| Heap Size | 6 MB | `Limits.getHeapSize()` |
| Callouts | 100 | `Limits.getCallouts()` |

### Limit Monitoring Code
```apex
public static void checkLimits() {
    System.debug('SOQL: ' + Limits.getQueries() + '/' + Limits.getLimitQueries());
    System.debug('Rows: ' + Limits.getQueryRows() + '/' + Limits.getLimitQueryRows());
    System.debug('DML: ' + Limits.getDmlStatements() + '/' + Limits.getLimitDmlStatements());
    System.debug('CPU: ' + Limits.getCpuTime() + '/' + Limits.getLimitCpuTime());
    System.debug('Heap: ' + Limits.getHeapSize() + '/' + Limits.getLimitHeapSize());
}
```

---

## Large Data Volume (LDV) Checklist

### Query Optimization for LDV
- [ ] Queries on tables > 100K records are selective
- [ ] Custom indexes requested for high-volume queries
- [ ] Skinny tables considered for reporting
- [ ] Archival strategy in place for old data

### Selectivity Rules
A query is selective if:
- Filter on indexed field returns < 30% of records
- Filter on non-indexed field returns < 10% of records
- Combined filters meet threshold

### LDV Anti-Patterns
- [ ] No `!=` filters (non-selective)
- [ ] No `NOT IN` filters (non-selective)
- [ ] No leading wildcards `LIKE '%value'`
- [ ] No null checks on non-indexed fields
