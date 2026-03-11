# LWC Audit Checklist

## Overview
This checklist covers Lightning Web Component (LWC) specific quality, security, and performance checks.

---

## Component Structure

### File Organization
- [ ] **FILE-001**: Component folder contains required files (.js, .html, .js-meta.xml)
- [ ] **FILE-002**: CSS file present for styled components
- [ ] **FILE-003**: Jest test folder (`__tests__/`) present
- [ ] **FILE-004**: File names match component name
- [ ] **FILE-005**: No unnecessary files in component folder

### Metadata Configuration
- [ ] **META-001**: API version is current (within last 3 releases)
- [ ] **META-002**: `isExposed` set appropriately
- [ ] **META-003**: Correct targets defined for usage context
- [ ] **META-004**: Design attributes have proper types
- [ ] **META-005**: Description provided for App Builder

---

## JavaScript Quality

### Code Structure
- [ ] **JS-001**: Component extends `LightningElement`
- [ ] **JS-002**: Reactive properties use `@track` only when necessary
- [ ] **JS-003**: Public properties use `@api`
- [ ] **JS-004**: Wire decorators configured correctly
- [ ] **JS-005**: Lifecycle hooks used appropriately

### Best Practices
- [ ] **JS-BP-001**: No direct DOM manipulation (use data binding)
- [ ] **JS-BP-002**: Async operations use `async/await` or Promises properly
- [ ] **JS-BP-003**: Error handling for all async operations
- [ ] **JS-BP-004**: Cleanup in `disconnectedCallback` for subscriptions
- [ ] **JS-BP-005**: Constants defined at module level

### Wire Service
- [ ] **WIRE-001**: `cacheable=true` used for read-only Apex methods
- [ ] **WIRE-002**: Wire parameters are reactive (`$property`)
- [ ] **WIRE-003**: Error and data handled in wire results
- [ ] **WIRE-004**: `refreshApex()` used sparingly
- [ ] **WIRE-005**: Appropriate wire adapters used (getRecord, getFieldValue)

---

## Security

### Locker Service Compliance
- [ ] **SEC-001**: No `innerHTML` assignment with user data
- [ ] **SEC-002**: No `document` object manipulation
- [ ] **SEC-003**: No `eval()` or `Function()` constructor
- [ ] **SEC-004**: No `window.location` direct access (use NavigationMixin)
- [ ] **SEC-005**: External resources from Static Resources only

### Data Security
- [ ] **DATA-001**: Sensitive data not exposed in console logs
- [ ] **DATA-002**: User input validated before use
- [ ] **DATA-003**: Apex controllers use `with sharing`
- [ ] **DATA-004**: FLS enforced in Apex queries
- [ ] **DATA-005**: CRUD checked in Apex DML

### Apex Controller Security
```apex
// REQUIRED pattern for LWC Apex controllers
public with sharing class MyController {
    
    @AuraEnabled(cacheable=true)
    public static List<Account> getAccounts() {
        return [
            SELECT Id, Name
            FROM Account
            WITH SECURITY_ENFORCED
            LIMIT 100
        ];
    }
    
    @AuraEnabled
    public static Account saveAccount(Account acc) {
        if (!Schema.sObjectType.Account.isUpdateable()) {
            throw new AuraHandledException('Insufficient access');
        }
        update acc;
        return acc;
    }
}
```

---

## Performance

### Rendering Performance
- [ ] **PERF-001**: Conditional rendering with `if:true/false`
- [ ] **PERF-002**: `for:each` has unique `key` attribute
- [ ] **PERF-003**: Large lists use virtualization/pagination
- [ ] **PERF-004**: Heavy computations not in getters
- [ ] **PERF-005**: Template expressions are simple

### Data Loading
- [ ] **LOAD-001**: Apex methods marked `cacheable=true` for reads
- [ ] **LOAD-002**: Lazy loading for large datasets
- [ ] **LOAD-003**: Debouncing on search inputs
- [ ] **LOAD-004**: Loading indicators shown during async ops
- [ ] **LOAD-005**: Error states handled and displayed

### Resource Loading
- [ ] **RES-001**: Static resources loaded in `renderedCallback` with flag
- [ ] **RES-002**: `loadScript`/`loadStyle` from `lightning/platformResourceLoader`
- [ ] **RES-003**: Promise.all for parallel resource loading
- [ ] **RES-004**: No external CDN scripts

---

## Communication Patterns

### Parent-Child Communication
- [ ] **COMM-001**: Public properties for parent-to-child data
- [ ] **COMM-002**: Public methods for parent-to-child actions
- [ ] **COMM-003**: Custom events for child-to-parent communication
- [ ] **COMM-004**: Event bubbling configured correctly
- [ ] **COMM-005**: Event detail contains necessary data only

### Cross-Component Communication
- [ ] **LMS-001**: Lightning Message Service for unrelated components
- [ ] **LMS-002**: Message channels defined in metadata
- [ ] **LMS-003**: Subscriptions cleaned up in `disconnectedCallback`
- [ ] **LMS-004**: Publish scope configured appropriately

### Event Pattern
```javascript
// Child component - dispatching event
handleClick() {
    this.dispatchEvent(new CustomEvent('selected', {
        detail: { recordId: this.recordId },
        bubbles: false,  // Stay in shadow DOM
        composed: false
    }));
}

// Parent component
// <c-child onselected={handleChildSelection}></c-child>
handleChildSelection(event) {
    const recordId = event.detail.recordId;
    // Process selection
}
```

---

## Template Quality

### HTML Best Practices
- [ ] **HTML-001**: Semantic HTML elements used
- [ ] **HTML-002**: ARIA attributes for accessibility
- [ ] **HTML-003**: Labels associated with form inputs
- [ ] **HTML-004**: Images have alt text
- [ ] **HTML-005**: Tab order is logical

### SLDS Usage
- [ ] **SLDS-001**: SLDS classes used for styling
- [ ] **SLDS-002**: Base components used where available
- [ ] **SLDS-003**: No inline styles (use CSS file)
- [ ] **SLDS-004**: Responsive design considerations
- [ ] **SLDS-005**: Theme tokens used for colors

---

## Testing

### Jest Test Coverage
- [ ] **TEST-001**: Jest tests exist for component
- [ ] **TEST-002**: Wire service mocked
- [ ] **TEST-003**: DOM querying tests present
- [ ] **TEST-004**: User interaction tests present
- [ ] **TEST-005**: Error scenarios tested

### Jest Test Pattern
```javascript
import { createElement } from 'lwc';
import MyComponent from 'c/myComponent';
import { getRecord } from 'lightning/uiRecordApi';

// Mock data
const mockRecord = require('./data/mockRecord.json');

describe('c-my-component', () => {
    afterEach(() => {
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.clearAllMocks();
    });
    
    it('displays record name', async () => {
        const element = createElement('c-my-component', {
            is: MyComponent
        });
        element.recordId = '001000000000001';
        document.body.appendChild(element);
        
        // Emit wire data
        getRecord.emit(mockRecord);
        
        // Wait for rerender
        await Promise.resolve();
        
        // Assert
        const nameElement = element.shadowRoot.querySelector('.name');
        expect(nameElement.textContent).toBe('Test Account');
    });
    
    it('handles error state', async () => {
        const element = createElement('c-my-component', {
            is: MyComponent
        });
        document.body.appendChild(element);
        
        // Emit error
        getRecord.error();
        
        await Promise.resolve();
        
        const errorElement = element.shadowRoot.querySelector('.error');
        expect(errorElement).not.toBeNull();
    });
});
```

---

## Error Handling

### Error Display
- [ ] **ERR-001**: User-friendly error messages
- [ ] **ERR-002**: Error toast notifications for failures
- [ ] **ERR-003**: Form validation errors shown inline
- [ ] **ERR-004**: Network errors handled gracefully
- [ ] **ERR-005**: Retry options for transient failures

### Error Handling Pattern
```javascript
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

async handleSave() {
    try {
        this.isLoading = true;
        const result = await saveRecord({ record: this.record });
        this.dispatchEvent(new ShowToastEvent({
            title: 'Success',
            message: 'Record saved',
            variant: 'success'
        }));
    } catch (error) {
        this.dispatchEvent(new ShowToastEvent({
            title: 'Error',
            message: this.reduceErrors(error),
            variant: 'error'
        }));
    } finally {
        this.isLoading = false;
    }
}

reduceErrors(errors) {
    if (!Array.isArray(errors)) {
        errors = [errors];
    }
    return errors
        .filter(error => !!error)
        .map(error => {
            if (Array.isArray(error.body)) {
                return error.body.map(e => e.message).join(', ');
            } else if (error.body && error.body.message) {
                return error.body.message;
            } else if (typeof error.message === 'string') {
                return error.message;
            }
            return 'Unknown error';
        })
        .join('; ');
}
```

---

## Accessibility

### WCAG Compliance
- [ ] **A11Y-001**: Color contrast meets WCAG AA
- [ ] **A11Y-002**: Focus indicators visible
- [ ] **A11Y-003**: Screen reader compatible
- [ ] **A11Y-004**: Keyboard navigation works
- [ ] **A11Y-005**: Error messages announced
