---
name: generating-apex-batch
description: "Generate a Batch Apex class plus its meta-xml and an integrated test class, following the repository and builder patterns. TRIGGER when: user asks to create/build/generate a Batch Apex class or a Database.Batchable job. DO NOT TRIGGER when: writing a synchronous service (use generating-apex-service-class), a trigger (use building-apex-triggers), or only a test (use generating-apex-integration-tests)."
license: TBD
metadata:
  version: "1.0"
---

# generating-apex-batch: Batch Apex Generator

Use this skill to generate the full set of artifacts for a Batch Apex job in the
repository pattern: the Batch class, its `.cls-meta.xml`, and an integrated test
class.

## When This Skill Owns the Task

Use `generating-apex-batch` when the user needs a `Database.Batchable` job
(scheduled/bulk processing). Reuse the data layer from
[generating-apex-repository](../generating-apex-repository/SKILL.md) and test
conventions from [generating-apex-integration-tests](../generating-apex-integration-tests/SKILL.md).

## Required Context to Gather First

- the target SObject and a **selective** `WHERE` for `start()` (no full scans)
- what `execute()` does per record and what it writes
- whether `execute()` makes callouts (needs `Database.AllowsCallouts`)
- whether state must persist across batches (`Database.Stateful`)
- the batch size and whether the job must be scheduled (and how often)

## Inputs to Confirm

- `entityName`: target object (e.g. `Opportunity`, `Account`).
- `batchName`: class name (e.g. `SyncExpiredContractsBatch`).
- `filterCondition`: the `WHERE` clause (must genuinely filter — no full scans).
- `logicDescription`: short description of the `execute` logic.

## Batch Class Pattern (`{{batchName}}.cls`)

```apex
public class {{batchName}} implements Database.Batchable<SObject>, Database.Stateful {

    @TestVisible private {{entityName}}Repository entityRepository;
    private Logger logger;

    public {{batchName}}() {
        entityRepository = new {{entityName}}Repository();
        logger = Logger.getInstance();
    }

    public Database.QueryLocator start(Database.BatchableContext context) {
        try {
            return Database.getQueryLocator(
                entityRepository.getBaseQuery() +
                'FROM {{entityName}} ' +
                'WHERE {{filterCondition}}'
            );
        } catch (Exception ex) {
            logger.addError(ex, 'Start Exception');
            logger.createLog('{{batchName}}');
            return Database.getQueryLocator('SELECT Id FROM {{entityName}} WHERE Id = null');
        }
    }

    public void execute(Database.BatchableContext context, List<{{entityName}}> scope) {
        Logger logger = Logger.getInstance();
        try {
            // {{logicDescription}}
            for ({{entityName}} record : scope) {
                try {
                    // process each record
                } catch (Exception ex) {
                    logger.addError(ex, record.Id);
                }
            }
        } catch (Exception ex) {
            logger.addError(ex, 'Execute Exception');
        } finally {
            logger.createLog(String.valueOf(this).split(':')[0]);
        }
    }

    public void finish(Database.BatchableContext context) {}
}
```

## Test Class Pattern (`{{batchName}}Test.cls`)

```apex
@isTest
private class {{batchName}}Test {

    @isTest //{{batchName}}
    static void givenRecordsMatchingFilter_whenBatchRuns_thenLogicIsApplied() {
        // Setup — insert records that MATCH the filter
        Account account = new Account(Name = 'Test Account', Website = 'test.com');
        insert account;

        // ...setup matching records...

        // Act
        Test.startTest();
        Database.executeBatch(new {{batchName}}(), 200);
        Test.stopTest();

        // Assert
        // {{entityName}} result = [SELECT ... FROM {{entityName}} WHERE Id = :record.Id];
        // Assert.areEqual(expectedValue, result.SomeField__c);
    }

    @isTest //{{batchName}}
    static void givenRecordsNotMatchingFilter_whenBatchRuns_thenNoChanges() {
        // Setup — insert records that do NOT match the filter
        Account account = new Account(Name = 'Test Account', Website = 'test.com');
        insert account;

        // Act
        Test.startTest();
        Database.executeBatch(new {{batchName}}(), 200);
        Test.stopTest();

        // Assert — verify no changes
    }
}
```

## Scheduling (optional)

If the job must run on a schedule, make it `Schedulable` (or use a thin scheduler
class) and schedule with a CRON expression:

```apex
public class {{batchName}}Scheduler implements Schedulable {
    public void execute(SchedulableContext sc) {
        Database.executeBatch(new {{batchName}}(), 200);
    }
}
// System.schedule('{{batchName}} nightly', '0 0 2 * * ?', new {{batchName}}Scheduler());
```

## Gotchas

| Pitfall | Resolution |
|---------|------------|
| Full scan in `start()` | The locator must filter; never select an entire object |
| Callouts in `execute()` without `Database.AllowsCallouts` | Add the interface, or the callout throws |
| Expecting state to persist without `Database.Stateful` | Member variables reset each `execute` unless stateful |
| One bad record aborts the whole batch | Wrap per-record work in `try/catch` and log, as shown |
| Test only covers `execute` | Cover `start`, `execute`, and `finish`; assert end-state |
| Batch size too large with heavy logic | Lower the scope size (e.g. 200 -> 50) to stay under limits |

## Delivery Checklist

- [ ] Batch implements `Database.Batchable<SObject>` and `Database.Stateful` (if state is needed).
- [ ] `start()` wrapped in `try/catch` with a `WHERE Id = null` fallback query.
- [ ] `execute()` uses a `Logger` instance with per-record `try/catch` and a `finally`.
- [ ] `finish()` present (empty unless chaining/notification is needed).
- [ ] Repository used in `start()` — no raw inline SOQL.
- [ ] `Database.AllowsCallouts` added if `execute()` calls out.
- [ ] Test class covers `start`/`execute`/`finish` with real DML and BDD naming.
- [ ] Both `.cls-meta.xml` files created.
