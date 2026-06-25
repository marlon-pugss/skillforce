---
name: generating-apex-repository
description: "Create, review, and refactor Apex Repository classes following the AbstractRepository pattern: injection-safe dynamic SOQL via Database.query with bind variables, findBy_X_Y naming, and aggregate helpers. TRIGGER when: user creates/edits a *Repository class, adds a finder/aggregate method, or centralizes SOQL. DO NOT TRIGGER when: writing business logic (use generating-apex-service-class), triggers (use building-apex-triggers), or tests (use generating-apex-integration-tests)."
license: TBD
metadata:
  version: "1.0"
---

# generating-apex-repository: Apex Repository Layer

Use this skill to build the **data-access layer**: Repository classes that
centralize all SOQL/DML for an object, extend a shared `AbstractRepository`, and
expose intention-revealing finder and aggregate methods.

## When This Skill Owns the Task

Use `generating-apex-repository` when the work involves:
- a `<SObject>Repository` class (new or refactor)
- a `findBy_<Field>_<Condition>` finder method
- an aggregate (`COUNT`, `SUM`) helper returning a `Map`
- moving inline SOQL out of services/handlers into the repository

Delegate elsewhere when the user is:
- writing the business rule that calls the repository -> [generating-apex-service-class](../generating-apex-service-class/SKILL.md)
- reviewing query selectivity / limits -> [reviewing-apex-governor-limits](../reviewing-apex-governor-limits/SKILL.md)

## Required Context to Gather First

Ask for or infer before writing code:
- the target SObject and the fields the callers actually need (keep `getBaseQuery()` lean)
- the filter(s) each finder must apply (which fields, which operators)
- whether an aggregate (COUNT/SUM grouped by a parent) is needed
- whether the project enforces FLS/sharing in the data layer (see Security / FLS)

## Core Pattern Reference

Every repository must follow this structure:

```apex
public class MyObjectRepository extends AbstractRepository {
    public MyObject__c findById(String recordId) {
        List<MyObject__c> records = this.findById(new List<String>{recordId});
        return records.isEmpty() ? null : records[0];
    }
    public List<MyObject__c> findById(List<String> recordIds) {
        return Database.query(getBaseQuery() +
                              'FROM MyObject__c ' +
                              'WHERE Id IN :recordIds');
    }
    private String getBaseQuery() {
        return 'SELECT Id, Field1__c, Field2__c ';
    }
}
```

## Finder Example (two-field filter)

The bind variables (`:accountIds`, `:status`) are the method parameters, so they
are in scope when `Database.query` runs.

```apex
public List<Contract> findBy_AccountIds_Status(List<String> accountIds, String status) {
    return Database.query(getBaseQuery() +
                          'FROM Contract ' +
                          'WHERE AccountId IN :accountIds ' +
                          'AND Status = :status');
}
```

## Aggregate Example (Map<Id, Decimal>)

Aggregates can use inline SOQL (there is no user-input concatenation). The alias
is lowercase camelCase and must match the `ar.get(...)` key exactly.

```apex
public Map<Id, Decimal> countContractsByAccountId(List<String> accountIds) {
    Map<Id, Decimal> countByAccount = new Map<Id, Decimal>();
    for (AggregateResult ar : [
        SELECT AccountId accountId, COUNT(Id) total
        FROM Contract
        WHERE AccountId IN :accountIds
        GROUP BY AccountId
    ]) {
        countByAccount.put((Id) ar.get('accountId'), (Decimal) ar.get('total'));
    }
    return countByAccount;
}
```

## Mandatory Rules

1. **Class declaration:** always `public class <SObject>Repository extends AbstractRepository`.
2. **Method naming:** `findBy_<Field1>_<Field2>` (PascalCase fields, underscore separator).
3. **Query construction:** always `Database.query(getBaseQuery() + 'FROM ...')` with bind variables.
4. **getBaseQuery():** private, includes `Id`, with a trailing space before `FROM`.
5. **Aggregate methods:** return `Map<Id, Decimal>`; the alias must be lowercase camelCase.
6. **Parameter types:** use collections (`List<String>`, `Set<Id>`) correctly.
7. **Instantiation:** never inline. Use a `@TestVisible private` field + constructor initialization.
8. Every query must have a genuine `WHERE` clause — no full-table scans, no always-true conditions.

## Security / FLS (optional)

If the project enforces field-level security and sharing in the data layer, apply
user-mode enforcement **consistently** across the repository — do not mix modes:
- `Database.query(qry, AccessLevel.USER_MODE)` or add `WITH USER_MODE` to the SOQL
- or `WITH SECURITY_ENFORCED` (throws on inaccessible fields)
- on writes, strip inaccessible fields with `Security.stripInaccessible(...)`

## Gotchas

| Pitfall | Resolution |
|---------|------------|
| Bind variable not in scope at query time | The `:x` referenced must be a method/class variable in scope when `Database.query` runs |
| Wrong aggregate cast | Use `(Id) ar.get('accountId')`, `(Decimal) ar.get('total')`; alias names must match exactly |
| Missing trailing space in `getBaseQuery()` | End with `'... Field2__c '` so it does not produce `Field2__cFROM` |
| Concatenating user input into SOQL | Injection risk — always bind; if truly unavoidable, wrap with `String.escapeSingleQuotes(...)` |
| Non-selective filter (non-indexed field) | Large objects raise selectivity errors; filter on indexed fields or narrow scope |
| `IN :emptyList` | Returns no rows (safe), but guard earlier to skip the query entirely |

## Review Checklist

1. Extends `AbstractRepository`.
2. `findById(String)` delegates to `findById(List<String>)`.
3. All queries use `Database.query` with bind variables (no string concatenation of user input).
4. Method names follow the `findBy_<Field>_<Condition>` convention.
5. `getBaseQuery()` is private and includes `Id` with a trailing space.
6. Aggregate methods cast `AggregateResult` correctly and return `Map<Id, Decimal>`.
7. No query without a real `WHERE` clause.
8. FLS/sharing enforcement applied consistently if the project requires it.
