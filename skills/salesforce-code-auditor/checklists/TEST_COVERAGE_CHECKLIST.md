# Test Coverage Checklist

## Overview
This checklist ensures test classes meet quality standards beyond just code coverage percentage.

---

## Coverage Requirements

### Minimum Coverage
- [ ] **COV-001**: Overall code coverage ≥ 75% (Salesforce requirement)
- [ ] **COV-002**: Critical business logic coverage ≥ 90%
- [ ] **COV-003**: Trigger coverage ≥ 90%
- [ ] **COV-004**: Controller coverage ≥ 85%
- [ ] **COV-005**: Service layer coverage ≥ 90%

### Coverage Quality
- [ ] **QUAL-001**: Every test has at least one assertion
- [ ] **QUAL-002**: Assertions test actual functionality (not just "no exceptions")
- [ ] **QUAL-003**: Edge cases covered
- [ ] **QUAL-004**: Error paths covered
- [ ] **QUAL-005**: All branches (if/else) covered

---

## Test Structure

### Test Class Organization
- [ ] **STRUCT-001**: Test class named `{ClassUnderTest}Test`
- [ ] **STRUCT-002**: Test class is private: `@IsTest private class`
- [ ] **STRUCT-003**: `@TestSetup` used for common test data
- [ ] **STRUCT-004**: Tests grouped by functionality
- [ ] **STRUCT-005**: Each test method tests one scenario

### Test Method Naming
- [ ] **NAME-001**: Method name describes scenario: `testMethodName_Scenario_ExpectedResult`
- [ ] **NAME-002**: Positive tests: `testCreateAccount_ValidData_Success`
- [ ] **NAME-003**: Negative tests: `testCreateAccount_InvalidData_ThrowsException`
- [ ] **NAME-004**: Bulk tests: `testCreateAccount_Bulk200Records_Success`

### Test Method Structure (AAA Pattern)
```apex
@IsTest
static void testMethodName_Scenario_ExpectedResult() {
    // Arrange (Given)
    Account testAccount = TestDataFactory.createAccount(false);
    testAccount.Industry = 'Technology';
    insert testAccount;
    
    // Act (When)
    Test.startTest();
    Account result = new AccountService().updateAccountType(testAccount.Id);
    Test.stopTest();
    
    // Assert (Then)
    System.assertEquals('Enterprise', result.Type, 'Type should be Enterprise for Tech industry');
}
```

---

## Test Data

### Test Data Factory
- [ ] **DATA-001**: TestDataFactory class exists
- [ ] **DATA-002**: Factory methods create valid records
- [ ] **DATA-003**: Factory methods support bulk creation
- [ ] **DATA-004**: Factory methods have `doInsert` parameter
- [ ] **DATA-005**: No hardcoded IDs in tests

### Data Isolation
- [ ] **ISO-001**: No `@IsTest(SeeAllData=true)` unless absolutely required
- [ ] **ISO-002**: Tests create all required data
- [ ] **ISO-003**: Tests don't depend on org-specific data
- [ ] **ISO-004**: Tests clean up after themselves (implicit)

---

## Bulk Testing

### Volume Testing
- [ ] **BULK-001**: Triggers tested with 200+ records
- [ ] **BULK-002**: Services tested with bulk data
- [ ] **BULK-003**: No governor limit exceptions in bulk tests
- [ ] **BULK-004**: Performance acceptable with bulk data

### Bulk Test Pattern
```apex
@IsTest
static void testTrigger_BulkInsert_Success() {
    // Arrange
    List<Account> accounts = TestDataFactory.createAccounts(200, false);
    
    // Act
    Test.startTest();
    insert accounts;
    Test.stopTest();
    
    // Assert
    List<Account> inserted = [SELECT Id, Status__c FROM Account WHERE Id IN :accounts];
    System.assertEquals(200, inserted.size(), 'All accounts should be inserted');
    
    for (Account acc : inserted) {
        System.assertEquals('New', acc.Status__c, 'Default status should be New');
    }
}
```

---

## Negative Testing

### Error Scenarios
- [ ] **NEG-001**: Invalid input data tested
- [ ] **NEG-002**: Null parameter handling tested
- [ ] **NEG-003**: Empty collection handling tested
- [ ] **NEG-004**: Exception scenarios tested
- [ ] **NEG-005**: Validation rule triggers tested

### Exception Testing Pattern
```apex
@IsTest
static void testCreateAccount_NullAccount_ThrowsException() {
    // Arrange
    AccountService service = new AccountService();
    
    // Act & Assert
    Test.startTest();
    try {
        service.createAccount(null);
        System.assert(false, 'Expected ValidationException');
    } catch (AccountService.ValidationException e) {
        System.assert(e.getMessage().contains('required'), 'Should mention required');
    }
    Test.stopTest();
}
```

---

## Security Testing

### User Context Testing
- [ ] **SEC-001**: Tests run with different user profiles
- [ ] **SEC-002**: FLS restrictions verified
- [ ] **SEC-003**: CRUD restrictions verified
- [ ] **SEC-004**: Sharing rules verified

### Security Test Pattern
```apex
@IsTest
static void testGetAccount_RestrictedUser_NoAccess() {
    // Arrange
    User restrictedUser = TestDataFactory.createRestrictedUser();
    Account testAccount = TestDataFactory.createAccount(true);
    
    // Act & Assert
    System.runAs(restrictedUser) {
        Test.startTest();
        try {
            Account result = new AccountService().getAccount(testAccount.Id);
            System.assert(false, 'Expected security exception');
        } catch (System.QueryException e) {
            // Expected - WITH SECURITY_ENFORCED blocks access
        }
        Test.stopTest();
    }
}
```

---

## Integration Testing

### Callout Testing
- [ ] **INT-001**: HttpCalloutMock implemented for external calls
- [ ] **INT-002**: Multiple response scenarios tested (success, error, timeout)
- [ ] **INT-003**: Retry logic tested
- [ ] **INT-004**: Circuit breaker behavior tested

### Mock Pattern
```apex
@IsTest
static void testExternalCall_ServerError_HandledGracefully() {
    // Arrange
    Test.setMock(HttpCalloutMock.class, new MockHttpResponse(500, 'Internal Error'));
    
    // Act
    Test.startTest();
    IntegrationService service = new IntegrationService();
    IntegrationResult result = service.callExternalApi('test-data');
    Test.stopTest();
    
    // Assert
    System.assertEquals(false, result.success, 'Should indicate failure');
    System.assert(result.errorMessage.contains('500'), 'Should include status code');
}

public class MockHttpResponse implements HttpCalloutMock {
    private Integer statusCode;
    private String body;
    
    public MockHttpResponse(Integer statusCode, String body) {
        this.statusCode = statusCode;
        this.body = body;
    }
    
    public HttpResponse respond(HttpRequest req) {
        HttpResponse res = new HttpResponse();
        res.setStatusCode(statusCode);
        res.setBody(body);
        return res;
    }
}
```

---

## Async Testing

### Async Apex Testing
- [ ] **ASYNC-001**: Future methods tested with `Test.startTest()`/`Test.stopTest()`
- [ ] **ASYNC-002**: Queueable jobs tested
- [ ] **ASYNC-003**: Batch Apex tested (start, execute, finish)
- [ ] **ASYNC-004**: Scheduled Apex tested

### Batch Test Pattern
```apex
@IsTest
static void testAccountBatch_ProcessesRecords() {
    // Arrange
    List<Account> accounts = TestDataFactory.createAccounts(100, true);
    
    // Act
    Test.startTest();
    Database.executeBatch(new AccountCleanupBatch(), 200);
    Test.stopTest();  // Forces batch to complete
    
    // Assert
    List<Account> processed = [SELECT Id, Status__c FROM Account WHERE Id IN :accounts];
    for (Account acc : processed) {
        System.assertEquals('Processed', acc.Status__c, 'Account should be processed');
    }
}
```

---

## Assertion Quality

### Good Assertions
- [ ] **ASSERT-001**: Assertions have descriptive messages
- [ ] **ASSERT-002**: Specific values asserted (not just true/false)
- [ ] **ASSERT-003**: Collection sizes verified
- [ ] **ASSERT-004**: Field values verified
- [ ] **ASSERT-005**: Error messages verified in exception tests

### Assertion Examples
```apex
// GOOD: Specific, descriptive assertions
System.assertEquals(expectedValue, actualValue, 'Field X should equal Y because Z');
System.assertNotEquals(null, record.Id, 'Record should have Id after insert');
System.assertEquals(5, results.size(), 'Query should return exactly 5 records');
System.assert(record.Name.startsWith('Test'), 'Name should start with Test prefix');

// BAD: Vague assertions
System.assert(true);
System.assertNotEquals(null, something);
System.assertEquals(true, results.size() > 0);
```

---

## Test Anti-Patterns to Avoid

### Common Mistakes
- [ ] No assertions in test method
- [ ] Using `SeeAllData=true`
- [ ] Hardcoded IDs
- [ ] Testing only happy path
- [ ] No bulk testing
- [ ] Test method doing too much
- [ ] Not using `Test.startTest()`/`Test.stopTest()`
- [ ] Creating data for each test instead of using `@TestSetup`

---

## Test Metrics Dashboard

| Metric | Target | Your Value | Status |
|--------|--------|------------|--------|
| Overall Coverage | ≥ 75% | | |
| Critical Code Coverage | ≥ 90% | | |
| Tests with Assertions | 100% | | |
| Bulk Tests Present | Yes | | |
| Negative Tests Present | Yes | | |
| Security Tests Present | Yes | | |
| Integration Mocks Present | Yes | | |
