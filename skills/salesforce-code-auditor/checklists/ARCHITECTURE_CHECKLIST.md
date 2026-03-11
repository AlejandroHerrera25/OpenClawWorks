# Architecture Audit Checklist

## Overview
This checklist evaluates Salesforce code architecture for maintainability, scalability, and alignment with enterprise patterns.

---

## CRITICAL Architecture Issues (Severity 1)

### Circular Dependencies
- [ ] **CIRC-001**: No circular class dependencies
- [ ] **CIRC-002**: No circular trigger dependencies
- [ ] **CIRC-003**: No circular Flow/Process Builder dependencies
- [ ] **CIRC-004**: Dependency graph is acyclic

**Detection**:
```
ClassA depends on ClassB
ClassB depends on ClassC
ClassC depends on ClassA  <-- CIRCULAR!
```

### God Classes
- [ ] **GOD-001**: No classes > 1000 lines
- [ ] **GOD-002**: No classes with > 20 public methods
- [ ] **GOD-003**: Single Responsibility Principle followed
- [ ] **GOD-004**: Classes have clear, focused purpose

### Mixed Concerns in Triggers
- [ ] **MIX-001**: Trigger bodies contain only handler delegation
- [ ] **MIX-002**: No business logic in trigger bodies
- [ ] **MIX-003**: No SOQL in trigger bodies
- [ ] **MIX-004**: No DML in trigger bodies

---

## HIGH Architecture Issues (Severity 2)

### Layer Separation

#### Controller Layer
- [ ] **CTRL-001**: Controllers only handle input/output
- [ ] **CTRL-002**: Controllers delegate to service layer
- [ ] **CTRL-003**: No direct SOQL in controllers
- [ ] **CTRL-004**: No direct DML in controllers (except simple cases)
- [ ] **CTRL-005**: Error handling converts exceptions to user messages

#### Service Layer
- [ ] **SVC-001**: Business logic encapsulated in services
- [ ] **SVC-002**: Services are stateless
- [ ] **SVC-003**: Services use dependency injection for selectors
- [ ] **SVC-004**: Transaction boundaries managed in services
- [ ] **SVC-005**: Services don't directly expose SObjects to UI

#### Selector Layer
- [ ] **SEL-001**: All SOQL queries in selector classes
- [ ] **SEL-002**: Selectors enforce security
- [ ] **SEL-003**: Selectors return consistent field sets
- [ ] **SEL-004**: Selectors are mockable for testing
- [ ] **SEL-005**: No business logic in selectors

#### Domain Layer
- [ ] **DOM-001**: Object-specific logic in domain classes
- [ ] **DOM-002**: Validations in domain layer
- [ ] **DOM-003**: Field derivations in domain layer
- [ ] **DOM-004**: Trigger handlers delegate to domain
- [ ] **DOM-005**: Domain classes operate on collections

### Trigger Architecture
- [ ] **TRIG-001**: Single trigger per object
- [ ] **TRIG-002**: Trigger handler framework used
- [ ] **TRIG-003**: Recursion control implemented
- [ ] **TRIG-004**: Bypass mechanism available
- [ ] **TRIG-005**: Context variables cached in handler

### Error Handling
- [ ] **ERR-001**: Custom exception hierarchy defined
- [ ] **ERR-002**: Exceptions contain meaningful messages
- [ ] **ERR-003**: Exceptions logged before re-throwing
- [ ] **ERR-004**: User-facing errors are friendly
- [ ] **ERR-005**: System errors don't expose internals

---

## MEDIUM Architecture Issues (Severity 3)

### Design Patterns

#### Factory Pattern
- [ ] **FACT-001**: Factory used for complex object creation
- [ ] **FACT-002**: Factory abstracts implementation details
- [ ] **FACT-003**: Factory supports testing via injection

#### Strategy Pattern
- [ ] **STRAT-001**: Strategy used for varying algorithms
- [ ] **STRAT-002**: Strategies implement common interface
- [ ] **STRAT-003**: Strategy selection externalized

#### Unit of Work Pattern
- [ ] **UOW-001**: Unit of Work used for complex transactions
- [ ] **UOW-002**: DML operations registered, not executed immediately
- [ ] **UOW-003**: Commit at end of business transaction
- [ ] **UOW-004**: Rollback handled properly

### Dependency Injection
- [ ] **DI-001**: Dependencies injected, not created internally
- [ ] **DI-002**: Interfaces used for injectable dependencies
- [ ] **DI-003**: Test-visible constructors for injection
- [ ] **DI-004**: Default implementations provided

### Configuration Management
- [ ] **CONFIG-001**: Custom Metadata for declarative config
- [ ] **CONFIG-002**: Custom Settings for hierarchy config
- [ ] **CONFIG-003**: No hardcoded values in code
- [ ] **CONFIG-004**: Feature flags for gradual rollout

### Naming Conventions
- [ ] **NAME-001**: Classes use PascalCase
- [ ] **NAME-002**: Methods use camelCase
- [ ] **NAME-003**: Constants use UPPER_SNAKE_CASE
- [ ] **NAME-004**: Test classes suffixed with 'Test'
- [ ] **NAME-005**: Interfaces prefixed with 'I' or suffixed with 'Interface'

---

## LOW Architecture Issues (Severity 4)

### Code Organization
- [ ] **ORG-001**: Related classes in same namespace/folder
- [ ] **ORG-002**: Test classes mirror production structure
- [ ] **ORG-003**: Utility classes grouped together
- [ ] **ORG-004**: DTOs clearly identified

### Documentation
- [ ] **DOC-001**: Class-level documentation present
- [ ] **DOC-002**: Complex methods documented
- [ ] **DOC-003**: Public APIs documented
- [ ] **DOC-004**: Architecture decisions documented

### Technical Debt
- [ ] **DEBT-001**: TODO comments tracked
- [ ] **DEBT-002**: Deprecated code marked
- [ ] **DEBT-003**: Legacy code documented
- [ ] **DEBT-004**: Refactoring opportunities identified

---

## Architecture Patterns Reference

### Recommended Layer Structure

```
┌──────────────────────────────────────────────────┐
│              UI Layer                            │
│   (LWC, Aura, Visualforce, REST Resources)       │
└───────────────────────┬──────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────┐
│           Controller Layer                       │
│    (Input validation, Response formatting)       │
└───────────────────────┬──────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────┐
│           Service Layer                          │
│  (Business logic, Transaction management)        │
└───────────┬──────────────────────────┬────────────┘
            │                          │
            ▼                          ▼
┌───────────────────────┐  ┌───────────────────────┐
│    Domain Layer       │  │   Selector Layer      │
│ (Business rules,      │  │ (Data access,         │
│  Validations)         │  │  Queries)             │
└───────────────────────┘  └───────────────────────┘
```

### File Organization

```
force-app/main/default/
├── classes/
│   ├── controllers/
│   │   ├── AccountController.cls
│   │   └── AccountControllerTest.cls
│   ├── services/
│   │   ├── AccountService.cls
│   │   └── AccountServiceTest.cls
│   ├── selectors/
│   │   ├── AccountSelector.cls
│   │   └── AccountSelectorTest.cls
│   ├── domain/
│   │   ├── Accounts.cls
│   │   └── AccountsTest.cls
│   ├── triggers/
│   │   ├── AccountTrigger.trigger
│   │   ├── AccountTriggerHandler.cls
│   │   └── AccountTriggerHandlerTest.cls
│   ├── dtos/
│   │   └── AccountDTO.cls
│   ├── utilities/
│   │   ├── StringUtils.cls
│   │   └── DateUtils.cls
│   └── exceptions/
│       ├── ApplicationException.cls
│       ├── ValidationException.cls
│       └── IntegrationException.cls
├── lwc/
│   ├── accountList/
│   ├── accountDetail/
│   └── accountForm/
└── triggers/
    └── AccountTrigger.trigger
```

---

## Architecture Decision Records (ADR)

For each significant architectural decision, document:

```markdown
# ADR-001: Use Service Layer Pattern

## Status
Accepted

## Context
Need consistent business logic handling across UI, API, and batch contexts.

## Decision
Implement service layer pattern with:
- Services contain all business logic
- Controllers only handle input/output
- Selectors contain all queries
- Domain classes for object-specific rules

## Consequences
- Positive: Testable, maintainable, reusable
- Negative: More classes, learning curve
```
