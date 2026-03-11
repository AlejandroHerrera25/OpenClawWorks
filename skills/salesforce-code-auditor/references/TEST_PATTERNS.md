# Test Patterns — Complete Reference

## Overview

Effective testing in Salesforce requires understanding governor limits, test data isolation, and bulk testing requirements. This guide provides patterns for comprehensive test coverage.

---

## Test Class Structure

### Standard Test Class Template

```apex
/**
 * AccountServiceTest
 * Test class for AccountService
 * @author Your Name
 * @date 2024-01-01
 */
@IsTest
private class AccountServiceTest {
    
    // Test data factory method
    @TestSetup
    static void setupTestData() {
        // Create common test data used across multiple tests
        List<Account> accounts = TestDataFactory.createAccounts(5, true);
    }
    
    // Positive test - happy path
    @IsTest
    static void testGetAccountsWithContacts_Success() {
        // Given
        Account testAccount = [SELECT Id FROM Account LIMIT 1];
        Contact testContact = TestDataFactory.createContact(testAccount.Id, true);
        
        // When
        Test.startTest();
        List<Account> result = new AccountService().getAccountsWithContacts(
            new Set<Id>{ testAccount.Id }
        );
        Test.stopTest();
        
        // Then
        System.assertEquals(1, result.size(), 'Should return one account');
        System.assertEquals(1, result[0].Contacts.size(), 'Account should have one contact');
    }
    
    // Negative test - invalid input
    @IsTest
    static void testGetAccountsWithContacts_EmptySet() {
        // When
        Test.startTest();
        List<Account> result = new AccountService().getAccountsWithContacts(new Set<Id>());
        Test.stopTest();
        
        // Then
        System.assertEquals(0, result.size(), 'Should return empty list for empty input');
    }
    
    // Exception test
    @IsTest
    static void testCreateAccount_ValidationException() {
        // Given
        AccountDTO invalidDto = new AccountDTO();
        invalidDto.name = ''; // Invalid - empty name
        
        // When/Then
        Test.startTest();
        try {
            new AccountService().createAccount(invalidDto);
            System.assert(false, 'Expected ValidationException');
        } catch (AccountService.ValidationException e) {
            System.assert(e.getMessage().contains('name'), 'Error should mention name field');
        }
        Test.stopTest();
    }
    
    // Bulk test - 200+ records
    @IsTest
    static void testActivateAccounts_Bulk() {
        // Given
        List<Account> accounts = TestDataFactory.createAccounts(200, true);
        Set<Id> accountIds = new Map<Id, Account>(accounts).keySet();
        
        // When
        Test.startTest();
        new AccountService().activateAccounts(accountIds);
        Test.stopTest();
        
        // Then
        List<Account> updatedAccounts = [SELECT Id, Status__c FROM Account WHERE Id IN :accountIds];
        for (Account acc : updatedAccounts) {
            System.assertEquals('Active', acc.Status__c, 'Account should be activated');
        }
    }
    
    // Security test - different user context
    @IsTest
    static void testGetAccounts_InsufficientAccess() {
        // Given
        User minimalUser = TestDataFactory.createMinimalAccessUser();
        Account testAccount = [SELECT Id FROM Account LIMIT 1];
        
        // When/Then
        Test.startTest();
        System.runAs(minimalUser) {
            try {
                new AccountService().getAccountsWithContacts(new Set<Id>{ testAccount.Id });
                // May succeed with empty results due to sharing
            } catch (SecurityException e) {
                System.assert(e.getMessage().contains('privileges'), 'Should mention privileges');
            }
        }
        Test.stopTest();
    }
}
```

---

## Test Data Factory

### Comprehensive Test Data Factory

```apex
/**
 * TestDataFactory
 * Centralized factory for creating test data
 * Follows bulkification patterns and respects governor limits
 */
@IsTest
public class TestDataFactory {
    
    // ==================== ACCOUNT ====================
    
    public static List<Account> createAccounts(Integer count, Boolean doInsert) {
        List<Account> accounts = new List<Account>();
        for (Integer i = 0; i < count; i++) {
            accounts.add(new Account(
                Name = 'Test Account ' + i,
                Industry = 'Technology',
                Type = 'Prospect',
                Phone = '555-000-' + String.valueOf(i).leftPad(4, '0'),
                BillingStreet = i + ' Test Street',
                BillingCity = 'Test City',
                BillingState = 'CA',
                BillingPostalCode = '94000',
                BillingCountry = 'USA'
            ));
        }
        if (doInsert) {
            insert accounts;
        }
        return accounts;
    }
    
    public static Account createAccount(Boolean doInsert) {
        return createAccounts(1, doInsert)[0];
    }
    
    public static Account createAccountWithContacts(Integer contactCount, Boolean doInsert) {
        Account acc = createAccount(true);
        if (contactCount > 0) {
            createContacts(acc.Id, contactCount, true);
        }
        return acc;
    }
    
    // ==================== CONTACT ====================
    
    public static List<Contact> createContacts(Id accountId, Integer count, Boolean doInsert) {
        List<Contact> contacts = new List<Contact>();
        for (Integer i = 0; i < count; i++) {
            contacts.add(new Contact(
                AccountId = accountId,
                FirstName = 'Test',
                LastName = 'Contact ' + i,
                Email = 'testcontact' + i + '@test.com',
                Phone = '555-111-' + String.valueOf(i).leftPad(4, '0')
            ));
        }
        if (doInsert) {
            insert contacts;
        }
        return contacts;
    }
    
    public static Contact createContact(Id accountId, Boolean doInsert) {
        return createContacts(accountId, 1, doInsert)[0];
    }
    
    // ==================== OPPORTUNITY ====================
    
    public static List<Opportunity> createOpportunities(Id accountId, Integer count, Boolean doInsert) {
        List<Opportunity> opportunities = new List<Opportunity>();
        for (Integer i = 0; i < count; i++) {
            opportunities.add(new Opportunity(
                AccountId = accountId,
                Name = 'Test Opportunity ' + i,
                StageName = 'Prospecting',
                CloseDate = Date.today().addMonths(1),
                Amount = 10000 + (i * 1000)
            ));
        }
        if (doInsert) {
            insert opportunities;
        }
        return opportunities;
    }
    
    // ==================== USER ====================
    
    public static User createUser(String profileName, Boolean doInsert) {
        Profile p = [SELECT Id FROM Profile WHERE Name = :profileName LIMIT 1];
        String uniqueKey = String.valueOf(Datetime.now().getTime());
        
        User u = new User(
            FirstName = 'Test',
            LastName = 'User ' + uniqueKey,
            Email = 'testuser' + uniqueKey + '@test.com',
            Username = 'testuser' + uniqueKey + '@test.com.sandbox',
            Alias = ('tu' + uniqueKey).left(8),
            TimeZoneSidKey = 'America/Los_Angeles',
            LocaleSidKey = 'en_US',
            EmailEncodingKey = 'UTF-8',
            LanguageLocaleKey = 'en_US',
            ProfileId = p.Id
        );
        
        if (doInsert) {
            insert u;
        }
        return u;
    }
    
    public static User createStandardUser(Boolean doInsert) {
        return createUser('Standard User', doInsert);
    }
    
    public static User createMinimalAccessUser() {
        // Create user with Minimum Access profile or custom minimal profile
        return createUser('Minimum Access - Salesforce', true);
    }
    
    public static User createAdminUser(Boolean doInsert) {
        return createUser('System Administrator', doInsert);
    }
    
    // ==================== CUSTOM SETTINGS ====================
    
    public static void createCustomSettings() {
        // Create hierarchy custom settings
        Account_Settings__c settings = Account_Settings__c.getOrgDefaults();
        settings.Create_Default_Contact__c = true;
        settings.Max_Contacts_Per_Account__c = 100;
        upsert settings;
    }
    
    // ==================== CUSTOM METADATA ====================
    // Note: Custom Metadata cannot be created in tests without seeAllData=true
    // Use @TestVisible mocking instead
    
    // ==================== COMPLEX SCENARIOS ====================
    
    public static Map<String, Object> createFullAccountHierarchy() {
        Map<String, Object> result = new Map<String, Object>();
        
        // Parent account
        Account parentAccount = createAccount(true);
        result.put('parentAccount', parentAccount);
        
        // Child accounts
        List<Account> childAccounts = new List<Account>();
        for (Integer i = 0; i < 3; i++) {
            childAccounts.add(new Account(
                Name = 'Child Account ' + i,
                ParentId = parentAccount.Id
            ));
        }
        insert childAccounts;
        result.put('childAccounts', childAccounts);
        
        // Contacts for parent
        List<Contact> contacts = createContacts(parentAccount.Id, 5, true);
        result.put('contacts', contacts);
        
        // Opportunities for parent
        List<Opportunity> opportunities = createOpportunities(parentAccount.Id, 3, true);
        result.put('opportunities', opportunities);
        
        return result;
    }
}
```

---

## Mocking Patterns

### Stub API for Mocking

```apex
// Interface for dependency injection
public interface IAccountSelector {
    List<Account> selectById(Set<Id> ids);
    List<Account> selectWithContacts(Set<Id> ids);
}

// Production implementation
public class AccountSelector implements IAccountSelector {
    public List<Account> selectById(Set<Id> ids) {
        return [SELECT Id, Name FROM Account WHERE Id IN :ids WITH SECURITY_ENFORCED];
    }
    
    public List<Account> selectWithContacts(Set<Id> ids) {
        return [
            SELECT Id, Name, (SELECT Id, Name, Email FROM Contacts)
            FROM Account
            WHERE Id IN :ids
            WITH SECURITY_ENFORCED
        ];
    }
}

// Mock implementation for tests
@IsTest
public class AccountSelectorMock implements IAccountSelector {
    
    public List<Account> mockAccounts = new List<Account>();
    public Exception exceptionToThrow;
    public Boolean wasCalledSelectById = false;
    public Boolean wasCalledSelectWithContacts = false;
    
    public List<Account> selectById(Set<Id> ids) {
        wasCalledSelectById = true;
        if (exceptionToThrow != null) {
            throw exceptionToThrow;
        }
        return mockAccounts;
    }
    
    public List<Account> selectWithContacts(Set<Id> ids) {
        wasCalledSelectWithContacts = true;
        if (exceptionToThrow != null) {
            throw exceptionToThrow;
        }
        return mockAccounts;
    }
}

// Service with injectable dependency
public class AccountService {
    
    private IAccountSelector selector;
    
    public AccountService() {
        this.selector = new AccountSelector();
    }
    
    @TestVisible
    private AccountService(IAccountSelector selector) {
        this.selector = selector;
    }
    
    public List<Account> getAccounts(Set<Id> ids) {
        return selector.selectById(ids);
    }
}

// Test using mock
@IsTest
private class AccountServiceTest {
    
    @IsTest
    static void testGetAccounts_WithMock() {
        // Given
        AccountSelectorMock mockSelector = new AccountSelectorMock();
        mockSelector.mockAccounts = new List<Account>{
            new Account(Id = TestDataFactory.getFakeId(Account.SObjectType), Name = 'Mock Account')
        };
        
        AccountService service = new AccountService(mockSelector);
        
        // When
        Test.startTest();
        List<Account> result = service.getAccounts(new Set<Id>{ mockSelector.mockAccounts[0].Id });
        Test.stopTest();
        
        // Then
        System.assert(mockSelector.wasCalledSelectById, 'Selector should have been called');
        System.assertEquals(1, result.size(), 'Should return mocked account');
        System.assertEquals('Mock Account', result[0].Name, 'Should return correct name');
    }
}
```

### HttpCalloutMock

```apex
@IsTest
global class ExternalSystemMock implements HttpCalloutMock {
    
    private Integer statusCode;
    private String responseBody;
    private Map<String, String> headers;
    
    public ExternalSystemMock(Integer statusCode, String responseBody) {
        this.statusCode = statusCode;
        this.responseBody = responseBody;
        this.headers = new Map<String, String>();
    }
    
    public ExternalSystemMock withHeader(String key, String value) {
        this.headers.put(key, value);
        return this;
    }
    
    global HttpResponse respond(HttpRequest req) {
        HttpResponse res = new HttpResponse();
        res.setStatusCode(statusCode);
        res.setBody(responseBody);
        
        for (String key : headers.keySet()) {
            res.setHeader(key, headers.get(key));
        }
        
        return res;
    }
    
    // Factory methods for common scenarios
    public static ExternalSystemMock success(String body) {
        return new ExternalSystemMock(200, body)
            .withHeader('Content-Type', 'application/json');
    }
    
    public static ExternalSystemMock notFound() {
        return new ExternalSystemMock(404, '{"error": "Not Found"}');
    }
    
    public static ExternalSystemMock serverError() {
        return new ExternalSystemMock(500, '{"error": "Internal Server Error"}');
    }
    
    public static ExternalSystemMock timeout() {
        return new ExternalSystemMock(504, '{"error": "Gateway Timeout"}');
    }
}

// Test using HttpCalloutMock
@IsTest
private class IntegrationServiceTest {
    
    @IsTest
    static void testCallExternalSystem_Success() {
        // Given
        String mockResponse = '{"id": "123", "status": "success"}';
        Test.setMock(HttpCalloutMock.class, ExternalSystemMock.success(mockResponse));
        
        // When
        Test.startTest();
        String result = new IntegrationService().callExternalSystem('test payload');
        Test.stopTest();
        
        // Then
        System.assert(result.contains('success'), 'Should return success response');
    }
    
    @IsTest
    static void testCallExternalSystem_ServerError() {
        // Given
        Test.setMock(HttpCalloutMock.class, ExternalSystemMock.serverError());
        
        // When/Then
        Test.startTest();
        try {
            new IntegrationService().callExternalSystem('test payload');
            System.assert(false, 'Expected exception');
        } catch (IntegrationService.IntegrationException e) {
            System.assert(e.getMessage().contains('500'), 'Should mention status code');
        }
        Test.stopTest();
    }
}
```

---

## Assertion Best Practices

### Comprehensive Assertions

```apex
@IsTest
private class AssertionExamplesTest {
    
    @IsTest
    static void demonstrateAssertions() {
        // Basic equality
        String expected = 'Hello';
        String actual = 'Hello';
        System.assertEquals(expected, actual, 'Strings should match');
        
        // Not equal
        System.assertNotEquals(null, actual, 'Should not be null');
        
        // Boolean assertions
        System.assert(actual.startsWith('H'), 'Should start with H');
        
        // Collection assertions
        List<String> items = new List<String>{'a', 'b', 'c'};
        System.assertEquals(3, items.size(), 'Should have 3 items');
        System.assert(items.contains('b'), 'Should contain b');
        
        // Exception assertions
        try {
            Integer result = 1 / 0;
            System.assert(false, 'Should have thrown exception');
        } catch (MathException e) {
            System.assert(e.getMessage() != null, 'Exception should have message');
        }
        
        // DML assertions
        Account acc = new Account(Name = 'Test');
        insert acc;
        System.assertNotEquals(null, acc.Id, 'Id should be populated after insert');
        
        // Query assertions
        Account queried = [SELECT Id, Name FROM Account WHERE Id = :acc.Id];
        System.assertEquals('Test', queried.Name, 'Name should match');
    }
    
    // Custom assertion methods
    static void assertAccountValid(Account acc) {
        System.assertNotEquals(null, acc, 'Account should not be null');
        System.assertNotEquals(null, acc.Id, 'Account should have Id');
        System.assert(String.isNotBlank(acc.Name), 'Account should have Name');
    }
    
    static void assertListNotEmpty(List<Object> items, String message) {
        System.assertNotEquals(null, items, message + ' - List should not be null');
        System.assert(!items.isEmpty(), message + ' - List should not be empty');
    }
}
```

---

## Test Audit Checklist

### Coverage
- [ ] Minimum 75% code coverage (aim for 90%+)
- [ ] All critical business logic covered
- [ ] All exception handlers tested
- [ ] All branches (if/else) covered

### Bulk Testing
- [ ] Tested with 200+ records
- [ ] Verified no governor limit exceptions
- [ ] Tested with empty collections
- [ ] Tested with single record

### Negative Testing
- [ ] Invalid input handled
- [ ] Null input handled
- [ ] Exception scenarios tested
- [ ] Boundary conditions tested

### Security Testing
- [ ] Tested with different user profiles
- [ ] CRUD restrictions verified
- [ ] FLS restrictions verified
- [ ] Sharing rules verified

### Data Isolation
- [ ] No SeeAllData=true (except when absolutely necessary)
- [ ] Test data created in test methods
- [ ] @TestSetup used for common data
- [ ] Test data factory used

### Assertion Quality
- [ ] Meaningful assertion messages
- [ ] Specific assertions (not just "no exceptions")
- [ ] Collection sizes verified
- [ ] Field values verified
