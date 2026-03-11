# Salesforce Code Auditor Skill v2.0 - PRD

## Original Problem Statement
Hardening del skill `salesforce-code-auditor` para OpenClaw, convirtiéndolo en una herramienta x10 más robusta para análisis técnico progresivo de codebases Salesforce (Apex, LWC, Visualforce, Triggers, Flows, Metadata).

## Architecture & Tech Stack
- **Platform**: OpenClaw Skills Framework
- **Format**: Markdown documentation files
- **Structure**: Hierarchical folder organization with specialized documents

## User Personas
1. **Salesforce Developers**: Need code quality guidance and best practices
2. **Architects**: Need architecture validation and design pattern recommendations
3. **Security Reviewers**: Need vulnerability detection and compliance checklists
4. **Team Leads**: Need audit reports for code review governance

## Core Requirements (Static)
- Token-efficient progressive analysis methodology
- Architect integration with handoff modes (A, B, C, D, E)
- Security analysis (FLS, CRUD, Injection, XSS)
- Performance analysis (Governor Limits, Bulkification)
- Architecture analysis (Design Patterns, Separation of Concerns)
- Complete reporting with remediation roadmaps

## What's Been Implemented (Jan 2026)

### Main Skill File
- `/app/skills/salesforce-code-auditor/SKILL.md` - Complete skill definition with:
  - 5 handoff modes (A-E) including new Security and Performance modes
  - Project state machine integration
  - Complete reporting layer specifications
  - Workspace code intake model
  - Token optimization strategy

### Reference Documentation (10 files)
- `GOVERNOR_LIMITS.md` - Complete limits reference with code examples
- `SECURITY_CONTROLS.md` - FLS, CRUD, Sharing, Injection prevention
- `APEX_BEST_PRACTICES.md` - Code organization, patterns, error handling
- `LWC_BEST_PRACTICES.md` - Component architecture, security, performance
- `TRIGGER_PATTERNS.md` - Handler framework, recursion control
- `INTEGRATION_PATTERNS.md` - Callout service, circuit breaker, DTOs
- `TEST_PATTERNS.md` - Test structure, mocking, assertions
- `FILE_TYPES.md` - Supported formats catalog
- `TOKEN_STRATEGY.md` - Token budget allocation strategy
- `REVIEW_CHECKLISTS.md` - Quick reference for code reviews

### Security Documentation (2 files)
- `VULNERABILITY_CATALOG.md` - 10+ vulnerability patterns with CWE references
- `FLS_CRUD_GUIDE.md` - Implementation guide with code examples

### Performance Documentation (2 files)
- `QUERY_OPTIMIZATION.md` - Selectivity, LDV strategies, optimization techniques
- `BULKIFICATION_GUIDE.md` - Complete bulkification patterns and examples

### Architecture Documentation (1 file)
- `SEPARATION_OF_CONCERNS.md` - Layered architecture guide

### Pattern Documentation (2 files)
- `ANTI_PATTERNS.md` - 20+ anti-patterns with detection and remediation
- `DESIGN_PATTERNS.md` - Service, Selector, Domain, Factory, Strategy patterns

### Checklists (8 files)
- `SECURITY_CHECKLIST.md` - 50+ security checks with severity levels
- `PERFORMANCE_CHECKLIST.md` - Governor limit tracking, LDV considerations
- `ARCHITECTURE_CHECKLIST.md` - Layer compliance, design patterns
- `CODE_QUALITY_CHECKLIST.md` - Naming, complexity, documentation
- `TEST_COVERAGE_CHECKLIST.md` - Coverage, bulk testing, security testing
- `LWC_CHECKLIST.md` - Component structure, security, performance
- `TRIGGER_CHECKLIST.md` - Handler framework, recursion, testing
- `INTEGRATION_CHECKLIST.md` - Callout patterns, error handling, monitoring

### Templates & Examples (2 files)
- `audit_report_template.md` - Complete template with placeholders
- `example_audit_report.md` - Full example report with findings

## Statistics
- **Total Files**: 28 markdown documentation files
- **Total Size**: ~420KB of documentation
- **Coverage Areas**: Security, Performance, Architecture, Code Quality, Testing, LWC, Triggers, Integrations

## Prioritized Backlog

### P0 - Done
✅ All implemented in this session

### P1 - Future Enhancements
- Add more anti-pattern examples
- Create video walkthrough guides
- Add Flow/Process Builder analysis patterns

### P2 - Nice to Have
- Interactive checklist tool
- VSCode extension integration guide
- CI/CD pipeline integration examples

## Next Tasks
1. Test skill with real Salesforce codebase
2. Gather feedback from Salesforce developers
3. Iterate on checklist completeness based on real-world audits
