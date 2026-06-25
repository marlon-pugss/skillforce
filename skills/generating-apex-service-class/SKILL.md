---
name: generating-apex-service-class
description: "Create and edit Apex business-logic classes (service/domain layer) that orchestrate Repositories and Builders. TRIGGER when: user implements a service class, a fill-fields/rollup class, or any business rule that reads via a Repository and writes via a Builder. DO NOT TRIGGER when: writing triggers/handlers (use building-apex-triggers), test classes (use generating-apex-integration-tests), repository classes (use generating-apex-repository), or batch classes (use generating-apex-batch)."
license: TBD
metadata:
  version: "1.0"
---

# generating-apex-service-class: Apex Service / Domain Logic

Use this skill to implement and edit **business-logic classes** (service/domain
layer) that concentrate rules and orchestrate the data layer — for example
rollup/fill-fields services that recalculate parent fields from child records.

This skill does **not** create triggers, handlers, or test classes. Delegate
those to [building-apex-triggers](../building-apex-triggers/SKILL.md) and
[generating-apex-integration-tests](../generating-apex-integration-tests/SKILL.md).

## When This Skill Owns the Task

Use `generating-apex-service-class` when the work involves:
- a class that holds business rules invoked by a trigger handler
- recalculating/aggregating fields on a parent from related child records
- orchestrating Repository (reads/writes) + Builder (record assembly)

Delegate elsewhere when the user is:
- creating the trigger/handler wiring -> [building-apex-triggers](../building-apex-triggers/SKILL.md)
- writing the repository/finder methods -> [generating-apex-repository](../generating-apex-repository/SKILL.md)
- writing tests -> [generating-apex-integration-tests](../generating-apex-integration-tests/SKILL.md)
- reviewing for limits -> [reviewing-apex-governor-limits](../reviewing-apex-governor-limits/SKILL.md)

## Required Context to Gather First

Ask for or infer before writing code:
- the SObject(s) involved and the parent/child relationship (which is parent, which is child)
- the exact business rule: when it runs and what it computes
- the trigger context that will call it (insert/update/delete; before/after)
- which fields are **read** and which are **written**
- whether an old-vs-new comparison is needed to skip work when nothing relevant changed

## Expected Project Dependencies

This skill assumes the project already provides these conventions (they are **not**
Salesforce built-ins):
- a base `AbstractRepository` + per-object `Repository` classes (data access)
- per-object `Builder` classes (record assembly)
- a central `Constants` class (status/stage values)
- a `CollectionHelper` utility (`extractIds`, `groupByField`)

If any required finder, setter, or helper is missing, **signal it and delegate**
(e.g. a missing finder -> [generating-apex-repository](../generating-apex-repository/SKILL.md)).
Never invent a method or setter silently.

## Before Coding (mandatory)

1. Open the closest existing service class in the project and mirror its style.
2. Confirm the finder you need already exists in the Repository; if not, signal it.
3. Confirm the setter you need already exists in the Builder; same rule.
4. Implement the minimum necessary logic — no artificial complexity.
5. Signal that a test class must be created/updated (out of scope here).

## MAXIMUM PRIORITY RULE — never violate

**Never build a query that could return ALL records of an object.**
- Every SOQL needs a `WHERE` clause that **truly filters**.
- `WHERE Id != null`, `WHERE Id != ''`, and any always-true condition are
  **disguised full scans** — as forbidden as having no `WHERE` at all.
- With dynamic `WHERE` joined by `OR`, a single tautological fragment nullifies
  every other filter.
- If the logic cannot filter in SOQL, find another strategy or stop and ask.

## Strict Rules (non-negotiable)

1. The class concentrates the business logic; the trigger/handler only delegates.
2. All query/persistence goes through a Repository — SOQL/DML in loops is forbidden.
3. Use the corresponding `Builder` to assemble update records.
4. Extract IDs with `CollectionHelper.extractIds(...)`.
5. Group collections with `CollectionHelper.groupByField(...)` when applicable.
6. Always write guard clauses for `null` and empty lists before any iteration/query.
7. Consider active Flows: never set required fields to `null`.
8. Use constants from a central `Constants` class (e.g. `Constants.STATUS_SIGNED`,
   `Constants.STATUS_LOST`). Hardcoding status/stage values is forbidden.
9. Dependencies (Repositories, Builders) must be declared `@TestVisible` and
   initialized in the constructor.
10. Be concise — no artificial complexity.
11. **Comments:** use brief `//` to document **business rules** (the why).
    Multi-line Javadoc and comments that merely restate the code are forbidden.

## When to use List vs Map for dedup

| Situation | Structure | Reason |
|-----------|-----------|--------|
| Iterating by **unique IDs** (via `Set<String>`) | Direct `List<Parent>` | IDs are already unique, no duplicate risk |
| Iterating by **child records** (several per parent) | `Map<Id, Parent>` with `containsKey` | Needed to deduplicate by parent Id |

## Pattern 1 — Iteration by unique IDs (direct List)

```apex
public class AccountRollupService {
    @TestVisible ContractRepository contractRepository;
    @TestVisible AccountBuilder accountBuilder;
    @TestVisible AccountRepository accountRepository;

    public AccountRollupService(){
        contractRepository = new ContractRepository();
        accountBuilder     = new AccountBuilder();
        accountRepository  = new AccountRepository();
    }

    public void recalculateSignedContracts(List<Contract> newContracts, Map<Id, SObject> oldContracts){
        // returns only the parent Ids whose rollup can actually change (diff old vs new)
        Set<String> accountIds = getAccountIdsToRecalculate(newContracts, oldContracts);
        if (accountIds == null || accountIds.isEmpty()) return;

        List<Contract> signedContracts = contractRepository.findBy_AccountIds_Status(
            new List<String>(accountIds), Constants.STATUS_SIGNED);

        Map<String, List<SObject>> contractsByAccountId = CollectionHelper.groupByField('AccountId', signedContracts);

        List<Account> accountsToUpdate = new List<Account>();
        for (String accountId : accountIds){
            List<SObject> related = contractsByAccountId?.get(accountId);
            Decimal count = (related != null) ? related.size() : 0;
            accountsToUpdate.add(accountBuilder.id(accountId)
                                               .signedContractCount(count)
                                               .build());
        }

        if (!accountsToUpdate.isEmpty())
            accountRepository.save(accountsToUpdate);
    }
}
```

## Pattern 2 — Iteration by child records (Map with dedup)

Note how the dependencies are declared and initialized in the constructor (Rule 9),
exactly like Pattern 1 — the method below is never shown "loose".

```apex
public class OpportunityRollupService {
    @TestVisible ContractRepository contractRepository;
    @TestVisible OpportunityBuilder opportunityBuilder;
    @TestVisible OpportunityRepository opportunityRepository;

    public OpportunityRollupService(){
        contractRepository    = new ContractRepository();
        opportunityBuilder    = new OpportunityBuilder();
        opportunityRepository = new OpportunityRepository();
    }

    public void countChildContracts(List<Contract> newContracts){
        List<String> parentIds = CollectionHelper.extractIds('Opportunity__c', newContracts);
        if (parentIds == null || parentIds.isEmpty()) return;

        List<Contract> contracts = contractRepository.findBy_OpportunityIds_NotStatus(parentIds, Constants.STATUS_LOST);
        Map<String, List<SObject>> contractsByParentId = CollectionHelper.groupByField('Opportunity__c', contracts);

        Map<Id, Opportunity> toUpdateById = new Map<Id, Opportunity>();
        for (Contract record : newContracts){
            if (record.Opportunity__c == null) continue;
            if (!toUpdateById.containsKey(record.Opportunity__c)) {
                List<SObject> related = contractsByParentId?.get(record.Opportunity__c);
                Decimal childCount = (related != null) ? related.size() : 0;
                toUpdateById.put(record.Opportunity__c,
                                 opportunityBuilder.id(record.Opportunity__c)
                                                   .childContractCount(childCount)
                                                   .build());
            }
        }

        if (!toUpdateById.isEmpty())
            opportunityRepository.save(toUpdateById.values());
    }
}
```

## Gotchas

| Pitfall | Resolution |
|---------|------------|
| `oldRecordsMap` is `null` on INSERT | Guard before dereferencing; only diff old vs new on UPDATE |
| Setting a required field to `null` | Breaks active Flows / validation rules — never null a required field |
| `.size()` on a possibly-null list | Use `(x != null) ? x.size() : 0` |
| Re-entrant trigger recursion | The save re-fires the trigger; guard with a static flag or change detection |
| `List` used when several children share a parent | Duplicates the parent; use `Map<Id, Parent>` + `containsKey` |
| Fetching related records inside the loop | Bulkify: one grouped query before the loop |
| Recalculating when nothing relevant changed | Compare old vs new and short-circuit early to save CPU/DML |

## Delivery Checklist

- [ ] Dependencies declared `@TestVisible` and initialized in the constructor.
- [ ] Guard clauses covering `null`/empty before any loop or query.
- [ ] `oldRecordsMap` handled safely for INSERT (null) vs UPDATE.
- [ ] Zero SOQL/DML inside loops.
- [ ] Reads through the Repository, record assembly through the Builder.
- [ ] Constants used for status/stage values (no hardcoding).
- [ ] Correct iteration pattern (List vs Map) chosen deliberately.
- [ ] `.cls-meta.xml` created/updated for new classes.
- [ ] Clear note that the test class must be created/updated.
