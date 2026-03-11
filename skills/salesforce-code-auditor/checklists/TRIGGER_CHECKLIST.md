# Trigger Audit Checklist

## Overview
This checklist covers trigger-specific quality, performance, and architecture checks.

---

## Trigger Architecture

### Single Trigger Pattern
- [ ] **ARCH-001**: Only ONE trigger per object
- [ ] **ARCH-002**: Trigger body delegates to handler class
- [ ] **ARCH-003**: Trigger body < 10 lines of code
- [ ] **ARCH-004**: No business logic in trigger body
- [ ] **ARCH-005**: Feature flag check in trigger (optional)

### Trigger Handler Pattern
- [ ] **HAND-001**: Handler extends base framework class
- [ ] **HAND-002**: Handler implements context methods (beforeInsert, afterUpdate, etc.)
- [ ] **HAND-003**: Trigger context variables cached in constructor
- [ ] **HAND-004**: Handler methods are private/protected
- [ ] **HAND-005**: Handler is testable without trigger

---

## Recursion Control

### Recursion Prevention
- [ ] **RECUR-001**: Static variable prevents infinite recursion
- [ ] **RECUR-002**: Maximum recursion depth defined
- [ ] **RECUR-003**: Recursion counter resets appropriately
- [ ] **RECUR-004**: Different recursion control per operation type
- [ ] **RECUR-005**: Test covers recursive scenarios

### Recursion Pattern
```apex
public class AccountTriggerHandler extends TriggerHandler {
    
    private static Boolean isExecuting = false;
    private static Integer recursionCount = 0;
    private static final Integer MAX_RECURSION = 2;
    
    public override void run() {
        if (isExecuting && recursionCount >= MAX_RECURSION) {
            return; // Prevent infinite recursion
        }
        
        isExecuting = true;
        recursionCount++;
        
        try {
            super.run();
        } finally {
            recursionCount--;
            if (recursionCount == 0) {
                isExecuting = false;
            }
        }
    }
}
```

---

## Bypass Mechanism

### Bypass Controls
- [ ] **BYPASS-001**: Static bypass method available
- [ ] **BYPASS-002**: Bypass can be set per handler
- [ ] **BYPASS-003**: Bypass cleared after use
- [ ] **BYPASS-004**: Bypass used in data migrations
- [ ] **BYPASS-005**: Bypass documented where used

### Bypass Pattern
```apex
// In TriggerHandler base class
public class TriggerHandler {
    private static Set<String> bypassedHandlers = new Set<String>();
    
    public static void bypass(String handlerName) {
        bypassedHandlers.add(handlerName);
    }
    
    public static void clearBypass(String handlerName) {
        bypassedHandlers.remove(handlerName);
    }
    
    public static void clearAllBypasses() {
        bypassedHandlers.clear();
    }
    
    protected Boolean isBypassed() {
        return bypassedHandlers.contains(getHandlerName());
    }
}

// Usage in data migration
TriggerHandler.bypass('AccountTriggerHandler');
try {
    // Bulk data operation
    insert accounts;
} finally {
    TriggerHandler.clearBypass('AccountTriggerHandler');
}
```

---

## Performance

### Query Optimization
- [ ] **PERF-001**: No SOQL in trigger body
- [ ] **PERF-002**: No SOQL in loops
- [ ] **PERF-003**: Queries collect IDs first, then batch query
- [ ] **PERF-004**: Maps used for lookups instead of queries
- [ ] **PERF-005**: Queries use selective filters

### DML Optimization
- [ ] **DML-001**: No DML in trigger body
- [ ] **DML-002**: No DML in loops
- [ ] **DML-003**: Records collected then bulk DML
- [ ] **DML-004**: Related objects updated in single transaction
- [ ] **DML-005**: Database.update with allOrNone considered

### Callout Handling
- [ ] **CALL-001**: No synchronous callouts in trigger
- [ ] **CALL-002**: Callouts moved to @future or Queueable
- [ ] **CALL-003**: Platform Events for async processing
- [ ] **CALL-004**: Callout context checked (isFuture, isBatch)

---

## Context Handling

### Trigger Context
- [ ] **CTX-001**: `Trigger.new` cached in handler variable
- [ ] **CTX-002**: `Trigger.oldMap` used for comparisons
- [ ] **CTX-003**: Context checked (isBefore, isAfter, isInsert, etc.)
- [ ] **CTX-004**: Appropriate logic in before vs after contexts
- [ ] **CTX-005**: isExecuting checked if needed

### Context Best Practices

| Context | Use For |
|---------|--------|
| before insert | Set defaults, validate, calculate fields |
| before update | Validate changes, recalculate fields |
| before delete | Validate deletion is allowed |
| after insert | Create related records, async operations |
| after update | Update related records, notifications |
| after delete | Cleanup, notifications |
| after undelete | Restore related data |

---

## Field Change Detection

### Change Detection
- [ ] **CHG-001**: Field changes detected using oldMap comparison
- [ ] **CHG-002**: Only changed records processed
- [ ] **CHG-003**: Change detection handles null values
- [ ] **CHG-004**: Multiple field changes handled efficiently

### Change Detection Pattern
```apex
private List<Account> getAccountsWithStatusChange() {
    List<Account> changed = new List<Account>();
    
    for (Account acc : (List<Account>) Trigger.new) {
        Account oldAcc = (Account) Trigger.oldMap.get(acc.Id);
        
        if (acc.Status__c != oldAcc.Status__c) {
            changed.add(acc);
        }
    }
    
    return changed;
}

private Boolean hasFieldChanged(SObject newRecord, SObject oldRecord, String fieldName) {
    return newRecord.get(fieldName) != oldRecord.get(fieldName);
}
```

---

## Error Handling

### Error Patterns
- [ ] **ERR-001**: `addError()` used for record-level errors
- [ ] **ERR-002**: `addError(field)` used for field-level errors
- [ ] **ERR-003**: Error messages are user-friendly
- [ ] **ERR-004**: Partial success considered (Database methods)
- [ ] **ERR-005**: Errors don't expose system information

### Error Pattern
```apex
private void validateAccounts(List<Account> accounts) {
    for (Account acc : accounts) {
        // Record-level error
        if (String.isBlank(acc.Name)) {
            acc.addError('Account name is required');
        }
        
        // Field-level error
        if (acc.AnnualRevenue != null && acc.AnnualRevenue < 0) {
            acc.AnnualRevenue.addError('Annual revenue cannot be negative');
        }
        
        // Cross-field validation
        if (acc.Type == 'Enterprise' && acc.Industry == null) {
            acc.addError('Industry is required for Enterprise accounts');
        }
    }
}
```

---

## Testing

### Test Requirements
- [ ] **TEST-001**: Trigger tested with 1 record
- [ ] **TEST-002**: Trigger tested with 200+ records (bulk)
- [ ] **TEST-003**: All trigger events tested (insert, update, delete, undelete)
- [ ] **TEST-004**: Recursive scenarios tested
- [ ] **TEST-005**: Error scenarios tested
- [ ] **TEST-006**: Field change scenarios tested
- [ ] **TEST-007**: Bypass mechanism tested

### Test Pattern
```apex
@IsTest
private class AccountTriggerTest {
    
    @TestSetup
    static void setup() {
        // Common test data
    }
    
    @IsTest
    static void testInsert_SingleRecord_Success() {
        Account acc = TestDataFactory.createAccount(false);
        
        Test.startTest();
        insert acc;
        Test.stopTest();
        
        Account result = [SELECT Id, Status__c FROM Account WHERE Id = :acc.Id];
        System.assertEquals('New', result.Status__c, 'Default status should be New');
    }
    
    @IsTest
    static void testInsert_BulkRecords_Success() {
        List<Account> accounts = TestDataFactory.createAccounts(200, false);
        
        Test.startTest();
        insert accounts;
        Test.stopTest();
        
        List<Account> results = [SELECT Id, Status__c FROM Account WHERE Id IN :accounts];
        System.assertEquals(200, results.size(), 'All accounts should be inserted');
    }
    
    @IsTest
    static void testUpdate_StatusChange_CreatesTask() {
        Account acc = TestDataFactory.createAccount(true);
        acc.Status__c = 'Active';
        
        Test.startTest();
        update acc;
        Test.stopTest();
        
        List<Task> tasks = [SELECT Id, Subject FROM Task WHERE WhatId = :acc.Id];
        System.assertEquals(1, tasks.size(), 'Status change should create task');
    }
    
    @IsTest
    static void testDelete_WithOpenOpportunities_Fails() {
        Account acc = TestDataFactory.createAccountWithOpportunities(true);
        
        Test.startTest();
        try {
            delete acc;
            System.assert(false, 'Delete should fail');
        } catch (DmlException e) {
            System.assert(e.getMessage().contains('open opportunities'));
        }
        Test.stopTest();
    }
}
```

---

## Order of Execution Awareness

### Execution Order
- [ ] **ORDER-001**: Aware of validation rules timing
- [ ] **ORDER-002**: Aware of workflow rules timing
- [ ] **ORDER-003**: Aware of process builder timing
- [ ] **ORDER-004**: Aware of flow timing
- [ ] **ORDER-005**: Cross-object updates handled correctly

### Order of Execution Summary
1. System validation (required fields, field formats)
2. **Before triggers**
3. Custom validation rules
4. Duplicate rules
5. Record saved (not committed)
6. **After triggers**
7. Assignment rules
8. Auto-response rules
9. Workflow rules
10. Processes and flows
11. Escalation rules
12. Roll-up summary fields
13. Cross-object workflow updates
14. Criteria-based sharing
15. **Commit**
16. Post-commit logic (outbound messages, platform events)
