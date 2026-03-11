# Supported File Types

## Overview

This document catalogs all file types supported by the Salesforce Code Auditor skill.

---

## Apex Files

| Extension | Type | Description |
|-----------|------|-------------|
| `.cls` | Apex Class | Standard Apex class files |
| `.cls-meta.xml` | Apex Class Metadata | API version, status, package version |
| `.trigger` | Apex Trigger | Trigger definition files |
| `.trigger-meta.xml` | Trigger Metadata | API version, status |

### Apex Class Categories

- **Controllers**: UI controllers, REST resources, batch entry points
- **Services**: Business logic, transaction management
- **Selectors**: Data access, queries
- **Domains**: Object-specific logic, validations
- **Handlers**: Trigger handlers
- **DTOs**: Data transfer objects
- **Utilities**: Helper classes
- **Exceptions**: Custom exception classes
- **Tests**: Test classes (@IsTest)

---

## Lightning Web Components (LWC)

| Extension | Type | Description |
|-----------|------|-------------|
| `.js` | JavaScript Controller | Component logic and handlers |
| `.html` | Template | Component markup |
| `.css` | Styles | Component-scoped CSS |
| `.js-meta.xml` | Component Metadata | Targets, design attributes |
| `.svg` | Icon | Custom component icon |

### LWC Folder Structure
```
myComponent/
├── myComponent.js
├── myComponent.html
├── myComponent.css
├── myComponent.js-meta.xml
└── __tests__/
    └── myComponent.test.js
```

---

## Aura Components

| Extension | Type | Description |
|-----------|------|-------------|
| `.cmp` | Component | Aura component markup |
| `.app` | Application | Aura application definition |
| `.evt` | Event | Custom event definition |
| `.intf` | Interface | Aura interface |
| `.design` | Design | App Builder configuration |
| `.auradoc` | Documentation | Component documentation |
| `.svg` | Icon | Component icon |

### Aura Component Controllers
| Extension | Type |
|-----------|------|
| `Controller.js` | Client-side controller |
| `Helper.js` | Helper functions |
| `Renderer.js` | Custom rendering |

---

## Visualforce

| Extension | Type | Description |
|-----------|------|-------------|
| `.page` | Visualforce Page | Page markup |
| `.page-meta.xml` | Page Metadata | API version, label |
| `.component` | VF Component | Reusable component |
| `.component-meta.xml` | Component Metadata | API version |

---

## Metadata Files

### Object Metadata
| Extension | Type |
|-----------|------|
| `.object` | Custom Object | Full object definition |
| `.object-meta.xml` | Object Metadata | Object properties |
| `.field-meta.xml` | Custom Field | Field definition |
| `.validationRule-meta.xml` | Validation Rule | Validation logic |
| `.compactLayout-meta.xml` | Compact Layout | Layout definition |
| `.listView-meta.xml` | List View | List view definition |

### Automation Metadata
| Extension | Type |
|-----------|------|
| `.flow-meta.xml` | Flow | Flow definition |
| `.workflow-meta.xml` | Workflow | Workflow rules |
| `.processBuilder-meta.xml` | Process Builder | Process definition |
| `.approvalProcess-meta.xml` | Approval Process | Approval definition |

### Security Metadata
| Extension | Type |
|-----------|------|
| `.profile-meta.xml` | Profile | Profile definition |
| `.permissionset-meta.xml` | Permission Set | Permission set |
| `.permissionsetgroup-meta.xml` | Permission Set Group | Group definition |
| `.sharingRules-meta.xml` | Sharing Rules | Sharing configuration |

### Other Metadata
| Extension | Type |
|-----------|------|
| `.labels-meta.xml` | Custom Labels | Label definitions |
| `.settings-meta.xml` | Custom Settings | Setting definitions |
| `.customMetadata-meta.xml` | Custom Metadata | Custom metadata records |
| `.tab-meta.xml` | Custom Tab | Tab definition |
| `.app-meta.xml` | Lightning App | App definition |
| `.flexipage-meta.xml` | Flexipage | Lightning page |

---

## Project Structure Formats

### SFDX Format (Preferred)
```
force-app/
└── main/
    └── default/
        ├── classes/
        ├── triggers/
        ├── lwc/
        ├── aura/
        ├── pages/
        ├── objects/
        ├── flows/
        ├── permissionsets/
        └── profiles/
```

### Metadata API Format (Legacy)
```
src/
├── classes/
├── triggers/
├── components/
├── pages/
├── objects/
└── package.xml
```

### Unlocked Package Format
```
sfdx-project.json
force-app/
├── core/
│   └── main/default/
└── features/
    └── main/default/
```

---

## File Priority for Analysis

### High Priority (Always Analyze)
1. Apex Classes (`.cls`)
2. Apex Triggers (`.trigger`)
3. LWC JavaScript (`.js`)
4. Visualforce Pages (`.page`)

### Medium Priority (Analyze When Relevant)
1. LWC Templates (`.html`)
2. Aura Components (`.cmp`)
3. Flow Definitions (`.flow-meta.xml`)
4. Custom Objects (`.object-meta.xml`)

### Low Priority (Context Only)
1. CSS Files (`.css`)
2. Static Resources
3. Labels and Translations
4. Profiles and Permission Sets

---

## File Identification Patterns

### Controller Indicators
- Class name ends with `Controller`
- Contains `@AuraEnabled` methods
- Contains `@RemoteAction` methods
- Extends `PageReference`
- Contains `@RestResource` annotation

### Service Indicators
- Class name ends with `Service`
- Contains business logic methods
- Calls selector classes
- Manages transactions

### Selector Indicators
- Class name ends with `Selector`
- Contains SOQL queries
- Returns SObject collections
- Uses `WITH SECURITY_ENFORCED`

### Test Indicators
- Has `@IsTest` annotation
- Class name ends with `Test`
- Contains `@TestSetup`
- Uses `Test.startTest()`/`Test.stopTest()`

### Trigger Handler Indicators
- Class name ends with `TriggerHandler` or `Handler`
- Extends base handler class
- Contains context methods (beforeInsert, afterUpdate, etc.)

### DTO Indicators
- Class name ends with `DTO`, `Request`, `Response`, `Wrapper`
- Contains only public properties
- Has `toJson()`/`fromJson()` methods
- Uses `@AuraEnabled` properties
