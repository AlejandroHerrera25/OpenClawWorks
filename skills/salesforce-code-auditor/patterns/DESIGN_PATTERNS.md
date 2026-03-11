# Recommended Design Patterns for Salesforce

## Overview

This document describes proven design patterns for Salesforce development that promote maintainability, testability, and scalability.

---

## Structural Patterns

### Service Layer Pattern

**Purpose**: Encapsulate business logic in reusable service classes.

**When to Use**:
- Business logic needs to be shared across controllers, triggers, and batch jobs
- Complex transactions involving multiple objects
- Need for testable business logic

**Implementation**:
```apex
public with sharing class OpportunityService {
    
    private OpportunitySelector selector;
    private AccountSelector accountSelector;
    
    public OpportunityService() {
        this.selector = new OpportunitySelector();
        this.accountSelector = new AccountSelector();
    }
    
    // Constructor for dependency injection in tests
    @TestVisible
    private OpportunityService(OpportunitySelector oppSelector, AccountSelector accSelector) {
        this.selector = oppSelector;
        this.accountSelector = accSelector;
    }
    
    public void closeOpportunities(Set<Id> opportunityIds, String reason) {
        List<Opportunity> opportunities = selector.selectById(opportunityIds);
        
        List<Opportunity> toUpdate = new List<Opportunity>();
        for (Opportunity opp : opportunities) {
            if (opp.StageName != 'Closed Won' && opp.StageName != 'Closed Lost') {
                opp.StageName = 'Closed Lost';
                opp.Loss_Reason__c = reason;
                opp.CloseDate = Date.today();
                toUpdate.add(opp);
            }
        }
        
        if (!toUpdate.isEmpty()) {
            update toUpdate;
        }
    }
    
    public OpportunityDTO createOpportunity(OpportunityDTO dto) {
        // Validate
        List<String> errors = dto.validate();
        if (!errors.isEmpty()) {
            throw new ValidationException(errors);
        }
        
        // Check account exists
        List<Account> accounts = accountSelector.selectById(new Set<Id>{dto.accountId});
        if (accounts.isEmpty()) {
            throw new ValidationException(new List<String>{'Account not found'});
        }
        
        // Create
        Opportunity opp = dto.toSObject();
        insert opp;
        
        return new OpportunityDTO(opp);
    }
}
```

---

### Selector Pattern

**Purpose**: Centralize and standardize data access.

**When to Use**:
- Consistent field selection across queries
- Security enforcement at query level
- Mockable data access for testing

**Implementation**:
```apex
public inherited sharing class OpportunitySelector {
    
    // Standard fields for this selector
    private static final String BASE_FIELDS = 
        'Id, Name, StageName, Amount, CloseDate, AccountId, OwnerId, ' +
        'Probability, Description, Loss_Reason__c';
    
    public List<Opportunity> selectById(Set<Id> ids) {
        if (ids == null || ids.isEmpty()) {
            return new List<Opportunity>();
        }
        
        return Database.query(
            'SELECT ' + BASE_FIELDS + ' ' +
            'FROM Opportunity ' +
            'WHERE Id IN :ids ' +
            'WITH SECURITY_ENFORCED'
        );
    }
    
    public List<Opportunity> selectByAccountId(Set<Id> accountIds) {
        if (accountIds == null || accountIds.isEmpty()) {
            return new List<Opportunity>();
        }
        
        return Database.query(
            'SELECT ' + BASE_FIELDS + ' ' +
            'FROM Opportunity ' +
            'WHERE AccountId IN :accountIds ' +
            'WITH SECURITY_ENFORCED ' +
            'ORDER BY CloseDate DESC'
        );
    }
    
    public List<Opportunity> selectOpenByCloseDate(Date startDate, Date endDate) {
        return [
            SELECT Id, Name, StageName, Amount, CloseDate, AccountId
            FROM Opportunity
            WHERE CloseDate >= :startDate
            AND CloseDate <= :endDate
            AND IsClosed = false
            WITH SECURITY_ENFORCED
            ORDER BY CloseDate ASC
        ];
    }
    
    public Database.QueryLocator getQueryLocatorForBatch(String stage) {
        return Database.getQueryLocator([
            SELECT Id, Name, StageName, Amount, CloseDate, AccountId
            FROM Opportunity
            WHERE StageName = :stage
        ]);
    }
    
    public AggregateResult[] selectTotalByStage() {
        return [
            SELECT StageName, COUNT(Id) cnt, SUM(Amount) total
            FROM Opportunity
            WHERE IsClosed = false
            WITH SECURITY_ENFORCED
            GROUP BY StageName
        ];
    }
}
```

---

### Domain Pattern

**Purpose**: Encapsulate object-specific behavior and validation.

**When to Use**:
- Complex validation rules
- Derived field calculations
- Object-specific business rules

**Implementation**:
```apex
public class Opportunities {
    
    private List<Opportunity> records;
    
    public Opportunities(List<Opportunity> records) {
        this.records = records;
    }
    
    public Opportunities(Set<Id> ids) {
        this.records = new OpportunitySelector().selectById(ids);
    }
    
    // Validation
    public void validate() {
        for (Opportunity opp : records) {
            if (opp.Amount != null && opp.Amount < 0) {
                opp.addError('Amount cannot be negative');
            }
            
            if (opp.CloseDate != null && opp.CloseDate < Date.today() && 
                opp.StageName != 'Closed Won' && opp.StageName != 'Closed Lost') {
                opp.addError('Close date cannot be in the past for open opportunities');
            }
        }
    }
    
    // Field defaulting
    public void setDefaults() {
        for (Opportunity opp : records) {
            if (opp.StageName == null) {
                opp.StageName = 'Prospecting';
            }
            if (opp.Probability == null) {
                opp.Probability = getStageProbability(opp.StageName);
            }
        }
    }
    
    // Derived calculations
    public void calculateForecast() {
        for (Opportunity opp : records) {
            if (opp.Amount != null && opp.Probability != null) {
                opp.Forecast_Amount__c = opp.Amount * (opp.Probability / 100);
            }
        }
    }
    
    // Filter operations
    public List<Opportunity> getHighValue(Decimal threshold) {
        List<Opportunity> result = new List<Opportunity>();
        for (Opportunity opp : records) {
            if (opp.Amount != null && opp.Amount >= threshold) {
                result.add(opp);
            }
        }
        return result;
    }
    
    // Bulk operations
    public Set<Id> getAccountIds() {
        Set<Id> accountIds = new Set<Id>();
        for (Opportunity opp : records) {
            if (opp.AccountId != null) {
                accountIds.add(opp.AccountId);
            }
        }
        return accountIds;
    }
    
    private Decimal getStageProbability(String stage) {
        Map<String, Decimal> probabilities = new Map<String, Decimal>{
            'Prospecting' => 10,
            'Qualification' => 20,
            'Needs Analysis' => 40,
            'Proposal' => 60,
            'Negotiation' => 80,
            'Closed Won' => 100,
            'Closed Lost' => 0
        };
        return probabilities.get(stage);
    }
}
```

---

### Unit of Work Pattern

**Purpose**: Manage complex transactions with multiple DML operations.

**When to Use**:
- Multiple related objects need to be saved
- Need to defer DML until end of transaction
- Complex parent-child relationships

**Implementation**:
```apex
public class UnitOfWork {
    
    private Map<Schema.SObjectType, List<SObject>> newRecords;
    private Map<Schema.SObjectType, List<SObject>> dirtyRecords;
    private Map<Schema.SObjectType, List<SObject>> deletedRecords;
    private List<Schema.SObjectType> objectOrder;
    
    public UnitOfWork(List<Schema.SObjectType> objectOrder) {
        this.objectOrder = objectOrder;
        this.newRecords = new Map<Schema.SObjectType, List<SObject>>();
        this.dirtyRecords = new Map<Schema.SObjectType, List<SObject>>();
        this.deletedRecords = new Map<Schema.SObjectType, List<SObject>>();
        
        for (Schema.SObjectType sObjType : objectOrder) {
            newRecords.put(sObjType, new List<SObject>());
            dirtyRecords.put(sObjType, new List<SObject>());
            deletedRecords.put(sObjType, new List<SObject>());
        }
    }
    
    public void registerNew(SObject record) {
        Schema.SObjectType sObjType = record.getSObjectType();
        newRecords.get(sObjType).add(record);
    }
    
    public void registerNew(List<SObject> records) {
        for (SObject record : records) {
            registerNew(record);
        }
    }
    
    public void registerDirty(SObject record) {
        Schema.SObjectType sObjType = record.getSObjectType();
        dirtyRecords.get(sObjType).add(record);
    }
    
    public void registerDeleted(SObject record) {
        Schema.SObjectType sObjType = record.getSObjectType();
        deletedRecords.get(sObjType).add(record);
    }
    
    public void commitWork() {
        Savepoint sp = Database.setSavepoint();
        
        try {
            // Insert in order (parents first)
            for (Schema.SObjectType sObjType : objectOrder) {
                if (!newRecords.get(sObjType).isEmpty()) {
                    insert newRecords.get(sObjType);
                }
            }
            
            // Update in order
            for (Schema.SObjectType sObjType : objectOrder) {
                if (!dirtyRecords.get(sObjType).isEmpty()) {
                    update dirtyRecords.get(sObjType);
                }
            }
            
            // Delete in reverse order (children first)
            for (Integer i = objectOrder.size() - 1; i >= 0; i--) {
                Schema.SObjectType sObjType = objectOrder[i];
                if (!deletedRecords.get(sObjType).isEmpty()) {
                    delete deletedRecords.get(sObjType);
                }
            }
            
        } catch (Exception e) {
            Database.rollback(sp);
            throw e;
        }
    }
}

// Usage
public class OrderService {
    public void createOrderWithItems(OrderDTO orderDto) {
        UnitOfWork uow = new UnitOfWork(new List<Schema.SObjectType>{
            Account.SObjectType,
            Order.SObjectType,
            OrderItem.SObjectType
        });
        
        Order order = new Order(
            AccountId = orderDto.accountId,
            Status = 'Draft',
            EffectiveDate = Date.today()
        );
        uow.registerNew(order);
        
        for (OrderItemDTO itemDto : orderDto.items) {
            OrderItem item = new OrderItem(
                OrderId = order.Id,  // Will be populated after insert
                Product2Id = itemDto.productId,
                Quantity = itemDto.quantity,
                UnitPrice = itemDto.price
            );
            uow.registerNew(item);
        }
        
        uow.commitWork();
    }
}
```

---

## Behavioral Patterns

### Strategy Pattern

**Purpose**: Define a family of algorithms and make them interchangeable.

**When to Use**:
- Multiple algorithms for same operation
- Algorithm selection at runtime
- Need to add new algorithms without changing existing code

**Implementation**:
```apex
// Strategy interface
public interface IDiscountStrategy {
    Decimal calculateDiscount(Opportunity opp);
}

// Concrete strategies
public class VolumeDiscountStrategy implements IDiscountStrategy {
    public Decimal calculateDiscount(Opportunity opp) {
        if (opp.Amount > 100000) return 0.15;
        if (opp.Amount > 50000) return 0.10;
        if (opp.Amount > 10000) return 0.05;
        return 0;
    }
}

public class LoyaltyDiscountStrategy implements IDiscountStrategy {
    public Decimal calculateDiscount(Opportunity opp) {
        // Query account history
        Integer yearlyOrders = [
            SELECT COUNT() FROM Opportunity 
            WHERE AccountId = :opp.AccountId 
            AND StageName = 'Closed Won'
            AND CloseDate = THIS_YEAR
        ];
        
        if (yearlyOrders > 10) return 0.20;
        if (yearlyOrders > 5) return 0.10;
        return 0;
    }
}

public class SeasonalDiscountStrategy implements IDiscountStrategy {
    public Decimal calculateDiscount(Opportunity opp) {
        Integer month = Date.today().month();
        // Q4 promotion
        if (month >= 10 && month <= 12) return 0.12;
        return 0;
    }
}

// Strategy factory
public class DiscountStrategyFactory {
    public static IDiscountStrategy getStrategy(String type) {
        switch on type {
            when 'VOLUME' { return new VolumeDiscountStrategy(); }
            when 'LOYALTY' { return new LoyaltyDiscountStrategy(); }
            when 'SEASONAL' { return new SeasonalDiscountStrategy(); }
            when else { return new VolumeDiscountStrategy(); }
        }
    }
}

// Usage
public class PricingService {
    public Decimal calculateFinalPrice(Opportunity opp, String discountType) {
        IDiscountStrategy strategy = DiscountStrategyFactory.getStrategy(discountType);
        Decimal discount = strategy.calculateDiscount(opp);
        return opp.Amount * (1 - discount);
    }
}
```

---

### Factory Pattern

**Purpose**: Create objects without specifying exact class.

**When to Use**:
- Object creation logic is complex
- Need to create different types based on criteria
- Decouple object creation from usage

**Implementation**:
```apex
// Abstract notification
public abstract class Notification {
    protected String recipient;
    protected String subject;
    protected String body;
    
    public Notification(String recipient, String subject, String body) {
        this.recipient = recipient;
        this.subject = subject;
        this.body = body;
    }
    
    public abstract void send();
}

// Concrete notifications
public class EmailNotification extends Notification {
    public EmailNotification(String recipient, String subject, String body) {
        super(recipient, subject, body);
    }
    
    public override void send() {
        Messaging.SingleEmailMessage email = new Messaging.SingleEmailMessage();
        email.setToAddresses(new List<String>{recipient});
        email.setSubject(subject);
        email.setPlainTextBody(body);
        Messaging.sendEmail(new List<Messaging.SingleEmailMessage>{email});
    }
}

public class ChatterNotification extends Notification {
    public ChatterNotification(String recipient, String subject, String body) {
        super(recipient, subject, body);
    }
    
    public override void send() {
        FeedItem post = new FeedItem(
            ParentId = recipient,
            Body = subject + '\n\n' + body
        );
        insert post;
    }
}

public class PushNotification extends Notification {
    public PushNotification(String recipient, String subject, String body) {
        super(recipient, subject, body);
    }
    
    public override void send() {
        // Send push notification via custom metadata config
    }
}

// Factory
public class NotificationFactory {
    
    public enum NotificationType { EMAIL, CHATTER, PUSH }
    
    public static Notification createNotification(
        NotificationType type, 
        String recipient, 
        String subject, 
        String body
    ) {
        switch on type {
            when EMAIL { return new EmailNotification(recipient, subject, body); }
            when CHATTER { return new ChatterNotification(recipient, subject, body); }
            when PUSH { return new PushNotification(recipient, subject, body); }
            when else { return new EmailNotification(recipient, subject, body); }
        }
    }
    
    public static List<Notification> createFromPreferences(Id userId, String subject, String body) {
        List<Notification> notifications = new List<Notification>();
        
        User_Notification_Preferences__c prefs = User_Notification_Preferences__c.getInstance(userId);
        
        if (prefs?.Email_Enabled__c == true) {
            User u = [SELECT Email FROM User WHERE Id = :userId];
            notifications.add(createNotification(NotificationType.EMAIL, u.Email, subject, body));
        }
        
        if (prefs?.Chatter_Enabled__c == true) {
            notifications.add(createNotification(NotificationType.CHATTER, userId, subject, body));
        }
        
        if (prefs?.Push_Enabled__c == true) {
            notifications.add(createNotification(NotificationType.PUSH, userId, subject, body));
        }
        
        return notifications;
    }
}

// Usage
public class AlertService {
    public void sendAlert(Id userId, String subject, String body) {
        List<Notification> notifications = NotificationFactory.createFromPreferences(userId, subject, body);
        for (Notification n : notifications) {
            n.send();
        }
    }
}
```

---

### Builder Pattern

**Purpose**: Construct complex objects step by step.

**When to Use**:
- Object has many optional parameters
- Object construction is multi-step
- Need readable object construction

**Implementation**:
```apex
public class OpportunityBuilder {
    
    private Opportunity opp;
    
    public OpportunityBuilder() {
        this.opp = new Opportunity();
        // Set required defaults
        this.opp.StageName = 'Prospecting';
        this.opp.CloseDate = Date.today().addMonths(3);
    }
    
    public OpportunityBuilder withName(String name) {
        this.opp.Name = name;
        return this;
    }
    
    public OpportunityBuilder withAccount(Id accountId) {
        this.opp.AccountId = accountId;
        return this;
    }
    
    public OpportunityBuilder withAmount(Decimal amount) {
        this.opp.Amount = amount;
        return this;
    }
    
    public OpportunityBuilder withStage(String stage) {
        this.opp.StageName = stage;
        return this;
    }
    
    public OpportunityBuilder withCloseDate(Date closeDate) {
        this.opp.CloseDate = closeDate;
        return this;
    }
    
    public OpportunityBuilder withOwner(Id ownerId) {
        this.opp.OwnerId = ownerId;
        return this;
    }
    
    public OpportunityBuilder withProbability(Decimal probability) {
        this.opp.Probability = probability;
        return this;
    }
    
    public OpportunityBuilder withDescription(String description) {
        this.opp.Description = description;
        return this;
    }
    
    public Opportunity build() {
        validate();
        return this.opp;
    }
    
    public Opportunity buildAndInsert() {
        validate();
        insert this.opp;
        return this.opp;
    }
    
    private void validate() {
        if (String.isBlank(this.opp.Name)) {
            throw new BuilderException('Opportunity name is required');
        }
        if (this.opp.AccountId == null) {
            throw new BuilderException('Account is required');
        }
    }
    
    public class BuilderException extends Exception {}
}

// Usage
Opportunity opp = new OpportunityBuilder()
    .withName('Big Deal')
    .withAccount(accountId)
    .withAmount(100000)
    .withStage('Qualification')
    .withCloseDate(Date.today().addMonths(2))
    .withProbability(30)
    .buildAndInsert();
```

---

## Concurrency Patterns

### Async Continuation Pattern

**Purpose**: Chain async operations without hitting limits.

**See**: `INTEGRATION_PATTERNS.md` for Queueable chaining examples.

### Platform Event Pattern

**Purpose**: Decouple components through event-driven architecture.

**See**: `INTEGRATION_PATTERNS.md` for Platform Event examples.
