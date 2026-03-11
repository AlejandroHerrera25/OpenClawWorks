---
name: salesforce-code-auditor
description: A production-ready skill for progressive technical analysis of Salesforce codebases (Apex, LWC, Visualforce, Triggers, Flows, Metadata) with token-efficient auditing. Enhanced with enterprise-grade security, performance, and architecture validation.
user-invocable: true
command-dispatch: salesforce-code-auditor
version: 2.0.0
author: OpenClaw Salesforce Expert
tags:
  - salesforce
  - apex
  - lwc
  - security
  - performance
  - code-review
  - architecture
---

# Salesforce Code Auditor Skill v2.0 — Enterprise Hardened Edition

## Overview

A production-ready skill for **progressive technical analysis of Salesforce codebases** (Apex, LWC, Visualforce, Triggers, Flows, Metadata) with **token-efficient auditing**. The agent requests only the minimal necessary code to reconstruct the real execution logic of a process.

Designed to **work together with the `salesforce-architect` skill** as a **subordinate validator** under architect governance.

### Key Capabilities
- **Security Analysis**: FLS, CRUD, Sharing Rules, SOQL/SOSL Injection, XSS, CSRF
- **Performance Analysis**: Governor Limits, Bulkification, Query Optimization
- **Architecture Analysis**: Design Patterns, Separation of Concerns, Technical Debt
- **Integration Analysis**: Callout Patterns, Error Handling, Circuit Breakers
- **Test Coverage Analysis**: Test Patterns, Assertions, Mock Strategies

---

## HARDENED ARCHITECT INTEGRATION

### Governance Relationship
The code-auditor operates as a **subordinate validator** to the salesforce-architect. All audits must be:
- Project-scoped under architect control
- Invoked through defined handoff modes
- Returning architect-consumable outputs
- Subject to architect review and validation

### Handoff Modes (Governance Contract)
The architect invokes the auditor using defined handoff modes from `CODE_AUDIT_HANDOFF_MODES.md`:

1. **Mode A — Architecture → Code Audit**
   - **When**: Architect needs current-state technical truth before design decisions
   - **Request**: Clear audit objectives, scope, context
   - **Response**: Technical assessment, constraints, recommendations

2. **Mode B — Code Audit → Architecture**
   - **When**: Audit findings must change architecture decisions
   - **Request**: Focus on specific concerns, architectural context
   - **Response**: Critical findings, architectural impact, remediation options

3. **Mode C — Design Validation Mode**
   - **When**: Architect needs to validate if implementation supports proposed design
   - **Request**: Design context, validation objectives, specific points
   - **Response**: Feasibility assessment, gap analysis, implementation complexity

4. **Mode D — Security Deep Dive** (NEW)
   - **When**: Security-focused audit required before deployment
   - **Request**: Security requirements, compliance needs, threat model
   - **Response**: Vulnerability assessment, remediation priorities, compliance gaps

5. **Mode E — Performance Optimization** (NEW)
   - **When**: Performance issues detected or optimization required
   - **Request**: Performance requirements, SLAs, bottleneck indicators
   - **Response**: Performance hotspots, optimization recommendations, capacity analysis

### Required Output Format for Architect Consumption
All audit reports must be structured for direct architect consumption:

```
## Code Audit Report - Mode <A/B/C/D/E>

**Project**: <project_key>
**Audit Case ID**: <case_id>
**Mode**: <A/B/C/D/E>
**Severity Distribution**: CRITICAL: X | HIGH: X | MEDIUM: X | LOW: X

### Executive Summary
- Overall code health assessment (score: X/100)
- Key findings summary
- Architectural implications
- Blocking issues count

### Technical Assessment
- Code structure and organization
- Design patterns used
- Technical debt identified
- Performance characteristics
- Security posture

### Constraints & Limitations
- Technical constraints for new development
- Integration limitations
- Scalability constraints
- Security limitations

### Risk Assessment
- **CRITICAL (Sev1)**: Security vulnerabilities, data loss risks, performance failures
- **HIGH (Sev2)**: Significant security/performance issues, major code quality problems
- **MEDIUM (Sev3)**: Code quality issues, performance optimizations, minor security concerns
- **LOW (Sev4)**: Code style issues, documentation improvements, test coverage

### Recommendations for Architecture
1. <recommendation 1>
2. <recommendation 2>
3. <recommendation 3>

### Evidence
- Code snippets supporting findings
- Performance metrics
- Security vulnerability details
- Design pattern analysis
```

### Blocking Conditions for Architectural Finalization
Findings that **block architectural finalization**:
- CRITICAL security vulnerabilities without approved mitigation
- Architectural flaws requiring design changes
- Performance issues making solution unusable
- Integration failures preventing core functionality
- Missing FLS/CRUD checks in user-facing operations
- Unhandled exceptions in critical paths
- SOQL injection vulnerabilities
- Cross-site scripting (XSS) vulnerabilities

**Incident emission for blocking findings**: `salesforce|CODE_AUDIT|design_alignment_gap|review_required`

---

## Workspace Code Intake Model

The user must place code inside a case folder created by the skill.

Directory created automatically:
`<workspace>/projects/<project_key>/code_audit/<case_id>/inputs/`

Supported formats:
- Apex `.cls`
- Apex Triggers `.trigger`
- LWC `.js`, `.html`, `.xml`
- Aura Components `.cmp`, `.app`, `.evt`
- Visualforce `.page`, `.component`
- Metadata `.xml`
- Flow metadata `-flow.xml`
- Custom Labels `.labels`
- Permission Sets `.permissionset`
- Profiles `.profile`
- Objects `.object`
- DTO / integration classes

The skill **indexes files first instead of reading them immediately**.

---

## Required Runtime Structure

```
<workspace>/projects/<project_key>/code_audit/<case_id>/
  CASE.md
  inputs/
  work/
    snippets/
    temp_analysis/
  outputs/
    INDEX.md
    MANIFEST.json
    DEPENDENCY_GRAPH.json
    ENTRYPOINTS.json
    EXECUTION_TRACE.md
    FINDINGS.md
    TEST_MATRIX.md
    SECURITY_ASSESSMENT.md
    PERFORMANCE_ASSESSMENT.md
    ARCHITECTURE_ASSESSMENT.md
    AUDIT_REPORT.md
```

---

## Skill Directory Structure

```
skills/salesforce-code-auditor/
  SKILL.md (this file)
  references/
    FILE_TYPES.md
    REVIEW_CHECKLISTS.md
    TOKEN_STRATEGY.md
    REPORT_TEMPLATE.md
    GOVERNOR_LIMITS.md
    SECURITY_CONTROLS.md
    APEX_BEST_PRACTICES.md
    LWC_BEST_PRACTICES.md
    TRIGGER_PATTERNS.md
    INTEGRATION_PATTERNS.md
    TEST_PATTERNS.md
  templates/
    audit_report_template.md
    security_assessment_template.md
    performance_assessment_template.md
    architecture_assessment_template.md
    findings_template.md
  checklists/
    SECURITY_CHECKLIST.md
    PERFORMANCE_CHECKLIST.md
    ARCHITECTURE_CHECKLIST.md
    CODE_QUALITY_CHECKLIST.md
    TEST_COVERAGE_CHECKLIST.md
    LWC_CHECKLIST.md
    TRIGGER_CHECKLIST.md
    INTEGRATION_CHECKLIST.md
  patterns/
    ANTI_PATTERNS.md
    DESIGN_PATTERNS.md
    TRIGGER_FRAMEWORKS.md
    SERVICE_LAYER_PATTERNS.md
    SELECTOR_PATTERNS.md
    DOMAIN_PATTERNS.md
  security/
    VULNERABILITY_CATALOG.md
    FLS_CRUD_GUIDE.md
    INJECTION_PREVENTION.md
    XSS_PREVENTION.md
    SHARING_RULES.md
    ENCRYPTION_GUIDE.md
  performance/
    GOVERNOR_LIMITS_DEEP_DIVE.md
    QUERY_OPTIMIZATION.md
    BULKIFICATION_GUIDE.md
    ASYNC_PATTERNS.md
    CACHING_STRATEGIES.md
  architecture/
    SEPARATION_OF_CONCERNS.md
    DEPENDENCY_INJECTION.md
    ERROR_HANDLING_PATTERNS.md
    LOGGING_PATTERNS.md
  examples/
    example_intake.md
    example_manifest.md
    example_audit_report.md
    example_findings.md
```

---

## Complete Reporting Layer

The skill includes a complete reporting layer that:

### 1. Findings Synthesis
- **Input**: Parsed dependencies from code analysis
- **Output**: Specific, actionable findings with:
  - Code location (file:line:column)
  - Severity (CRITICAL/HIGH/MEDIUM/LOW)
  - Category (Security/Performance/Architecture/Quality)
  - Pattern detected (SOQL in loop, missing FLS, etc.)
  - CWE/CVE reference where applicable
  - Recommendation (specific fix suggestion)
  - Impact (performance, security, maintainability)
  - Effort estimate (hours)
  - Code snippet with highlighted issue

### 2. Risk Assessment
- **CRITICAL**: Security vulnerabilities, data loss risks, compliance violations
- **HIGH**: Performance issues, major design flaws, data integrity risks
- **MEDIUM**: Code quality issues, maintainability concerns, minor security issues
- **LOW**: Style issues, minor optimizations, documentation gaps
- **Blocking Conditions**: Identifies findings that block architectural finalization

### 3. Complete Audit Reports
Produces architect-consumable reports that:
- Include executive summary with health score
- List findings by severity and category
- Show code snippets with issues highlighted
- Provide specific recommendations with effort estimates
- Include dependency graphs
- Format for architect consumption
- Include remediation roadmap

### 4. Integration Standards
- Uses formats from `CODE_AUDIT_HANDOFF_MODES.md`
- Preserves project context
- Stores artifacts in project folder
- Enables architect to consume findings

---

## PROJECT STATE MACHINE INTEGRATION

### Audit Timing in Project Lifecycle
Audits must align with project state from `SALESFORCE_PROJECT_STATE_MACHINE.md`:

1. **DISCOVERY phase**: Mode A audits to understand current codebase
2. **DESIGN phase**: Mode C audits to validate design feasibility
3. **ARCH_REVIEW phase**: Mode B audits for architectural validation
4. **CODE_AUDIT phase**: Formal audit as part of state progression
5. **SECURITY_REVIEW phase**: Mode D audits for security validation
6. **PERFORMANCE_REVIEW phase**: Mode E audits for performance validation
7. **REMEDIATION phase**: Follow-up audits to validate fixes

### State Transition Impact
- **CODE_AUDIT → ARCH_REVIEW**: Findings may require architectural changes
- **ARCH_REVIEW → REMEDIATION**: Critical findings require remediation
- **REMEDIATION → FINALIZED**: All blocking findings must be resolved
- **Any state → CODE_AUDIT**: Can trigger audit at any phase if needed

### Project README Integration
The auditor must update project README with audit information:

```
## Code Audits
- Case ID: <case_id>
- Mode: <A/B/C/D/E>
- Date: <timestamp>
- Findings: <summary>
- Health Score: <score>/100
- Status: <open / in remediation / closed>

## Audit History
- <case_id_1>: <date> - <mode> - <status> - <score>
- <case_id_2>: <date> - <mode> - <status> - <score>
```

---

## Analysis Methodology

Reconstruct system behavior in this order:

### 1 — UI Layer
Identify entry points: Visualforce pages, Lightning Web Components, Aura Components, Flow Screens
Detect: buttons, actions, Apex calls, events, wire services, imperative calls

**LWC Specific Analysis**:
- Wire adapters usage
- Imperative Apex calls
- Event handling (CustomEvent, LMS)
- Navigation service usage
- Platform event subscriptions
- Security: locker service compliance, CSP violations

### 2 — Controller Layer
Analyze controller classes called by the UI.
Detect: invoked methods, validations, business logic, SOQL queries, DML operations

**Analysis Points**:
- Method visibility (public vs private)
- AuraEnabled/RemoteAction annotations
- Cacheable methods appropriateness
- Input validation
- Error handling patterns
- FLS/CRUD enforcement

### 3 — Service Layer
Trace service classes implementing business logic:
- Transaction management
- Unit of Work patterns
- Domain logic encapsulation
- Cross-object operations

### 4 — Selector Layer
Analyze query classes:
- Query optimization
- Field selection efficiency
- Filter criteria
- Relationship queries
- Aggregate queries
- Security enforcement in queries

### 5 — Domain Layer
Examine domain logic:
- Validation rules in code
- Field defaults
- Derived fields
- Domain events

### 6 — Integration and DTO Layer
Identify classes responsible for:
- Callouts (HTTP, SOAP, REST)
- Response parsing
- External API integrations
- DTO transport objects
- Named credentials usage
- Certificate management
- Circuit breaker patterns
- Retry logic

### 7 — Triggers
Detect triggers related to objects used by the process.
Analyze:
- Trigger context events
- Automation side effects
- Recursive logic risks
- Trigger framework usage
- Order of execution awareness
- Bulk safety

### 8 — Metadata and Automation
Detect:
- Flows (Screen, Record-Triggered, Scheduled, Platform Event)
- Process Builders (deprecated)
- Platform Events
- Async logic (Queueable, Batch, Schedulable, Future)
- Custom Metadata Types
- Custom Settings

### 9 — Test Classes
Analyze test coverage:
- Test method patterns
- Assertion quality
- Test data factories
- Mock implementations
- Bulk test scenarios
- Negative test cases
- Integration test patterns

---

## Token Optimization Strategy

**Never load all code simultaneously.**

Procedure:
1. Index files using file system scan
2. Detect entrypoints from annotations and metadata
3. Request specific files or snippets
4. Extract only required methods
5. Build incremental understanding

The analysis proceeds **incrementally**.

### Token Budget Allocation
- **Phase 1 - Indexing**: 5% of budget
- **Phase 2 - Entrypoint Detection**: 10% of budget
- **Phase 3 - Dependency Tracing**: 25% of budget
- **Phase 4 - Deep Analysis**: 40% of budget
- **Phase 5 - Report Generation**: 20% of budget

---

## SFDX Support

Supports both:
- Option A — SFDX structure: `force-app/main/default/`
- Option B — loose files in `inputs/`
- Option C — Metadata API format: `src/`
- Option D — Unlocked Package structure

The indexing must detect all formats automatically.

---

## Dependency Reconstruction

Generate `DEPENDENCY_GRAPH.json` containing:
- Class dependencies (inheritance, composition, usage)
- Method calls (internal and external)
- Trigger relationships
- Integration flows
- LWC component hierarchy
- Event dependencies
- Platform event subscriptions
- Flow dependencies
- Custom metadata dependencies

---

## Execution Trace

Generate `EXECUTION_TRACE.md` describing runtime order:
UI → Controller → Service → Selector → Domain → Integration → Triggers → Async

Include:
- Governor limit consumption at each step
- Transaction boundaries
- Async breakpoints
- Callout points
- DML operations
- Query operations

---

## Audit Findings Categories

`FINDINGS.md` must identify issues across these categories:

### Security Findings
- Missing FLS checks
- Missing CRUD checks
- Sharing rule violations
- SOQL/SOSL injection risks
- XSS vulnerabilities
- CSRF vulnerabilities
- Sensitive data exposure
- Hardcoded credentials
- Insecure direct object references
- Missing input validation
- Insufficient logging

### Performance Findings
- Governor limit risks
- SOQL in loops
- DML in loops
- Inefficient queries
- Missing selective filters
- Unbounded queries
- Recursive triggers
- Synchronous callouts in triggers
- Large data volume issues
- CPU time concerns
- Heap size risks

### Architecture Findings
- Mixed responsibilities
- Tight coupling
- Missing abstraction layers
- Circular dependencies
- God classes
- Dead code
- Duplicated logic
- Missing error handling
- Inconsistent naming
- Missing documentation

### Quality Findings
- Low test coverage
- Missing assertions
- Test data in tests
- Hardcoded IDs
- Magic numbers
- Complex methods (high cyclomatic complexity)
- Long methods
- Deep nesting
- Inconsistent formatting

---

## Testing Matrix

Generate `TEST_MATRIX.md` containing:
- Scenario ID
- Trigger action
- Expected system behavior
- Related code location
- Bulk scenario (1/200/10000 records)
- Negative scenario
- Security scenario (different user profiles)
- Performance scenario (with/without data)

---

## Final Audit Report

`AUDIT_REPORT.md` must include:
- Executive Summary with Health Score
- Methodology Used
- Scope and Limitations
- Architecture Observations
- Technical Risks with Severity
- Performance Risks with Metrics
- Security Risks with CVE/CWE References
- Code Quality Metrics
- Refactor Opportunities with Effort Estimates
- Design Alignment Analysis
- Remediation Roadmap
- Appendices

The last section must compare the real code behaviour against outputs produced by the **salesforce-architect skill** when available.

---

## Integration with Learning System

If critical issues are detected append incidents to `workspace/.learnings/ERRORS.md`.

Example pattern keys:
- `security|FLS_MISSING|apex|<class_name>`
- `security|CRUD_MISSING|apex|<class_name>`
- `security|SOQL_INJECTION|apex|<class_name>`
- `security|XSS_VULNERABILITY|lwc|<component_name>`
- `security|SHARING_VIOLATION|apex|<class_name>`
- `limits|SOQL_IN_LOOP|apex|<class_name>`
- `limits|DML_IN_LOOP|apex|<class_name>`
- `limits|CPU_RISK|apex|<class_name>`
- `limits|HEAP_RISK|apex|<class_name>`
- `architecture|MIXED_CONCERNS|controller|<class_name>`
- `architecture|GOD_CLASS|apex|<class_name>`
- `architecture|CIRCULAR_DEPENDENCY|apex|<class_names>`
- `integration|UNHANDLED_CALLOUT_FAILURE|<class_name>`
- `integration|MISSING_RETRY|<class_name>`
- `test|LOW_COVERAGE|apex|<class_name>`
- `test|MISSING_ASSERTIONS|apex|<test_class_name>`

Then trigger error-learning-loop index rebuild fallback.

---

## Demonstration Test

Run a demo case: `demo_code_audit`

The test must:
1. Create case folder
2. Simulate input files
3. Generate INDEX.md
4. Build dependency graph
5. Produce security assessment
6. Produce performance assessment
7. Produce architecture assessment
8. Produce complete audit report

---

## How to Use

1. Ensure the skill directory is present.
2. Create the case:
   ```
   Create case folder for project <key> with case ID <case>
   ```
3. Place source files in the generated `inputs/` folder.
4. Request indexing:
   ```
   Index the inputs for project <key> case <case>
   ```
5. Request analysis:
   ```
   Analyze project <key> case <case> with mode <A/B/C/D/E>
   ```
6. For demo:
   ```
   Run demo audit case
   ```

---

## Handoff Report Requirement

Every sub-agent spawned by this skill must end its final response with a structured Handoff Report using this exact format:

### Handoff Report
- **Outcome**: success|partial|failure
- **Incidents**:
  - [TYPE=ERROR|NEAR_MISS|MISUNDERSTANDING|TOOL_FAILURE|MULTI_AGENT_HANDOFF; SEV=S1|S2|S3|S4] <brief symptom> (evidence: <1-line concrete detail, no secrets>)
  - Pattern hint: <optional>
  - Prevention rule: <optional>
- **Files touched**: <list or "none">
- **Next action**: <1-line suggestion>
- **Watchdog fields** (required for monitoring):
  - session_id: <your session identifier>
  - run_id: <your run identifier>
  - last_activity_at: <timestamp of last progress>
  - progress_marker: <current step or checkpoint>

If no incidents occurred, write "Incidents: none".

---

## Referenced Documentation Files

This skill references the following documentation files that provide detailed guidance:

| File | Purpose |
|------|------|
| `references/GOVERNOR_LIMITS.md` | Complete governor limits reference |
| `references/SECURITY_CONTROLS.md` | Security controls and enforcement |
| `references/APEX_BEST_PRACTICES.md` | Apex coding best practices |
| `references/LWC_BEST_PRACTICES.md` | LWC development best practices |
| `references/TRIGGER_PATTERNS.md` | Trigger implementation patterns |
| `references/INTEGRATION_PATTERNS.md` | Integration and callout patterns |
| `references/TEST_PATTERNS.md` | Test class best practices |
| `checklists/SECURITY_CHECKLIST.md` | Security review checklist |
| `checklists/PERFORMANCE_CHECKLIST.md` | Performance review checklist |
| `checklists/ARCHITECTURE_CHECKLIST.md` | Architecture review checklist |
| `patterns/ANTI_PATTERNS.md` | Common anti-patterns to detect |
| `patterns/DESIGN_PATTERNS.md` | Recommended design patterns |
| `security/VULNERABILITY_CATALOG.md` | Known vulnerability patterns |
| `security/FLS_CRUD_GUIDE.md` | FLS/CRUD implementation guide |
| `performance/GOVERNOR_LIMITS_DEEP_DIVE.md` | Deep dive on limits |
| `performance/QUERY_OPTIMIZATION.md` | SOQL optimization techniques |
