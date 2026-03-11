# Audit Report Template

## Code Audit Report - Mode {MODE}

---

**Project**: {PROJECT_KEY}
**Audit Case ID**: {CASE_ID}
**Mode**: {MODE} ({MODE_DESCRIPTION})
**Auditor**: OpenClaw Salesforce Code Auditor v2.0
**Date**: {AUDIT_DATE}
**Status**: {STATUS}

---

## Executive Summary

### Overall Health Score: {HEALTH_SCORE}/100

| Category | Score | Status |
|----------|-------|--------|
| Security | {SECURITY_SCORE}/100 | {SECURITY_STATUS} |
| Performance | {PERF_SCORE}/100 | {PERF_STATUS} |
| Architecture | {ARCH_SCORE}/100 | {ARCH_STATUS} |
| Code Quality | {QUALITY_SCORE}/100 | {QUALITY_STATUS} |
| Test Coverage | {TEST_SCORE}/100 | {TEST_STATUS} |

### Findings Distribution

| Severity | Count | Blocking |
|----------|-------|----------|
| CRITICAL (Sev1) | {CRITICAL_COUNT} | {CRITICAL_BLOCKING} |
| HIGH (Sev2) | {HIGH_COUNT} | {HIGH_BLOCKING} |
| MEDIUM (Sev3) | {MEDIUM_COUNT} | {MEDIUM_BLOCKING} |
| LOW (Sev4) | {LOW_COUNT} | {LOW_BLOCKING} |
| **Total** | **{TOTAL_COUNT}** | **{TOTAL_BLOCKING}** |

### Key Findings

1. **{FINDING_1_TITLE}**: {FINDING_1_SUMMARY}
2. **{FINDING_2_TITLE}**: {FINDING_2_SUMMARY}
3. **{FINDING_3_TITLE}**: {FINDING_3_SUMMARY}

### Blocking Issues

{BLOCKING_ISSUES_LIST}

---

## Scope and Methodology

### Files Analyzed

| Category | Count |
|----------|-------|
| Apex Classes | {APEX_CLASS_COUNT} |
| Apex Triggers | {TRIGGER_COUNT} |
| LWC Components | {LWC_COUNT} |
| Aura Components | {AURA_COUNT} |
| Visualforce Pages | {VF_COUNT} |
| Flows | {FLOW_COUNT} |
| Custom Objects | {OBJECT_COUNT} |
| **Total** | **{TOTAL_FILES}** |

### Analysis Methodology

1. **Indexing**: Cataloged all source files
2. **Entrypoint Detection**: Identified UI entry points and API endpoints
3. **Dependency Analysis**: Built complete dependency graph
4. **Execution Trace**: Mapped runtime execution flow
5. **Security Scan**: Analyzed for vulnerabilities
6. **Performance Analysis**: Identified governor limit risks
7. **Architecture Review**: Evaluated design patterns and structure
8. **Test Coverage**: Assessed test quality and coverage

### Limitations

- {LIMITATION_1}
- {LIMITATION_2}

---

## Security Assessment

### Critical Vulnerabilities

{CRITICAL_VULNERABILITIES_SECTION}

### High Severity Issues

{HIGH_SECURITY_ISSUES_SECTION}

### Security Compliance

| Check | Status | Details |
|-------|--------|--------|
| FLS Enforcement | {FLS_STATUS} | {FLS_DETAILS} |
| CRUD Enforcement | {CRUD_STATUS} | {CRUD_DETAILS} |
| Sharing Model | {SHARING_STATUS} | {SHARING_DETAILS} |
| Injection Prevention | {INJECTION_STATUS} | {INJECTION_DETAILS} |
| XSS Prevention | {XSS_STATUS} | {XSS_DETAILS} |
| Credential Management | {CRED_STATUS} | {CRED_DETAILS} |

---

## Performance Assessment

### Governor Limit Risks

| Issue | Location | Risk Level | Estimated Impact |
|-------|----------|------------|------------------|
| {PERF_ISSUE_1} | {PERF_LOC_1} | {PERF_RISK_1} | {PERF_IMPACT_1} |
| {PERF_ISSUE_2} | {PERF_LOC_2} | {PERF_RISK_2} | {PERF_IMPACT_2} |

### Query Analysis

| Metric | Value | Status |
|--------|-------|--------|
| Total SOQL Queries | {SOQL_COUNT} | {SOQL_STATUS} |
| Queries in Loops | {SOQL_IN_LOOP} | {SOQL_LOOP_STATUS} |
| Non-Selective Queries | {NON_SELECTIVE} | {SELECTIVE_STATUS} |
| Unbounded Queries | {UNBOUNDED} | {BOUNDED_STATUS} |

### DML Analysis

| Metric | Value | Status |
|--------|-------|--------|
| Total DML Operations | {DML_COUNT} | {DML_STATUS} |
| DML in Loops | {DML_IN_LOOP} | {DML_LOOP_STATUS} |
| Bulk-Safe Operations | {BULK_SAFE} | {BULK_STATUS} |

---

## Architecture Assessment

### Layer Compliance

| Layer | Implemented | Compliance |
|-------|-------------|------------|
| Controller | {CTRL_IMPL} | {CTRL_COMPLIANCE} |
| Service | {SVC_IMPL} | {SVC_COMPLIANCE} |
| Selector | {SEL_IMPL} | {SEL_COMPLIANCE} |
| Domain | {DOM_IMPL} | {DOM_COMPLIANCE} |
| Trigger Handler | {TRIG_IMPL} | {TRIG_COMPLIANCE} |

### Design Pattern Usage

- {PATTERN_1}: {PATTERN_1_STATUS}
- {PATTERN_2}: {PATTERN_2_STATUS}
- {PATTERN_3}: {PATTERN_3_STATUS}

### Code Organization

| Issue | Count | Impact |
|-------|-------|--------|
| God Classes | {GOD_CLASS_COUNT} | {GOD_CLASS_IMPACT} |
| Circular Dependencies | {CIRCULAR_COUNT} | {CIRCULAR_IMPACT} |
| Mixed Concerns | {MIXED_COUNT} | {MIXED_IMPACT} |
| Dead Code | {DEAD_CODE_COUNT} | {DEAD_CODE_IMPACT} |

---

## Code Quality Assessment

### Metrics Overview

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Average Method Length | {AVG_METHOD_LEN} | < 50 lines | {METHOD_LEN_STATUS} |
| Average Class Length | {AVG_CLASS_LEN} | < 500 lines | {CLASS_LEN_STATUS} |
| Cyclomatic Complexity | {AVG_COMPLEXITY} | < 10 | {COMPLEXITY_STATUS} |
| Code Duplication | {DUPLICATION_PCT}% | < 5% | {DUP_STATUS} |

### Naming Convention Compliance

| Type | Compliant | Non-Compliant |
|------|-----------|---------------|
| Classes | {CLASS_COMPLIANT} | {CLASS_NON_COMPLIANT} |
| Methods | {METHOD_COMPLIANT} | {METHOD_NON_COMPLIANT} |
| Variables | {VAR_COMPLIANT} | {VAR_NON_COMPLIANT} |

---

## Test Coverage Assessment

### Coverage Summary

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Overall Coverage | {OVERALL_COVERAGE}% | 75% | {COVERAGE_STATUS} |
| Critical Classes | {CRITICAL_COVERAGE}% | 90% | {CRITICAL_STATUS} |
| Trigger Coverage | {TRIGGER_COVERAGE}% | 90% | {TRIGGER_STATUS} |

### Test Quality

| Check | Status | Details |
|-------|--------|--------|
| Assertion Quality | {ASSERT_STATUS} | {ASSERT_DETAILS} |
| Bulk Testing | {BULK_TEST_STATUS} | {BULK_TEST_DETAILS} |
| Negative Testing | {NEG_TEST_STATUS} | {NEG_TEST_DETAILS} |
| Test Data Factory | {FACTORY_STATUS} | {FACTORY_DETAILS} |

---

## Detailed Findings

### CRITICAL Findings

{CRITICAL_FINDINGS_DETAIL}

### HIGH Findings

{HIGH_FINDINGS_DETAIL}

### MEDIUM Findings

{MEDIUM_FINDINGS_DETAIL}

### LOW Findings

{LOW_FINDINGS_DETAIL}

---

## Dependency Graph

### Class Dependencies

```
{DEPENDENCY_GRAPH_ASCII}
```

### Execution Flow

```
{EXECUTION_FLOW_ASCII}
```

---

## Recommendations

### Immediate Actions (Before Deployment)

1. {IMMEDIATE_ACTION_1}
2. {IMMEDIATE_ACTION_2}
3. {IMMEDIATE_ACTION_3}

### Short-Term Improvements (1-2 Sprints)

1. {SHORT_TERM_1}
2. {SHORT_TERM_2}
3. {SHORT_TERM_3}

### Long-Term Technical Debt

1. {LONG_TERM_1}
2. {LONG_TERM_2}
3. {LONG_TERM_3}

---

## Remediation Roadmap

| Phase | Duration | Focus | Estimated Effort |
|-------|----------|-------|------------------|
| 1 | {PHASE_1_DURATION} | Critical Security Issues | {PHASE_1_EFFORT} |
| 2 | {PHASE_2_DURATION} | Performance Optimization | {PHASE_2_EFFORT} |
| 3 | {PHASE_3_DURATION} | Architecture Improvements | {PHASE_3_EFFORT} |
| 4 | {PHASE_4_DURATION} | Code Quality & Tests | {PHASE_4_EFFORT} |

---

## Design Alignment

{DESIGN_ALIGNMENT_SECTION}

### Comparison with Architect Specifications

| Specification | Implementation | Alignment |
|---------------|----------------|----------|
| {SPEC_1} | {IMPL_1} | {ALIGN_1} |
| {SPEC_2} | {IMPL_2} | {ALIGN_2} |
| {SPEC_3} | {IMPL_3} | {ALIGN_3} |

---

## Appendices

### A. Files Analyzed

{FILE_LIST}

### B. Complete Findings List

{COMPLETE_FINDINGS_TABLE}

### C. Code Snippets

{CODE_SNIPPETS}

---

## Audit Metadata

| Field | Value |
|-------|-------|
| Audit Start | {AUDIT_START} |
| Audit End | {AUDIT_END} |
| Token Budget Used | {TOKENS_USED} |
| Files Processed | {FILES_PROCESSED} |
| Lines Analyzed | {LINES_ANALYZED} |

---

## Handoff Report

- **Outcome**: {OUTCOME}
- **Incidents**: {INCIDENTS}
- **Files Touched**: {FILES_TOUCHED}
- **Next Action**: {NEXT_ACTION}
- **Watchdog Fields**:
  - session_id: {SESSION_ID}
  - run_id: {RUN_ID}
  - last_activity_at: {LAST_ACTIVITY}
  - progress_marker: {PROGRESS_MARKER}
