# Token Optimization Strategy

## Overview

The Salesforce Code Auditor uses a token-efficient approach to analyze codebases. This document describes the strategy for minimizing token usage while maximizing analysis quality.

---

## Core Principles

### 1. Never Load All Code Simultaneously

Loading entire codebases wastes tokens on irrelevant code. Instead:
- Index files first (metadata only)
- Detect entry points
- Trace dependencies
- Load only required code

### 2. Progressive Depth Analysis

```
Phase 1: Index (5% tokens)
    └── File names, sizes, types
    
 Phase 2: Entrypoints (10% tokens)
    └── Controllers, triggers, REST resources
    
 Phase 3: Dependency Graph (25% tokens)
    └── Class relationships, method calls
    
 Phase 4: Deep Analysis (40% tokens)
    └── Security, performance, architecture
    
 Phase 5: Report Generation (20% tokens)
    └── Findings, recommendations
```

### 3. Snippet-Based Analysis

Instead of loading full files:
- Extract specific methods
- Load only relevant sections
- Use line ranges when possible

---

## Token Budget Allocation

### Small Codebase (< 50 files)

| Phase | Budget % | Tokens (100K total) |
|-------|----------|--------------------|
| Indexing | 5% | 5,000 |
| Entrypoint Detection | 10% | 10,000 |
| Dependency Analysis | 20% | 20,000 |
| Deep Analysis | 45% | 45,000 |
| Report Generation | 20% | 20,000 |

### Medium Codebase (50-200 files)

| Phase | Budget % | Tokens (200K total) |
|-------|----------|--------------------|
| Indexing | 3% | 6,000 |
| Entrypoint Detection | 7% | 14,000 |
| Dependency Analysis | 25% | 50,000 |
| Deep Analysis | 45% | 90,000 |
| Report Generation | 20% | 40,000 |

### Large Codebase (200+ files)

| Phase | Budget % | Tokens (500K total) |
|-------|----------|--------------------|
| Indexing | 2% | 10,000 |
| Entrypoint Detection | 5% | 25,000 |
| Dependency Analysis | 20% | 100,000 |
| Deep Analysis | 50% | 250,000 |
| Report Generation | 23% | 115,000 |

---

## Phase 1: Indexing Strategy

### Minimal Index Entry
```json
{
  "path": "classes/AccountService.cls",
  "type": "apex_class",
  "size": 4523,
  "category": "service",
  "priority": "high"
}
```

### Category Detection (No Content Load)

Detect category from file name patterns:
- `*Controller.cls` → controller
- `*Service.cls` → service
- `*Selector.cls` → selector
- `*Handler.cls` → trigger_handler
- `*Test.cls` → test
- `*.trigger` → trigger
- `*DTO.cls` → dto

---

## Phase 2: Entrypoint Detection

### Quick Scan Patterns

Scan only first 50-100 lines for annotations:

```apex
// Controller indicators (scan for these)
@AuraEnabled
@RemoteAction
@RestResource
@HttpGet
@HttpPost

// Trigger indicators
trigger AccountTrigger on Account

// Batch/Async indicators
implements Database.Batchable
implements Queueable
@future
```

### Token-Efficient Scan

```
FOR each file:
    READ first 100 lines only
    SCAN for annotation patterns
    IF entrypoint found:
        ADD to entrypoint list
    END IF
END FOR
```

---

## Phase 3: Dependency Analysis

### Incremental Dependency Building

1. **Start from entrypoints**
2. **Trace method calls** (load only method signatures)
3. **Build graph incrementally**
4. **Stop at depth 5** (configurable)

### Efficient Dependency Detection

Scan for patterns without loading full content:

```apex
// Class instantiation
new ClassName(

// Method calls
ClassName.methodName(
this.dependency.method(

// Inheritance
extends BaseClass
implements Interface
```

---

## Phase 4: Deep Analysis

### Targeted Analysis

Prioritize analysis based on:

1. **Security-sensitive code**
   - Controllers (user input handling)
   - SOQL queries (injection risk)
   - DML operations (CRUD checks)

2. **Performance-critical code**
   - Triggers (bulk operations)
   - Batch execute methods
   - Loop bodies

3. **Architecture-significant code**
   - Service layer methods
   - Base classes
   - Interfaces

### Snippet Extraction

Load only specific methods:

```
REQUEST: Load method `processAccounts` from `AccountService.cls`

INSTEAD OF: Loading entire 500-line class

LOAD ONLY: Lines 45-89 (the method body)
```

---

## Phase 5: Report Generation

### Finding Deduplication

- Group similar findings
- Reference first occurrence
- List additional locations

### Template-Based Output

Use templates to reduce token usage:

```markdown
### {FINDING_ID}: {FINDING_TITLE}

**Location**: {FILE}:{LINE}
**Severity**: {SEVERITY}
**Pattern**: {PATTERN_ID}

{CODE_SNIPPET}

**Remediation**: See {PATTERN_ID} in references.
```

---

## Optimization Techniques

### 1. Caching

- Cache index results
- Cache dependency graphs
- Reuse for incremental audits

### 2. Prioritization

- Critical paths first
- Skip test classes in initial analysis
- Focus on changed files in follow-up audits

### 3. Early Termination

- Stop if blocking issues found early
- Report critical findings immediately
- Defer low-priority analysis

### 4. Compression

- Use abbreviated patterns in findings
- Reference documentation instead of inline
- Use IDs for known vulnerabilities

---

## Token Tracking

### During Analysis

```
TOKENS_USED: 0
BUDGET: 100000

[Phase 1] Indexing: +2,341 tokens (2,341 total, 97,659 remaining)
[Phase 2] Entrypoints: +8,456 tokens (10,797 total, 89,203 remaining)
[Phase 3] Dependencies: +23,102 tokens (33,899 total, 66,101 remaining)
[Phase 4] Analysis: +41,234 tokens (75,133 total, 24,867 remaining)
[Phase 5] Reporting: +18,543 tokens (93,676 total, 6,324 remaining)

FINAL: 93,676 / 100,000 tokens used (93.7%)
```

### Budget Exceeded Handling

```
IF tokens_used > budget * 0.8:
    SWITCH to minimal mode:
        - Stop deep analysis
        - Report findings so far
        - Note incomplete analysis
        - Recommend follow-up audit
END IF
```

---

## Configuration Options

```yaml
token_strategy:
  budget: 100000
  phases:
    indexing: 0.05
    entrypoints: 0.10
    dependencies: 0.25
    analysis: 0.40
    reporting: 0.20
  options:
    max_depth: 5
    max_file_size: 10000  # lines
    skip_tests: false
    priority_only: false
```
