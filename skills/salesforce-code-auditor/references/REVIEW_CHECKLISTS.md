# Review Checklists — Quick Reference

## Overview

This document provides quick-reference checklists for code reviews, organized by review focus area.

---

## Quick Security Review

### Must Check (All Code)
- [ ] No SOQL injection (use bind variables)
- [ ] FLS enforced (WITH SECURITY_ENFORCED or stripInaccessible)
- [ ] CRUD checked before DML
- [ ] Sharing declared (with sharing on controllers)
- [ ] No hardcoded credentials
- [ ] No XSS vulnerabilities

### Red Flags
```apex
// IMMEDIATE FIX REQUIRED
Database.query('SELECT ... WHERE Name = \'' + userInput + '\'');
acc.put(fieldName, value); // Without FLS check
insert record; // Without CRUD check
public class Controller { // Missing sharing declaration
String apiKey = 'sk_live_...'; // Hardcoded credential
```

---

## Quick Performance Review

### Must Check
- [ ] No SOQL in loops
- [ ] No DML in loops
- [ ] Queries have LIMIT or are bounded
- [ ] Maps used for lookups
- [ ] Collections used for bulk DML

### Red Flags
```apex
// IMMEDIATE FIX REQUIRED
for (Account acc : accounts) {
    List<Contact> contacts = [SELECT Id FROM Contact WHERE AccountId = :acc.Id];
}

for (Account acc : accounts) {
    update acc;
}

List<Account> all = [SELECT Id FROM Account]; // Unbounded
```

---

## Quick Architecture Review

### Must Check
- [ ] Single trigger per object
- [ ] Trigger delegates to handler
- [ ] Business logic not in trigger body
- [ ] Recursion control implemented
- [ ] Service layer for shared logic

### Red Flags
```apex
// NEEDS REFACTORING
trigger AccountTrigger1 on Account (before insert) { } // Multiple triggers
trigger AccountTrigger2 on Account (before insert) { }

trigger AccountTrigger on Account (before insert) {
    // 100+ lines of logic in trigger body
}

public class AccountService {
    // 1000+ lines - God class
}
```

---

## Quick Test Review

### Must Check
- [ ] Test has assertions
- [ ] Assertions have messages
- [ ] Bulk testing present (200+ records)
- [ ] Negative scenarios tested
- [ ] No hardcoded IDs
- [ ] No SeeAllData=true

### Red Flags
```apex
// NEEDS IMPROVEMENT
@IsTest
static void testMethod() {
    insert new Account(Name = 'Test');
    // No assertions!
}

@IsTest(SeeAllData=true) // Avoid

Account acc = [SELECT Id FROM Account WHERE Id = '001000000000001']; // Hardcoded ID
```

---

## Quick LWC Review

### Must Check
- [ ] No innerHTML with user data
- [ ] Wire service for reactive data
- [ ] Error handling for async operations
- [ ] Toast notifications for user feedback
- [ ] cacheable=true for read-only Apex

### Red Flags
```javascript
// NEEDS FIX
this.template.querySelector('div').innerHTML = userInput; // XSS risk
await saveRecord(); // No try/catch

// In Apex controller
@AuraEnabled // Missing cacheable=true for read operation
public static List<Account> getAccounts() { }
```

---

## Quick Trigger Review

### Must Check
- [ ] Uses handler framework
- [ ] Recursion control present
- [ ] Bypass mechanism available
- [ ] Context properly handled
- [ ] Bulk safe operations

### Trigger Checklist
```apex
// GOOD PATTERN
trigger AccountTrigger on Account (before insert, after insert, before update, after update) {
    if (TriggerSettings__c.getInstance().Disable_Account_Trigger__c) {
        return; // Feature flag
    }
    new AccountTriggerHandler().run(); // Delegate to handler
}
```

---

## Quick Integration Review

### Must Check
- [ ] Named Credentials used
- [ ] Timeout configured
- [ ] Error handling complete
- [ ] Retry logic for transient failures
- [ ] Response validated

### Red Flags
```apex
// NEEDS FIX
req.setHeader('Authorization', 'Bearer ' + apiKey); // Should use Named Credentials
Http http = new Http();
HttpResponse res = http.send(req); // No timeout set
return res.getBody(); // No status code check
```

---

## Severity Quick Reference

| Severity | Response Time | Examples |
|----------|--------------|----------|
| CRITICAL | Immediate fix | SOQL injection, hardcoded credentials, missing sharing |
| HIGH | This sprint | SOQL in loop, missing FLS, no error handling |
| MEDIUM | Next sprint | Code duplication, missing tests, poor naming |
| LOW | Backlog | Documentation, formatting, minor optimizations |

---

## Review Sign-Off

### Before Approval

- [ ] All CRITICAL issues resolved
- [ ] All HIGH issues resolved or tracked
- [ ] Test coverage meets minimum (75%+)
- [ ] Security scan passed
- [ ] Performance tested with bulk data
- [ ] Code follows project patterns

### Approval Statement

```
Code Review: [APPROVED / APPROVED WITH CONDITIONS / REJECTED]

Reviewer: [Name]
Date: [Date]

Conditions (if any):
- [ ] [Condition 1]
- [ ] [Condition 2]

Notes:
[Any additional notes]
```
