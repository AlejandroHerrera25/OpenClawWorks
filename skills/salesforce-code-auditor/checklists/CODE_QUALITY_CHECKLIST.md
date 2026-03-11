# Code Quality Checklist

## Overview
This checklist evaluates code for maintainability, readability, and adherence to coding standards.

---

## Code Organization

### Class Structure
- [ ] **ORG-001**: Class has clear single responsibility
- [ ] **ORG-002**: Class length < 500 lines (recommended < 300)
- [ ] **ORG-003**: Public methods < 20 per class
- [ ] **ORG-004**: Class documentation present (purpose, author, date)
- [ ] **ORG-005**: Imports organized and minimal

### Method Structure
- [ ] **METH-001**: Method length < 50 lines (recommended < 30)
- [ ] **METH-002**: Method has single responsibility
- [ ] **METH-003**: Cyclomatic complexity < 10
- [ ] **METH-004**: Parameters < 5 per method
- [ ] **METH-005**: Return type is explicit (not Object unless necessary)

### Variable Naming
- [ ] **VAR-001**: Variables have meaningful names
- [ ] **VAR-002**: No single-letter variables (except loops)
- [ ] **VAR-003**: Boolean variables have is/has/can/should prefix
- [ ] **VAR-004**: Collections named as plurals
- [ ] **VAR-005**: Constants in UPPER_SNAKE_CASE

---

## Naming Conventions

### Classes
- [ ] **NAME-001**: PascalCase for class names
- [ ] **NAME-002**: Service suffix for service classes: `AccountService`
- [ ] **NAME-003**: Selector suffix for query classes: `AccountSelector`
- [ ] **NAME-004**: Handler suffix for trigger handlers: `AccountTriggerHandler`
- [ ] **NAME-005**: Controller suffix for controllers: `AccountController`
- [ ] **NAME-006**: Test suffix for test classes: `AccountServiceTest`
- [ ] **NAME-007**: DTO suffix for data transfer objects: `AccountDTO`
- [ ] **NAME-008**: Exception suffix for exceptions: `ValidationException`

### Methods
- [ ] **METH-NAME-001**: camelCase for method names
- [ ] **METH-NAME-002**: Verbs for action methods: `createAccount`, `sendEmail`
- [ ] **METH-NAME-003**: get/set prefixes for accessors
- [ ] **METH-NAME-004**: is/has/can for boolean methods: `isActive`, `hasPermission`
- [ ] **METH-NAME-005**: Descriptive names over abbreviations

### Variables
- [ ] **VAR-NAME-001**: camelCase for variables
- [ ] **VAR-NAME-002**: Descriptive names: `accountList` not `al`
- [ ] **VAR-NAME-003**: No Hungarian notation: `strName` -> `name`
- [ ] **VAR-NAME-004**: Avoid generic names: `data`, `temp`, `item`

---

## Code Clarity

### Readability
- [ ] **READ-001**: Consistent indentation (4 spaces or tabs)
- [ ] **READ-002**: Line length < 120 characters
- [ ] **READ-003**: Blank lines separate logical sections
- [ ] **READ-004**: No excessive comments (code should be self-documenting)
- [ ] **READ-005**: Complex logic explained in comments

### Control Flow
- [ ] **FLOW-001**: Early returns for guard clauses
- [ ] **FLOW-002**: No deep nesting (max 3-4 levels)
- [ ] **FLOW-003**: Switch statements have default case
- [ ] **FLOW-004**: Ternary operators only for simple conditions
- [ ] **FLOW-005**: No empty catch blocks

### Magic Values
- [ ] **MAGIC-001**: No hardcoded strings (use constants or labels)
- [ ] **MAGIC-002**: No magic numbers (use named constants)
- [ ] **MAGIC-003**: Configuration in Custom Metadata or Custom Settings
- [ ] **MAGIC-004**: API endpoints in Named Credentials

---

## DRY Principle

### Code Duplication
- [ ] **DRY-001**: No copy-pasted code blocks
- [ ] **DRY-002**: Common logic extracted to utility methods
- [ ] **DRY-003**: Base classes for shared behavior
- [ ] **DRY-004**: Interfaces for common contracts
- [ ] **DRY-005**: Test data factory for test data creation

### Abstraction
- [ ] **ABS-001**: Appropriate abstraction level (not too high/low)
- [ ] **ABS-002**: Reusable components identified
- [ ] **ABS-003**: Configuration externalized where appropriate

---

## Error Handling

### Exception Handling
- [ ] **ERR-001**: Specific exceptions caught (not generic Exception)
- [ ] **ERR-002**: Exceptions have meaningful messages
- [ ] **ERR-003**: Exceptions logged before re-throwing
- [ ] **ERR-004**: Custom exception hierarchy defined
- [ ] **ERR-005**: User-facing errors are friendly

### Null Safety
- [ ] **NULL-001**: Null checks before dereferencing
- [ ] **NULL-002**: Safe navigation operator used where appropriate
- [ ] **NULL-003**: Default values for optional parameters
- [ ] **NULL-004**: Collections initialized (never null)

---

## Documentation

### Code Comments
- [ ] **DOC-001**: Class-level ApexDoc present
- [ ] **DOC-002**: Public methods documented
- [ ] **DOC-003**: Complex algorithms explained
- [ ] **DOC-004**: TODO comments tracked with ticket/owner
- [ ] **DOC-005**: No commented-out code

### ApexDoc Format
```apex
/**
 * @description Service class for Account operations
 * @author Developer Name
 * @date 2024-01-01
 */
public with sharing class AccountService {
    
    /**
     * @description Creates new account with validation
     * @param account Account to create
     * @return Created account with Id populated
     * @throws ValidationException if account data is invalid
     */
    public Account createAccount(Account account) {
        // Implementation
    }
}
```

---

## Dead Code

### Unused Elements
- [ ] **DEAD-001**: No unused variables
- [ ] **DEAD-002**: No unused methods
- [ ] **DEAD-003**: No unused classes
- [ ] **DEAD-004**: No commented-out code blocks
- [ ] **DEAD-005**: No TODO methods with empty implementations

### Deprecated Code
- [ ] **DEPR-001**: Deprecated methods marked with @deprecated
- [ ] **DEPR-002**: Deprecation notes explain replacement
- [ ] **DEPR-003**: Deprecated code has removal timeline

---

## Complexity Metrics

### Cyclomatic Complexity

Calculate by counting decision points:
- `if` statements
- `else if` clauses
- `for` loops
- `while` loops
- `case` statements
- `&&` and `||` operators
- `catch` blocks
- Ternary operators

**Thresholds**:
| Complexity | Risk Level | Action |
|------------|------------|--------|
| 1-10 | Low | Acceptable |
| 11-20 | Moderate | Consider refactoring |
| 21-50 | High | Should refactor |
| 50+ | Very High | Must refactor |

### Method Length Guidelines

| Length | Assessment |
|--------|------------|
| < 15 lines | Excellent |
| 15-30 lines | Good |
| 30-50 lines | Acceptable |
| 50-100 lines | Needs attention |
| > 100 lines | Must refactor |

---

## Quality Patterns

### Good Pattern Examples

```apex
// GOOD: Clear, focused method
public List<Account> getActiveAccounts(Set<Id> accountIds) {
    if (accountIds == null || accountIds.isEmpty()) {
        return new List<Account>();
    }
    
    return [
        SELECT Id, Name, Industry
        FROM Account
        WHERE Id IN :accountIds
        AND Status__c = :STATUS_ACTIVE
        WITH SECURITY_ENFORCED
    ];
}

// GOOD: Named constant instead of magic value
private static final String STATUS_ACTIVE = 'Active';
private static final Integer MAX_BATCH_SIZE = 200;

// GOOD: Descriptive variable names
Map<Id, Account> accountsById = new Map<Id, Account>(accounts);
Set<String> uniqueIndustries = new Set<String>();
List<Contact> primaryContacts = new List<Contact>();
```

### Bad Pattern Examples

```apex
// BAD: Unclear method name, magic numbers
public List<Account> getData(Set<Id> ids) {
    List<Account> a = [SELECT Id, Name FROM Account WHERE Id IN :ids];
    if (a.size() > 100) {  // Magic number
        // ...
    }
    return a;
}

// BAD: Deep nesting
if (condition1) {
    if (condition2) {
        if (condition3) {
            for (Item i : items) {
                if (condition4) {
                    // Too deep!
                }
            }
        }
    }
}
```
