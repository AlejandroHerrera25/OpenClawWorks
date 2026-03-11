# Lightning Web Components (LWC) Best Practices — Complete Reference

## Overview

Lightning Web Components is Salesforce's modern framework for building user interfaces. This guide covers security, performance, architecture, and testing best practices.

---

## Component Architecture

### Component Structure

```
myComponent/
├── myComponent.html          # Template
├── myComponent.js            # Controller
├── myComponent.css           # Styles (scoped)
├── myComponent.js-meta.xml   # Metadata configuration
└── __tests__/
    └── myComponent.test.js   # Jest tests
```

### Metadata Configuration

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>59.0</apiVersion>
    <isExposed>true</isExposed>
    <masterLabel>My Component</masterLabel>
    <description>Component description</description>
    <targets>
        <target>lightning__RecordPage</target>
        <target>lightning__AppPage</target>
        <target>lightning__HomePage</target>
        <target>lightning__FlowScreen</target>
        <target>lightningCommunity__Page</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__RecordPage">
            <objects>
                <object>Account</object>
                <object>Contact</object>
            </objects>
            <property name="title" type="String" default="My Title"/>
            <property name="showDetails" type="Boolean" default="true"/>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

---

## Data Retrieval Patterns

### Wire Service (Reactive)

```javascript
import { LightningElement, wire, api } from 'lwc';
import { getRecord, getFieldValue } from 'lightning/uiRecordApi';
import NAME_FIELD from '@salesforce/schema/Account.Name';
import INDUSTRY_FIELD from '@salesforce/schema/Account.Industry';

const FIELDS = [NAME_FIELD, INDUSTRY_FIELD];

export default class AccountDetails extends LightningElement {
    @api recordId;
    
    @wire(getRecord, { recordId: '$recordId', fields: FIELDS })
    account;
    
    get accountName() {
        return getFieldValue(this.account.data, NAME_FIELD);
    }
    
    get industry() {
        return getFieldValue(this.account.data, INDUSTRY_FIELD);
    }
    
    get hasError() {
        return this.account.error;
    }
    
    get isLoading() {
        return !this.account.data && !this.account.error;
    }
}
```

### Wire to Apex

```javascript
import { LightningElement, wire, api } from 'lwc';
import getAccountDetails from '@salesforce/apex/AccountController.getAccountDetails';

export default class AccountView extends LightningElement {
    @api recordId;
    
    @wire(getAccountDetails, { accountId: '$recordId' })
    wiredAccount({ error, data }) {
        if (data) {
            this.account = data;
            this.error = undefined;
        } else if (error) {
            this.error = this.reduceErrors(error);
            this.account = undefined;
        }
    }
    
    // Error reducer utility
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
                return error.statusText || 'Unknown error';
            })
            .join('; ');
    }
}
```

### Imperative Apex Calls

```javascript
import { LightningElement, api, track } from 'lwc';
import saveAccount from '@salesforce/apex/AccountController.saveAccount';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

export default class AccountEditor extends LightningElement {
    @api recordId;
    @track isLoading = false;
    
    async handleSave() {
        this.isLoading = true;
        
        try {
            const accountData = this.gatherFormData();
            const result = await saveAccount({ account: accountData });
            
            this.dispatchEvent(
                new ShowToastEvent({
                    title: 'Success',
                    message: 'Account saved successfully',
                    variant: 'success'
                })
            );
            
            // Refresh view or navigate
            this.dispatchEvent(new CustomEvent('accountsaved', { detail: result }));
            
        } catch (error) {
            this.dispatchEvent(
                new ShowToastEvent({
                    title: 'Error',
                    message: this.reduceErrors(error),
                    variant: 'error'
                })
            );
        } finally {
            this.isLoading = false;
        }
    }
    
    gatherFormData() {
        const fields = this.template.querySelectorAll('lightning-input-field');
        const data = {};
        fields.forEach(field => {
            data[field.fieldName] = field.value;
        });
        return data;
    }
}
```

---

## Communication Patterns

### Parent to Child (Public Properties)

```javascript
// Parent component
// <c-child-component account-id={selectedAccountId}></c-child-component>

// Child component
export default class ChildComponent extends LightningElement {
    @api accountId;
    
    // Getter for derived properties
    @api
    get recordId() {
        return this.accountId;
    }
    
    // Public method callable by parent
    @api
    refresh() {
        // Refresh component data
    }
}
```

### Child to Parent (Custom Events)

```javascript
// Child component
handleSelection(event) {
    const selectedId = event.target.value;
    
    // Dispatch custom event
    this.dispatchEvent(
        new CustomEvent('selection', {
            detail: { id: selectedId },
            bubbles: true,
            composed: false // Stay within shadow DOM
        })
    );
}

// Parent component
// <c-child-component onselection={handleChildSelection}></c-child-component>
handleChildSelection(event) {
    const selectedId = event.detail.id;
    // Process selection
}
```

### Lightning Message Service (Cross-Component)

```javascript
// messageChannel/AccountSelected.messageChannel-meta.xml
import { LightningElement, wire } from 'lwc';
import { publish, subscribe, unsubscribe, MessageContext } from 'lightning/messageService';
import ACCOUNT_SELECTED_CHANNEL from '@salesforce/messageChannel/AccountSelected__c';

export default class Publisher extends LightningElement {
    @wire(MessageContext)
    messageContext;
    
    handleAccountSelect(event) {
        const message = {
            accountId: event.target.dataset.id,
            source: 'accountList'
        };
        publish(this.messageContext, ACCOUNT_SELECTED_CHANNEL, message);
    }
}

export default class Subscriber extends LightningElement {
    subscription = null;
    
    @wire(MessageContext)
    messageContext;
    
    connectedCallback() {
        this.subscribeToChannel();
    }
    
    disconnectedCallback() {
        this.unsubscribeFromChannel();
    }
    
    subscribeToChannel() {
        if (!this.subscription) {
            this.subscription = subscribe(
                this.messageContext,
                ACCOUNT_SELECTED_CHANNEL,
                (message) => this.handleMessage(message)
            );
        }
    }
    
    unsubscribeFromChannel() {
        unsubscribe(this.subscription);
        this.subscription = null;
    }
    
    handleMessage(message) {
        this.selectedAccountId = message.accountId;
    }
}
```

---

## Security Best Practices

### Locker Service Compliance

```javascript
// DON'T: Direct DOM manipulation with innerHTML
this.template.querySelector('div').innerHTML = userContent; // XSS RISK

// DO: Use data binding
// Template: {sanitizedContent}
this.sanitizedContent = userContent; // Automatically escaped

// DON'T: Access global objects directly
window.location.href = url; // May be blocked by Locker

// DO: Use Navigation Service
import { NavigationMixin } from 'lightning/navigation';

export default class MyComponent extends NavigationMixin(LightningElement) {
    navigateToPage() {
        this[NavigationMixin.Navigate]({
            type: 'standard__webPage',
            attributes: {
                url: this.targetUrl
            }
        });
    }
}
```

### Static Resource Security

```javascript
// DON'T: Load external scripts from CDN
// Security risk and CSP violation

// DO: Use static resources
import RESOURCE from '@salesforce/resourceUrl/myResource';
import { loadScript, loadStyle } from 'lightning/platformResourceLoader';

renderedCallback() {
    if (this.resourcesLoaded) return;
    this.resourcesLoaded = true;
    
    Promise.all([
        loadScript(this, RESOURCE + '/js/library.js'),
        loadStyle(this, RESOURCE + '/css/styles.css')
    ])
    .then(() => {
        this.initializeLibrary();
    })
    .catch(error => {
        console.error('Error loading resources', error);
    });
}
```

### Secure Apex Controller Design

```apex
public with sharing class AccountController {
    
    // Cacheable for wire service optimization
    @AuraEnabled(cacheable=true)
    public static Account getAccountDetails(Id accountId) {
        // FLS and sharing are enforced by 'with sharing' and WITH SECURITY_ENFORCED
        return [
            SELECT Id, Name, Industry, Phone, Website
            FROM Account
            WHERE Id = :accountId
            WITH SECURITY_ENFORCED
            LIMIT 1
        ];
    }
    
    // Non-cacheable for mutations
    @AuraEnabled
    public static Account saveAccount(Account account) {
        // Validate input
        if (account == null) {
            throw new AuraHandledException('Account data is required');
        }
        
        // Check CRUD
        if (account.Id == null && !Schema.sObjectType.Account.isCreateable()) {
            throw new AuraHandledException('Insufficient privileges to create Account');
        }
        if (account.Id != null && !Schema.sObjectType.Account.isUpdateable()) {
            throw new AuraHandledException('Insufficient privileges to update Account');
        }
        
        try {
            upsert account;
            return account;
        } catch (DmlException e) {
            throw new AuraHandledException(e.getMessage());
        }
    }
}
```

---

## Performance Best Practices

### Efficient Rendering

```html
<!-- DON'T: Render everything always -->
<template for:each={allItems} for:item="item">
    <c-item-detail key={item.id} item={item}></c-item-detail>
</template>

<!-- DO: Conditional rendering -->
<template if:true={hasItems}>
    <template for:each={visibleItems} for:item="item">
        <c-item-detail key={item.id} item={item}></c-item-detail>
    </template>
</template>
<template if:false={hasItems}>
    <c-empty-state></c-empty-state>
</template>
```

### Lazy Loading

```javascript
export default class LazyLoadList extends LightningElement {
    @track items = [];
    @track isLoading = false;
    pageSize = 20;
    offset = 0;
    
    connectedCallback() {
        this.loadMore();
    }
    
    async loadMore() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        try {
            const newItems = await getItems({ 
                pageSize: this.pageSize, 
                offset: this.offset 
            });
            this.items = [...this.items, ...newItems];
            this.offset += newItems.length;
        } finally {
            this.isLoading = false;
        }
    }
    
    handleScroll(event) {
        const element = event.target;
        if (element.scrollHeight - element.scrollTop === element.clientHeight) {
            this.loadMore();
        }
    }
}
```

### Debouncing User Input

```javascript
export default class SearchComponent extends LightningElement {
    searchTerm = '';
    delayTimeout;
    
    handleSearchChange(event) {
        const searchTerm = event.target.value;
        
        // Clear existing timeout
        clearTimeout(this.delayTimeout);
        
        // Debounce: wait 300ms after user stops typing
        this.delayTimeout = setTimeout(() => {
            this.searchTerm = searchTerm;
            this.performSearch();
        }, 300);
    }
    
    performSearch() {
        // Execute search
    }
}
```

### Caching Apex Results

```apex
// Use cacheable=true for read-only operations
@AuraEnabled(cacheable=true)
public static List<Account> getAccounts() {
    return [SELECT Id, Name FROM Account LIMIT 100];
}
```

```javascript
// Refresh cached data when needed
import { refreshApex } from '@salesforce/apex';

@wire(getAccounts)
wiredAccounts;

async handleRefresh() {
    await refreshApex(this.wiredAccounts);
}
```

---

## Error Handling

### Comprehensive Error Handler

```javascript
export default class ErrorHandler extends LightningElement {
    
    // Centralized error reducer
    reduceErrors(errors) {
        if (!errors) return 'Unknown error';
        
        if (!Array.isArray(errors)) {
            errors = [errors];
        }
        
        return errors
            .filter(error => !!error)
            .map(error => {
                // UI API errors
                if (Array.isArray(error.body)) {
                    return error.body.map(e => e.message).join(', ');
                }
                // Standard error format
                if (error.body && typeof error.body.message === 'string') {
                    return error.body.message;
                }
                // Field errors
                if (error.body && error.body.fieldErrors) {
                    const fieldErrors = [];
                    Object.keys(error.body.fieldErrors).forEach(field => {
                        error.body.fieldErrors[field].forEach(fe => {
                            fieldErrors.push(`${field}: ${fe.message}`);
                        });
                    });
                    return fieldErrors.join(', ');
                }
                // Page errors
                if (error.body && error.body.pageErrors) {
                    return error.body.pageErrors.map(e => e.message).join(', ');
                }
                // JS errors
                if (typeof error.message === 'string') {
                    return error.message;
                }
                // Status text
                if (typeof error.statusText === 'string') {
                    return error.statusText;
                }
                return 'Unknown error';
            })
            .join('; ');
    }
    
    showError(title, error) {
        this.dispatchEvent(
            new ShowToastEvent({
                title: title,
                message: this.reduceErrors(error),
                variant: 'error',
                mode: 'sticky'
            })
        );
    }
}
```

---

## Testing Best Practices

### Jest Unit Tests

```javascript
import { createElement } from 'lwc';
import AccountDetails from 'c/accountDetails';
import { getRecord } from 'lightning/uiRecordApi';

// Mock data
const mockGetRecord = require('./data/getRecord.json');

describe('c-account-details', () => {
    afterEach(() => {
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.clearAllMocks();
    });
    
    it('displays account name from wire service', async () => {
        const element = createElement('c-account-details', {
            is: AccountDetails
        });
        element.recordId = '001xx000003DGb2AAG';
        document.body.appendChild(element);
        
        // Emit mock data
        getRecord.emit(mockGetRecord);
        
        // Wait for rerender
        await Promise.resolve();
        
        // Assert
        const nameElement = element.shadowRoot.querySelector('.account-name');
        expect(nameElement.textContent).toBe('Test Account');
    });
    
    it('displays error when wire service fails', async () => {
        const element = createElement('c-account-details', {
            is: AccountDetails
        });
        document.body.appendChild(element);
        
        // Emit error
        getRecord.error();
        
        await Promise.resolve();
        
        const errorElement = element.shadowRoot.querySelector('.error-message');
        expect(errorElement).not.toBeNull();
    });
});
```

---

## LWC Audit Checklist

### Security
- [ ] No innerHTML usage with user data
- [ ] Using Navigation Service instead of window.location
- [ ] External resources loaded from Static Resources
- [ ] Apex controllers use `with sharing`
- [ ] FLS enforced in Apex queries
- [ ] Input validation in Apex methods
- [ ] AuraHandledException used for user-facing errors

### Performance
- [ ] Using `cacheable=true` for read operations
- [ ] Debouncing search inputs
- [ ] Lazy loading large datasets
- [ ] Conditional rendering for complex templates
- [ ] Minimizing wire service calls

### Architecture
- [ ] Component single responsibility
- [ ] Proper event propagation patterns
- [ ] Using Lightning Message Service for cross-component communication
- [ ] Lifecycle hooks used appropriately
- [ ] Proper cleanup in disconnectedCallback

### Code Quality
- [ ] Jest tests for all components
- [ ] Error handling for all async operations
- [ ] Accessible components (ARIA attributes)
- [ ] Consistent naming conventions
- [ ] Documentation for public APIs
