# Trigger Implementation Patterns — Complete Reference

## Overview

Triggers are critical automation components in Salesforce. Poor trigger design leads to performance issues, recursion problems, and unmaintainable code. This guide provides enterprise-grade patterns for trigger implementation.

---

## Order of Execution

### Complete Salesforce Order of Execution

```
1. System Validation Rules
2. Before Triggers
3. Custom Validation Rules
4. Duplicate Rules
5. After Triggers
6. Assignment Rules
7. Auto-Response Rules
8. Workflow Rules
9. Processes and Flows
10. Escalation Rules
11. Entitlement Rules
12. Roll-Up Summary Fields
13. Cross-Object Workflow Updates
14. Parent Roll-Up Summary (if child updated)
15. Criteria-Based Sharing Evaluation
16. Post-Commit Logic (Platform Events, Outbound Messages)
```

### Implications for Trigger Design

1. **Before triggers** should handle:
   - Field defaulting
   - Field validation
   - Field calculation
   - Cross-object field population (query-based)

2. **After triggers** should handle:
   - Related record creation/update
   - Platform event publishing
   - Async job queueing
   - Integration callouts (via async)

---

## Single Trigger Per Object Pattern

### The Trigger

```apex
/**
 * AccountTrigger
 * Single trigger for Account object - delegates all logic to handler
 * @author Your Name
 * @date 2024-01-01
 */
trigger AccountTrigger on Account (
    before insert, before update, before delete,
    after insert, after update, after delete, after undelete
) {
    // Feature flag check (optional)
    if (Trigger_Settings__c.getInstance().Disable_Account_Trigger__c) {
        return;
    }
    
    // Delegate to handler
    new AccountTriggerHandler().run();
}
```

---

## Trigger Handler Framework

### Base Handler Class

```apex
/**
 * TriggerHandler
 * Abstract base class for all trigger handlers
 * Provides recursion control, bypass mechanism, and lifecycle hooks
 */
public virtual class TriggerHandler {
    
    // Recursion control
    private static Map<String, LoopCount> loopCountMap = new Map<String, LoopCount>();
    private static Set<String> bypassedHandlers = new Set<String>();
    
    // Instance variables
    @TestVisible
    protected Boolean isTriggerExecuting;
    @TestVisible
    protected TriggerOperation context;
    
    // Constructor
    public TriggerHandler() {
        this.setTriggerContext();
    }
    
    // Main entry point
    public void run() {
        if (!validateRun()) {
            return;
        }
        
        addToLoopCount();
        
        // Dispatch to appropriate handler method
        switch on this.context {
            when BEFORE_INSERT {
                this.beforeInsert();
            }
            when BEFORE_UPDATE {
                this.beforeUpdate();
            }
            when BEFORE_DELETE {
                this.beforeDelete();
            }
            when AFTER_INSERT {
                this.afterInsert();
            }
            when AFTER_UPDATE {
                this.afterUpdate();
            }
            when AFTER_DELETE {
                this.afterDelete();
            }
            when AFTER_UNDELETE {
                this.afterUndelete();
            }
        }
    }
    
    // Set max loop count for recursion control
    public void setMaxLoopCount(Integer max) {
        String handlerName = getHandlerName();
        if (!loopCountMap.containsKey(handlerName)) {
            loopCountMap.put(handlerName, new LoopCount(max));
        } else {
            loopCountMap.get(handlerName).setMax(max);
        }
    }
    
    // Clear max loop count
    public void clearMaxLoopCount() {
        loopCountMap.remove(getHandlerName());
    }
    
    // Bypass this handler
    public static void bypass(String handlerName) {
        bypassedHandlers.add(handlerName);
    }
    
    // Remove bypass
    public static void clearBypass(String handlerName) {
        bypassedHandlers.remove(handlerName);
    }
    
    // Check if bypassed
    public static Boolean isBypassed(String handlerName) {
        return bypassedHandlers.contains(handlerName);
    }
    
    // Clear all bypasses
    public static void clearAllBypasses() {
        bypassedHandlers.clear();
    }
    
    // Protected context methods - override in concrete handlers
    @TestVisible
    protected virtual void beforeInsert() {}
    @TestVisible
    protected virtual void beforeUpdate() {}
    @TestVisible
    protected virtual void beforeDelete() {}
    @TestVisible
    protected virtual void afterInsert() {}
    @TestVisible
    protected virtual void afterUpdate() {}
    @TestVisible
    protected virtual void afterDelete() {}
    @TestVisible
    protected virtual void afterUndelete() {}
    
    // Private helper methods
    private void setTriggerContext() {
        this.isTriggerExecuting = Trigger.isExecuting;
        this.context = Trigger.operationType;
    }
    
    private Boolean validateRun() {
        if (!this.isTriggerExecuting) {
            throw new TriggerHandlerException('Trigger handler called outside of Trigger execution');
        }
        
        if (bypassedHandlers.contains(getHandlerName())) {
            return false;
        }
        
        if (hasExceededMaxLoopCount()) {
            return false;
        }
        
        return true;
    }
    
    private void addToLoopCount() {
        String handlerName = getHandlerName();
        if (loopCountMap.containsKey(handlerName)) {
            loopCountMap.get(handlerName).increment();
        }
    }
    
    private Boolean hasExceededMaxLoopCount() {
        String handlerName = getHandlerName();
        if (!loopCountMap.containsKey(handlerName)) {
            return false;
        }
        return loopCountMap.get(handlerName).exceeded();
    }
    
    @TestVisible
    private String getHandlerName() {
        return String.valueOf(this).split(':')[0];
    }
    
    // Inner class for loop counting
    private class LoopCount {
        private Integer max;
        private Integer count;
        
        public LoopCount() {
            this.max = 5;
            this.count = 0;
        }
        
        public LoopCount(Integer max) {
            this.max = max;
            this.count = 0;
        }
        
        public void increment() {
            this.count++;
        }
        
        public Boolean exceeded() {
            return this.count > this.max;
        }
        
        public void setMax(Integer max) {
            this.max = max;
        }
    }
    
    public class TriggerHandlerException extends Exception {}
}
```

### Concrete Handler Example

```apex
/**
 * AccountTriggerHandler
 * Handles all Account trigger events
 */
public class AccountTriggerHandler extends TriggerHandler {
    
    // Cached trigger collections
    private List<Account> newAccounts;
    private List<Account> oldAccounts;
    private Map<Id, Account> newAccountsMap;
    private Map<Id, Account> oldAccountsMap;
    
    // Constructor - cache trigger context
    public AccountTriggerHandler() {
        super();
        this.newAccounts = (List<Account>) Trigger.new;
        this.oldAccounts = (List<Account>) Trigger.old;
        this.newAccountsMap = (Map<Id, Account>) Trigger.newMap;
        this.oldAccountsMap = (Map<Id, Account>) Trigger.oldMap;
        
        // Set max recursion depth
        this.setMaxLoopCount(2);
    }
    
    // Before Insert
    protected override void beforeInsert() {
        setDefaults(this.newAccounts);
        validateRequiredFields(this.newAccounts);
        populateExternalId(this.newAccounts);
    }
    
    // Before Update
    protected override void beforeUpdate() {
        validateStatusTransitions(this.newAccounts, this.oldAccountsMap);
        calculateDerivedFields(this.newAccounts, this.oldAccountsMap);
    }
    
    // Before Delete
    protected override void beforeDelete() {
        validateDeletion(this.oldAccounts);
    }
    
    // After Insert
    protected override void afterInsert() {
        createDefaultContacts(this.newAccounts);
        notifyIntegrations(this.newAccounts, null);
    }
    
    // After Update
    protected override void afterUpdate() {
        handleStatusChanges(this.newAccounts, this.oldAccountsMap);
        syncToExternalSystem(this.newAccounts, this.oldAccountsMap);
    }
    
    // After Delete
    protected override void afterDelete() {
        cleanupRelatedData(this.oldAccounts);
    }
    
    // After Undelete
    protected override void afterUndelete() {
        restoreRelatedData(this.newAccounts);
    }
    
    // ============ PRIVATE HELPER METHODS ============
    
    private void setDefaults(List<Account> accounts) {
        for (Account acc : accounts) {
            if (acc.Rating == null) {
                acc.Rating = 'Cold';
            }
            if (acc.Type == null) {
                acc.Type = 'Prospect';
            }
        }
    }
    
    private void validateRequiredFields(List<Account> accounts) {
        for (Account acc : accounts) {
            if (String.isBlank(acc.Name)) {
                acc.addError('Account name is required');
            }
            if (acc.Industry == null && acc.Type == 'Customer') {
                acc.addError('Industry is required for Customer accounts');
            }
        }
    }
    
    private void populateExternalId(List<Account> accounts) {
        for (Account acc : accounts) {
            if (String.isBlank(acc.External_Id__c)) {
                acc.External_Id__c = generateExternalId();
            }
        }
    }
    
    private String generateExternalId() {
        return 'ACC-' + String.valueOf(Datetime.now().getTime()) + 
               '-' + String.valueOf(Math.abs(Crypto.getRandomInteger()));
    }
    
    private void validateStatusTransitions(List<Account> newAccounts, Map<Id, Account> oldMap) {
        Map<String, Set<String>> allowedTransitions = new Map<String, Set<String>>{
            'Prospect' => new Set<String>{'Active', 'Inactive'},
            'Active' => new Set<String>{'Inactive', 'Closed'},
            'Inactive' => new Set<String>{'Active', 'Closed'},
            'Closed' => new Set<String>() // No transitions allowed
        };
        
        for (Account acc : newAccounts) {
            Account oldAcc = oldMap.get(acc.Id);
            if (acc.Status__c != oldAcc.Status__c) {
                Set<String> allowed = allowedTransitions.get(oldAcc.Status__c);
                if (allowed == null || !allowed.contains(acc.Status__c)) {
                    acc.addError('Invalid status transition from ' + oldAcc.Status__c + 
                                ' to ' + acc.Status__c);
                }
            }
        }
    }
    
    private void calculateDerivedFields(List<Account> newAccounts, Map<Id, Account> oldMap) {
        for (Account acc : newAccounts) {
            Account oldAcc = oldMap.get(acc.Id);
            
            // Track status change date
            if (acc.Status__c != oldAcc.Status__c) {
                acc.Status_Changed_Date__c = Date.today();
            }
        }
    }
    
    private void validateDeletion(List<Account> accounts) {
        // Check for related opportunities
        Set<Id> accountIds = new Map<Id, Account>(accounts).keySet();
        Map<Id, Integer> oppCounts = new Map<Id, Integer>();
        
        for (AggregateResult ar : [
            SELECT AccountId, COUNT(Id) cnt
            FROM Opportunity
            WHERE AccountId IN :accountIds
            AND StageName NOT IN ('Closed Won', 'Closed Lost')
            GROUP BY AccountId
        ]) {
            oppCounts.put((Id)ar.get('AccountId'), (Integer)ar.get('cnt'));
        }
        
        for (Account acc : accounts) {
            if (oppCounts.containsKey(acc.Id) && oppCounts.get(acc.Id) > 0) {
                acc.addError('Cannot delete account with open opportunities');
            }
        }
    }
    
    private void createDefaultContacts(List<Account> accounts) {
        // Check if feature is enabled
        if (!Account_Settings__c.getInstance().Create_Default_Contact__c) {
            return;
        }
        
        List<Contact> contactsToCreate = new List<Contact>();
        for (Account acc : accounts) {
            if (acc.Type == 'Customer') {
                contactsToCreate.add(new Contact(
                    AccountId = acc.Id,
                    LastName = 'Primary Contact',
                    Email = 'primary@' + acc.Name.toLowerCase().replaceAll('[^a-z0-9]', '') + '.com'
                ));
            }
        }
        
        if (!contactsToCreate.isEmpty()) {
            insert contactsToCreate;
        }
    }
    
    private void notifyIntegrations(List<Account> newAccounts, Map<Id, Account> oldMap) {
        // Queue async job for integration
        List<Account> toSync = new List<Account>();
        for (Account acc : newAccounts) {
            if (acc.Sync_To_External__c) {
                toSync.add(acc);
            }
        }
        
        if (!toSync.isEmpty() && !System.isBatch() && !System.isFuture()) {
            System.enqueueJob(new AccountSyncQueueable(toSync));
        }
    }
    
    private void handleStatusChanges(List<Account> newAccounts, Map<Id, Account> oldMap) {
        List<Task> tasksToCreate = new List<Task>();
        
        for (Account acc : newAccounts) {
            Account oldAcc = oldMap.get(acc.Id);
            
            // Create follow-up task when account becomes active
            if (acc.Status__c == 'Active' && oldAcc.Status__c != 'Active') {
                tasksToCreate.add(new Task(
                    Subject = 'New Active Account - Follow Up',
                    WhatId = acc.Id,
                    OwnerId = acc.OwnerId,
                    ActivityDate = Date.today().addDays(7),
                    Priority = 'High'
                ));
            }
        }
        
        if (!tasksToCreate.isEmpty()) {
            insert tasksToCreate;
        }
    }
    
    private void syncToExternalSystem(List<Account> newAccounts, Map<Id, Account> oldMap) {
        // Implement external sync logic
    }
    
    private void cleanupRelatedData(List<Account> accounts) {
        // Cleanup logic for deleted accounts
    }
    
    private void restoreRelatedData(List<Account> accounts) {
        // Restore logic for undeleted accounts
    }
}
```

---

## Anti-Patterns to Detect

### 1. Multiple Triggers on Same Object

```apex
// ANTI-PATTERN: Multiple triggers
trigger AccountTrigger1 on Account (before insert) {
    // Logic 1
}

trigger AccountTrigger2 on Account (before insert) {
    // Logic 2
}
// Problem: Non-deterministic execution order!
```

### 2. SOQL/DML in Loops

```apex
// ANTI-PATTERN: Query in trigger loop
trigger BadAccountTrigger on Account (after insert) {
    for (Account acc : Trigger.new) {
        // CRITICAL: SOQL in loop
        List<Contact> contacts = [SELECT Id FROM Contact WHERE AccountId = :acc.Id];
    }
}
```

### 3. No Recursion Control

```apex
// ANTI-PATTERN: No recursion control
trigger RecursiveTrigger on Account (after update) {
    List<Account> toUpdate = new List<Account>();
    for (Account acc : Trigger.new) {
        acc.Last_Updated__c = Datetime.now();
        toUpdate.add(acc); // This causes infinite loop!
    }
    update toUpdate;
}
```

### 4. Direct DML in Trigger Body

```apex
// ANTI-PATTERN: DML directly in trigger
trigger DirectDmlTrigger on Account (after insert) {
    // Hard to test, hard to maintain
    Contact c = new Contact(LastName = 'Test', AccountId = Trigger.new[0].Id);
    insert c;
}
```

### 5. Hard-coded Values

```apex
// ANTI-PATTERN: Hard-coded values
trigger HardcodedTrigger on Account (before insert) {
    for (Account acc : Trigger.new) {
        if (acc.Industry == 'Technology') { // Hard-coded
            acc.Priority__c = 'High';
        }
    }
}

// CORRECT: Use Custom Metadata or Custom Settings
trigger ConfigurableTrigger on Account (before insert) {
    Map<String, String> industryPriority = new Map<String, String>();
    for (Industry_Priority__mdt config : [
        SELECT Industry__c, Priority__c 
        FROM Industry_Priority__mdt
    ]) {
        industryPriority.put(config.Industry__c, config.Priority__c);
    }
    
    for (Account acc : Trigger.new) {
        if (industryPriority.containsKey(acc.Industry)) {
            acc.Priority__c = industryPriority.get(acc.Industry);
        }
    }
}
```

---

## Trigger Audit Checklist

### Structure
- [ ] Single trigger per object
- [ ] Trigger delegates to handler class
- [ ] Handler extends framework base class
- [ ] Clear separation of before/after logic

### Performance
- [ ] No SOQL in loops
- [ ] No DML in loops
- [ ] Collections used for bulk operations
- [ ] Maps used for efficient lookups
- [ ] Early returns for empty sets

### Recursion
- [ ] Recursion control implemented
- [ ] Max loop count configured
- [ ] Static bypass mechanism available
- [ ] Test coverage for recursion scenarios

### Error Handling
- [ ] addError() used for field/record errors
- [ ] Custom exceptions for handler errors
- [ ] Meaningful error messages
- [ ] No silent failures

### Security
- [ ] CRUD checks if operating on different objects
- [ ] FLS checks for field population
- [ ] Sharing context considered

### Testing
- [ ] Bulk testing (200+ records)
- [ ] Negative scenario testing
- [ ] Recursion scenario testing
- [ ] Mixed DML testing
- [ ] Test data factory used
