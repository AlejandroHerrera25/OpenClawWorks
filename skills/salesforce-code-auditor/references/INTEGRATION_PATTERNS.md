# Integration Patterns — Complete Reference

## Overview

Salesforce integrations must handle network failures, timeouts, rate limits, and data transformation gracefully. This guide provides enterprise patterns for building robust integrations.

---

## Callout Architecture

### Named Credentials (Preferred)

```apex
// Using Named Credentials - credentials managed declaratively
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:MyExternalSystem/api/accounts');
req.setMethod('GET');
req.setHeader('Content-Type', 'application/json');

Http http = new Http();
HttpResponse res = http.send(req);
```

### HTTP Callout Service Pattern

```apex
/**
 * HttpCalloutService
 * Centralized HTTP callout handling with retry, logging, and error handling
 */
public class HttpCalloutService {
    
    private static final Integer DEFAULT_TIMEOUT = 30000; // 30 seconds
    private static final Integer MAX_RETRIES = 3;
    private static final Set<Integer> RETRYABLE_STATUS_CODES = new Set<Integer>{500, 502, 503, 504};
    
    public class CalloutException extends Exception {
        public Integer statusCode { get; private set; }
        public String responseBody { get; private set; }
        
        public CalloutException(String message, Integer statusCode, String responseBody) {
            this(message);
            this.statusCode = statusCode;
            this.responseBody = responseBody;
        }
    }
    
    public class CalloutRequest {
        public String endpoint { get; set; }
        public String method { get; set; }
        public String body { get; set; }
        public Map<String, String> headers { get; set; }
        public Integer timeout { get; set; }
        public Integer maxRetries { get; set; }
        
        public CalloutRequest() {
            this.headers = new Map<String, String>();
            this.timeout = DEFAULT_TIMEOUT;
            this.maxRetries = MAX_RETRIES;
        }
        
        public CalloutRequest withHeader(String key, String value) {
            this.headers.put(key, value);
            return this;
        }
    }
    
    public class CalloutResponse {
        public Integer statusCode { get; set; }
        public String body { get; set; }
        public Map<String, String> headers { get; set; }
        public Long responseTime { get; set; }
        public Boolean success { get; set; }
        
        public CalloutResponse(HttpResponse res, Long responseTime) {
            this.statusCode = res.getStatusCode();
            this.body = res.getBody();
            this.responseTime = responseTime;
            this.success = statusCode >= 200 && statusCode < 300;
            this.headers = new Map<String, String>();
            for (String key : res.getHeaderKeys()) {
                if (key != null) {
                    this.headers.put(key, res.getHeader(key));
                }
            }
        }
    }
    
    public static CalloutResponse execute(CalloutRequest request) {
        HttpRequest req = buildHttpRequest(request);
        
        Integer attempts = 0;
        Exception lastException = null;
        
        while (attempts < request.maxRetries) {
            attempts++;
            Long startTime = System.currentTimeMillis();
            
            try {
                Http http = new Http();
                HttpResponse res = http.send(req);
                Long responseTime = System.currentTimeMillis() - startTime;
                
                CalloutResponse response = new CalloutResponse(res, responseTime);
                
                // Log the callout
                logCallout(request, response, attempts);
                
                // Check if we should retry
                if (!response.success && RETRYABLE_STATUS_CODES.contains(response.statusCode)) {
                    if (attempts < request.maxRetries) {
                        // Exponential backoff
                        waitBeforeRetry(attempts);
                        continue;
                    }
                }
                
                return response;
                
            } catch (System.CalloutException e) {
                lastException = e;
                logError(request, e, attempts);
                
                if (attempts < request.maxRetries) {
                    waitBeforeRetry(attempts);
                }
            }
        }
        
        // All retries exhausted
        throw new CalloutException(
            'Callout failed after ' + attempts + ' attempts: ' + lastException?.getMessage(),
            null,
            null
        );
    }
    
    private static HttpRequest buildHttpRequest(CalloutRequest request) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint(request.endpoint);
        req.setMethod(request.method);
        req.setTimeout(request.timeout);
        
        // Set default content type if not specified
        if (!request.headers.containsKey('Content-Type')) {
            req.setHeader('Content-Type', 'application/json');
        }
        
        // Set headers
        for (String key : request.headers.keySet()) {
            req.setHeader(key, request.headers.get(key));
        }
        
        // Set body
        if (String.isNotBlank(request.body)) {
            req.setBody(request.body);
        }
        
        return req;
    }
    
    private static void waitBeforeRetry(Integer attempt) {
        // Exponential backoff: 1s, 2s, 4s...
        Integer waitMs = (Integer)Math.pow(2, attempt - 1) * 1000;
        // Note: In production, use Queueable with delay instead
        // This is simplified for illustration
    }
    
    private static void logCallout(CalloutRequest request, CalloutResponse response, Integer attempt) {
        Integration_Log__c log = new Integration_Log__c(
            Endpoint__c = request.endpoint?.left(255),
            Method__c = request.method,
            Request_Body__c = request.body?.left(131072),
            Response_Body__c = response.body?.left(131072),
            Status_Code__c = response.statusCode,
            Response_Time_Ms__c = response.responseTime,
            Attempt__c = attempt,
            Success__c = response.success,
            Timestamp__c = Datetime.now()
        );
        insert log;
    }
    
    private static void logError(CalloutRequest request, Exception e, Integer attempt) {
        Integration_Log__c log = new Integration_Log__c(
            Endpoint__c = request.endpoint?.left(255),
            Method__c = request.method,
            Request_Body__c = request.body?.left(131072),
            Error_Message__c = e.getMessage()?.left(32768),
            Attempt__c = attempt,
            Success__c = false,
            Timestamp__c = Datetime.now()
        );
        insert log;
    }
}
```

---

## Circuit Breaker Pattern

```apex
/**
 * CircuitBreaker
 * Prevents cascading failures by stopping calls to failing services
 */
public class CircuitBreaker {
    
    public enum State { CLOSED, OPEN, HALF_OPEN }
    
    private static Map<String, CircuitState> circuits = new Map<String, CircuitState>();
    
    private static final Integer FAILURE_THRESHOLD = 5;
    private static final Integer SUCCESS_THRESHOLD = 3;
    private static final Integer RESET_TIMEOUT_SECONDS = 60;
    
    private class CircuitState {
        public State state = State.CLOSED;
        public Integer failureCount = 0;
        public Integer successCount = 0;
        public Datetime lastFailureTime;
    }
    
    public static Boolean canExecute(String circuitName) {
        CircuitState circuit = getCircuit(circuitName);
        
        switch on circuit.state {
            when CLOSED {
                return true;
            }
            when OPEN {
                // Check if enough time has passed to try again
                if (circuit.lastFailureTime != null && 
                    circuit.lastFailureTime.addSeconds(RESET_TIMEOUT_SECONDS) < Datetime.now()) {
                    circuit.state = State.HALF_OPEN;
                    circuit.successCount = 0;
                    return true;
                }
                return false;
            }
            when HALF_OPEN {
                return true;
            }
            when else {
                return true;
            }
        }
    }
    
    public static void recordSuccess(String circuitName) {
        CircuitState circuit = getCircuit(circuitName);
        
        switch on circuit.state {
            when CLOSED {
                circuit.failureCount = 0;
            }
            when HALF_OPEN {
                circuit.successCount++;
                if (circuit.successCount >= SUCCESS_THRESHOLD) {
                    circuit.state = State.CLOSED;
                    circuit.failureCount = 0;
                }
            }
        }
    }
    
    public static void recordFailure(String circuitName) {
        CircuitState circuit = getCircuit(circuitName);
        circuit.lastFailureTime = Datetime.now();
        
        switch on circuit.state {
            when CLOSED {
                circuit.failureCount++;
                if (circuit.failureCount >= FAILURE_THRESHOLD) {
                    circuit.state = State.OPEN;
                }
            }
            when HALF_OPEN {
                circuit.state = State.OPEN;
            }
        }
    }
    
    public static State getState(String circuitName) {
        return getCircuit(circuitName).state;
    }
    
    public static void reset(String circuitName) {
        circuits.remove(circuitName);
    }
    
    private static CircuitState getCircuit(String circuitName) {
        if (!circuits.containsKey(circuitName)) {
            circuits.put(circuitName, new CircuitState());
        }
        return circuits.get(circuitName);
    }
}
```

### Using Circuit Breaker

```apex
public class ExternalSystemService {
    
    private static final String CIRCUIT_NAME = 'ExternalSystemAPI';
    
    public ExternalSystemResponse callExternalSystem(String payload) {
        // Check circuit breaker
        if (!CircuitBreaker.canExecute(CIRCUIT_NAME)) {
            throw new ServiceUnavailableException('Service temporarily unavailable. Please try again later.');
        }
        
        try {
            HttpCalloutService.CalloutRequest request = new HttpCalloutService.CalloutRequest();
            request.endpoint = 'callout:ExternalSystem/api/process';
            request.method = 'POST';
            request.body = payload;
            
            HttpCalloutService.CalloutResponse response = HttpCalloutService.execute(request);
            
            if (response.success) {
                CircuitBreaker.recordSuccess(CIRCUIT_NAME);
                return parseResponse(response.body);
            } else {
                CircuitBreaker.recordFailure(CIRCUIT_NAME);
                throw new IntegrationException('External system error: ' + response.statusCode);
            }
            
        } catch (Exception e) {
            CircuitBreaker.recordFailure(CIRCUIT_NAME);
            throw e;
        }
    }
}
```

---

## Async Integration Patterns

### Queueable Chain for API Calls

```apex
public class AccountSyncQueueable implements Queueable, Database.AllowsCallouts {
    
    private List<Id> accountIds;
    private Integer batchIndex;
    private static final Integer BATCH_SIZE = 10;
    
    public AccountSyncQueueable(List<Id> accountIds) {
        this(accountIds, 0);
    }
    
    private AccountSyncQueueable(List<Id> accountIds, Integer batchIndex) {
        this.accountIds = accountIds;
        this.batchIndex = batchIndex;
    }
    
    public void execute(QueueableContext context) {
        // Get current batch
        Integer startIndex = batchIndex * BATCH_SIZE;
        Integer endIndex = Math.min(startIndex + BATCH_SIZE, accountIds.size());
        
        if (startIndex >= accountIds.size()) {
            return; // All done
        }
        
        List<Id> currentBatch = new List<Id>();
        for (Integer i = startIndex; i < endIndex; i++) {
            currentBatch.add(accountIds[i]);
        }
        
        // Process current batch
        processBatch(currentBatch);
        
        // Chain next batch if more records exist
        if (endIndex < accountIds.size()) {
            System.enqueueJob(new AccountSyncQueueable(accountIds, batchIndex + 1));
        }
    }
    
    private void processBatch(List<Id> batchIds) {
        List<Account> accounts = [
            SELECT Id, Name, External_Id__c, Industry, Phone
            FROM Account
            WHERE Id IN :batchIds
        ];
        
        for (Account acc : accounts) {
            syncAccount(acc);
        }
    }
    
    private void syncAccount(Account acc) {
        // Make callout for each account
        // In production, batch multiple records into single call if API supports it
    }
}
```

### Platform Event Integration

```apex
// Publishing platform event
public class AccountEventPublisher {
    
    public static void publishAccountChanges(List<Account> accounts, Map<Id, Account> oldMap) {
        List<Account_Changed__e> events = new List<Account_Changed__e>();
        
        for (Account acc : accounts) {
            Account oldAcc = oldMap?.get(acc.Id);
            
            events.add(new Account_Changed__e(
                Account_Id__c = acc.Id,
                Account_Name__c = acc.Name,
                Change_Type__c = oldAcc == null ? 'INSERT' : 'UPDATE',
                Changed_Fields__c = oldAcc != null ? getChangedFields(acc, oldAcc) : 'ALL'
            ));
        }
        
        if (!events.isEmpty()) {
            List<Database.SaveResult> results = EventBus.publish(events);
            handlePublishResults(results);
        }
    }
    
    private static String getChangedFields(Account newAcc, Account oldAcc) {
        List<String> changed = new List<String>();
        if (newAcc.Name != oldAcc.Name) changed.add('Name');
        if (newAcc.Industry != oldAcc.Industry) changed.add('Industry');
        if (newAcc.Phone != oldAcc.Phone) changed.add('Phone');
        return String.join(changed, ',');
    }
    
    private static void handlePublishResults(List<Database.SaveResult> results) {
        for (Database.SaveResult sr : results) {
            if (!sr.isSuccess()) {
                for (Database.Error err : sr.getErrors()) {
                    System.debug('Error publishing event: ' + err.getMessage());
                }
            }
        }
    }
}

// Subscribing to platform event (Trigger)
trigger AccountChangedTrigger on Account_Changed__e (after insert) {
    List<Account_Changed__e> events = Trigger.new;
    
    for (Account_Changed__e event : events) {
        // Process event
        System.debug('Account changed: ' + event.Account_Id__c);
    }
}
```

---

## DTO Patterns

### Request/Response DTOs

```apex
/**
 * AccountDTO
 * Data Transfer Object for Account external representation
 */
public class AccountDTO {
    
    @AuraEnabled public String id { get; set; }
    @AuraEnabled public String name { get; set; }
    @AuraEnabled public String externalId { get; set; }
    @AuraEnabled public String industry { get; set; }
    @AuraEnabled public String phone { get; set; }
    @AuraEnabled public String website { get; set; }
    @AuraEnabled public AddressDTO billingAddress { get; set; }
    @AuraEnabled public List<ContactDTO> contacts { get; set; }
    
    public AccountDTO() {
        this.contacts = new List<ContactDTO>();
    }
    
    // Constructor from SObject
    public AccountDTO(Account acc) {
        this.id = acc.Id;
        this.name = acc.Name;
        this.externalId = acc.External_Id__c;
        this.industry = acc.Industry;
        this.phone = acc.Phone;
        this.website = acc.Website;
        
        if (acc.BillingStreet != null || acc.BillingCity != null) {
            this.billingAddress = new AddressDTO(
                acc.BillingStreet,
                acc.BillingCity,
                acc.BillingState,
                acc.BillingPostalCode,
                acc.BillingCountry
            );
        }
        
        this.contacts = new List<ContactDTO>();
        if (acc.Contacts != null) {
            for (Contact con : acc.Contacts) {
                this.contacts.add(new ContactDTO(con));
            }
        }
    }
    
    // Convert to SObject
    public Account toSObject() {
        Account acc = new Account();
        
        if (String.isNotBlank(this.id)) {
            acc.Id = this.id;
        }
        
        acc.Name = this.name;
        acc.External_Id__c = this.externalId;
        acc.Industry = this.industry;
        acc.Phone = this.phone;
        acc.Website = this.website;
        
        if (this.billingAddress != null) {
            acc.BillingStreet = this.billingAddress.street;
            acc.BillingCity = this.billingAddress.city;
            acc.BillingState = this.billingAddress.state;
            acc.BillingPostalCode = this.billingAddress.postalCode;
            acc.BillingCountry = this.billingAddress.country;
        }
        
        return acc;
    }
    
    // Serialize to JSON
    public String toJson() {
        return JSON.serialize(this);
    }
    
    // Deserialize from JSON
    public static AccountDTO fromJson(String jsonString) {
        return (AccountDTO) JSON.deserialize(jsonString, AccountDTO.class);
    }
    
    // Validate DTO
    public List<String> validate() {
        List<String> errors = new List<String>();
        
        if (String.isBlank(this.name)) {
            errors.add('Account name is required');
        }
        
        if (this.name != null && this.name.length() > 255) {
            errors.add('Account name cannot exceed 255 characters');
        }
        
        if (this.phone != null && !Pattern.matches('^[+]?[0-9\\s\\-().]+$', this.phone)) {
            errors.add('Invalid phone number format');
        }
        
        if (this.website != null && !this.website.startsWith('http')) {
            errors.add('Website must start with http or https');
        }
        
        return errors;
    }
}

public class AddressDTO {
    @AuraEnabled public String street { get; set; }
    @AuraEnabled public String city { get; set; }
    @AuraEnabled public String state { get; set; }
    @AuraEnabled public String postalCode { get; set; }
    @AuraEnabled public String country { get; set; }
    
    public AddressDTO() {}
    
    public AddressDTO(String street, String city, String state, String postalCode, String country) {
        this.street = street;
        this.city = city;
        this.state = state;
        this.postalCode = postalCode;
        this.country = country;
    }
}

public class ContactDTO {
    @AuraEnabled public String id { get; set; }
    @AuraEnabled public String firstName { get; set; }
    @AuraEnabled public String lastName { get; set; }
    @AuraEnabled public String email { get; set; }
    @AuraEnabled public String phone { get; set; }
    
    public ContactDTO() {}
    
    public ContactDTO(Contact con) {
        this.id = con.Id;
        this.firstName = con.FirstName;
        this.lastName = con.LastName;
        this.email = con.Email;
        this.phone = con.Phone;
    }
}
```

---

## REST API Patterns

### REST Resource Implementation

```apex
@RestResource(urlMapping='/api/accounts/*')
global with sharing class AccountRestResource {
    
    @HttpGet
    global static AccountDTO getAccount() {
        RestRequest req = RestContext.request;
        RestResponse res = RestContext.response;
        
        try {
            String accountId = req.requestURI.substringAfterLast('/');
            
            if (String.isBlank(accountId)) {
                res.statusCode = 400;
                return null;
            }
            
            Account acc = [
                SELECT Id, Name, External_Id__c, Industry, Phone, Website,
                       BillingStreet, BillingCity, BillingState, BillingPostalCode, BillingCountry,
                       (SELECT Id, FirstName, LastName, Email, Phone FROM Contacts)
                FROM Account
                WHERE Id = :accountId
                WITH SECURITY_ENFORCED
                LIMIT 1
            ];
            
            res.statusCode = 200;
            return new AccountDTO(acc);
            
        } catch (QueryException e) {
            res.statusCode = 404;
            return null;
        } catch (Exception e) {
            res.statusCode = 500;
            return null;
        }
    }
    
    @HttpPost
    global static AccountDTO createAccount(AccountDTO dto) {
        RestResponse res = RestContext.response;
        
        try {
            // Validate input
            List<String> errors = dto.validate();
            if (!errors.isEmpty()) {
                res.statusCode = 400;
                return null;
            }
            
            // Check CRUD
            if (!Schema.sObjectType.Account.isCreateable()) {
                res.statusCode = 403;
                return null;
            }
            
            // Create account
            Account acc = dto.toSObject();
            insert acc;
            
            res.statusCode = 201;
            return new AccountDTO(acc);
            
        } catch (DmlException e) {
            res.statusCode = 400;
            return null;
        } catch (Exception e) {
            res.statusCode = 500;
            return null;
        }
    }
    
    @HttpPut
    global static AccountDTO updateAccount(AccountDTO dto) {
        RestRequest req = RestContext.request;
        RestResponse res = RestContext.response;
        
        try {
            String accountId = req.requestURI.substringAfterLast('/');
            dto.id = accountId;
            
            // Validate
            List<String> errors = dto.validate();
            if (!errors.isEmpty()) {
                res.statusCode = 400;
                return null;
            }
            
            // Check CRUD
            if (!Schema.sObjectType.Account.isUpdateable()) {
                res.statusCode = 403;
                return null;
            }
            
            // Update
            Account acc = dto.toSObject();
            update acc;
            
            res.statusCode = 200;
            return new AccountDTO(acc);
            
        } catch (DmlException e) {
            res.statusCode = 400;
            return null;
        }
    }
    
    @HttpDelete
    global static void deleteAccount() {
        RestRequest req = RestContext.request;
        RestResponse res = RestContext.response;
        
        try {
            String accountId = req.requestURI.substringAfterLast('/');
            
            // Check CRUD
            if (!Schema.sObjectType.Account.isDeletable()) {
                res.statusCode = 403;
                return;
            }
            
            delete new Account(Id = accountId);
            res.statusCode = 204;
            
        } catch (DmlException e) {
            res.statusCode = 400;
        }
    }
}
```

---

## Integration Audit Checklist

### Callout Design
- [ ] Named Credentials used for authentication
- [ ] Timeout configured appropriately
- [ ] Retry logic implemented
- [ ] Circuit breaker for failing services
- [ ] Async processing for non-critical integrations

### Error Handling
- [ ] All callout exceptions caught
- [ ] Meaningful error messages
- [ ] Fallback behavior defined
- [ ] Integration logging implemented

### Security
- [ ] No credentials in code
- [ ] TLS/SSL used for all connections
- [ ] Input validation before callout
- [ ] Response validation after callout

### Performance
- [ ] Bulk APIs used where available
- [ ] Callouts batched when possible
- [ ] Async processing for large volumes
- [ ] Response caching considered

### Monitoring
- [ ] Integration logs captured
- [ ] Error notifications configured
- [ ] Performance metrics tracked
- [ ] Retry counts monitored
