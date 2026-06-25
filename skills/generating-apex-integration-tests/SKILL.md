---
name: generating-apex-integration-tests
description: "Create, review, and fix integrated Apex test classes that exercise triggers/services through real DML with BDD naming. TRIGGER when: user writes or repairs *Test.cls classes that insert/update real records to cover a handler or service. DO NOT TRIGGER when: running existing tests / coverage analysis (use validating-apex-changes), writing the production code (use generating-apex-service-class or building-apex-triggers)."
license: TBD
metadata:
  version: "1.0"
---

# generating-apex-integration-tests: Integrated Apex Tests

Use this skill to author and fix **integrated Apex tests** that drive behavior
through real DML (not mocks) and use BDD-style method names. The goal is
coverage that proves the trigger/service chain actually works end to end.

## When This Skill Owns the Task

Use `generating-apex-integration-tests` when the work involves:
- a `*Test.cls` that inserts/updates records to fire a handler or service
- fixing a failing test by correcting production code or setup data
- improving integrated coverage of a logic path

Delegate elsewhere when the user is:
- only running tests / checking coverage -> [validating-apex-changes](../validating-apex-changes/SKILL.md)
- writing the production logic -> [generating-apex-service-class](../generating-apex-service-class/SKILL.md)

## Required Context to Gather First

Ask for or infer before writing the test:
- which class/handler/trigger is under test and which method/behavior to cover
- the happy path **and** at least one negative/edge path
- the minimum records (and required fields) needed to fire the automation
- any validation rule or required field that the setup must satisfy
- the expected end-state to assert (which field on which record)

## Mandatory Rules

1. Tests are **always integrated** (real DML).
2. BDD naming: `givenCondition_whenAction_thenResult`.
3. Use `Assert.areEqual(expected, actual)` — never `System.assertEquals`.
4. Use `Assert.isTrue` / `Assert.isFalse` for booleans — no message parameter.
5. Wrap the triggering action with `Test.startTest()` / `Test.stopTest()`.
6. Add `@isTest //validatedMethodName` above each method.
7. Create `.cls-meta.xml` for every new test class.
8. Indent with **4 spaces**.
9. No `@testSetup`, no `TestDataFactory` — set up inline per method.

## When a Test Fails with `CANNOT_EXECUTE_FLOW_TRIGGER`

- Do not change the approach just to bypass the Flow.
- Identify the missing required field.
- Fix the **production code** with a guard clause.

## Minimum Setup Examples

- **Account:** `new Account(Name = 'Test', Website = 'test.com')`.
- **Opportunity:** `Name`, `StageName = 'Prospecting'`, `AccountId`, `CloseDate`,
  plus any custom required field your org enforces.
- **Contract:** `StartDate` is required. If a validation rule blocks status
  changes, set a bypass flag (e.g. `BypassValidation__c = 'test'`) alongside the
  `Status` change so the test can proceed.

## Picklist / status values

Use constants from a central `Constants` class instead of hardcoded strings, and
verify the valid values for the **target org** before asserting on them — picklist
values are org-specific. Never assume a value like `'Draft'` exists.

## Test Structure Template

```apex
@isTest
private class MyServiceTest {

    @isTest //myMethodName
    static void givenCondition_whenAction_thenResult() {
        // Setup
        Account account = new Account(Name = 'Test', Website = 'test.com');
        insert account;

        // ...additional setup...

        // Act
        Test.startTest();
        insert someRecord; // or the DML that fires the handler
        Test.stopTest();

        // Assert
        SomeObject result = [SELECT Field FROM SomeObject WHERE Id = :someRecord.Id];
        Assert.areEqual(expectedValue, result.Field);
    }
}
```

## Negative-Path Example

```apex
@isTest //myMethodName
static void givenMissingParent_whenInsert_thenNoRollup() {
    Account account = new Account(Name = 'Test', Website = 'test.com');
    insert account;

    Test.startTest();
    insert new Contract(AccountId = account.Id, StartDate = Date.today());
    Test.stopTest();

    Account result = [SELECT Id, SignedContractCount__c FROM Account WHERE Id = :account.Id];
    Assert.areEqual(0, result.SignedContractCount__c);
}
```

## Gotchas

| Pitfall | Resolution |
|---------|------------|
| Wrapping setup inside `Test.startTest()` | Wrap only the triggering DML; do setup before `startTest()` |
| Asserting before async finishes | `@future`/Queueable/Batch run at `Test.stopTest()`; assert **after** it |
| `MIXED_DML_OPERATION` | Separate setup-object DML (User, Group) using `System.runAs` |
| Relying on org data | Tests do not see org data by default; create everything you assert on |
| Sharing-sensitive logic | Use `System.runAs(testUser)` to exercise the real permission context |
| Asserting on a stale in-memory record | Re-query the record after the DML to read trigger-updated fields |

## Delivery Checklist

- [ ] BDD method name: `givenX_whenY_thenZ`.
- [ ] `@isTest //methodName` annotation on each test method.
- [ ] Real DML — no mocks.
- [ ] `Test.startTest()` / `Test.stopTest()` wrapping only the triggering DML.
- [ ] Async behavior asserted after `Test.stopTest()`.
- [ ] At least one negative/edge path covered.
- [ ] `Assert.areEqual(expected, actual)` — never `System.assertEquals`.
- [ ] Validation-bypass flag set when changing a status guarded by a rule.
- [ ] `.cls-meta.xml` created for the new test class.
