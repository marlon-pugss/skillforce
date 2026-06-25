---
name: investigating-runtime-errors
description: "Investigate and diagnose runtime error logs captured in a custom logging object (header + items) in a Salesforce org. Reads via 'sf data query' and marks reviewed headers via 'sf data update' (a single review flag only). TRIGGER when: user asks to look at today's logs/errors, check the logging object, or diagnose trigger/batch/integration failures. DO NOT TRIGGER when: analyzing raw debug .log files (use reviewing-apex-governor-limits for limit-specific code review), writing tests (use generating-apex-integration-tests), or fixing the code (use generating-apex-service-class / building-apex-triggers)."
license: TBD
metadata:
  version: "1.0"
---

# investigating-runtime-errors: Custom Log Investigation

Use this skill to **monitor and diagnose runtime error logs** stored in a custom
logging object. The job: find failure records, read the error detail, identify
the root cause from the stack trace, report clearly and actionably, and **mark
the reviewed logs**.

This is an investigation skill. The ONLY data change it may make is setting a
single review flag (`Reviewed__c = true`) on the log headers it reviewed — it
never changes anything else, never writes code, never deploys.

## Required Context to Gather First

- the org alias to query (and confirm it is the right monitoring/production org)
- the time window (today, last N days, a specific date)
- whether to include already-reviewed logs (default: only unreviewed)
- any source filter (a specific trigger, batch, or integration name)
- the API names of your logging objects/fields if they differ from the model below

## Assumed Log Data Model

This skill assumes a two-layer custom logging schema (adapt the API names to your
org). A `Logger`-style helper typically populates these:

### `Log__c` (header — one per logged execution/transaction)
| Field | Type | Meaning |
| --- | --- | --- |
| `Name` | Auto Number | Record name, e.g. `LOG-#####` |
| `Interface__c` | Text | Source class/interface that produced the log (e.g. a trigger or batch name) |
| `FailQuantity__c` | Number | Errors accumulated in the transaction |
| `Status__c` | Formula (Text) | e.g. `IF(FailQuantity__c == 0, "Success", "Fail")` — derived; filter on `FailQuantity__c > 0` instead |
| `Date__c` | DateTime | Timestamp at log creation |
| `User__c` | Lookup/Text | User who ran it; use `User__r.Name` in queries |
| `Reviewed__c` | Checkbox | **Set by this skill** -> `true` once reviewed. By default only fetch `false` |

### `LogItem__c` (items — detail of each message/error)
| Field | Type | Meaning |
| --- | --- | --- |
| `Name` | Auto Number | Item name |
| `Log__c` | Master-Detail | FK to the header |
| `Item__c` | Text | Item category (e.g. `System.DmlException`, `Catch Exception`) |
| `FailDescription__c` | Long Text | Error message + stack trace. An item with this = ERROR |
| `Message__c` | Long Text | Informational content (request/response echo) |

Rule of thumb: an item with `FailDescription__c` populated is a failure; an item
with only `Message__c` is informational.

## Target Org

- Query the org alias the user provides. If your team monitors a single
  production-style org, default to that alias and **state which org was queried**
  in the report. Run `sf org list` only to confirm connectivity if a query fails
  with an auth error.
- Every `sf data query` must pass `--target-org <alias>`.

## How to Find the Logs

### Step 1 — list unreviewed headers for the period
By default fetch only logs not yet reviewed (`Reviewed__c = false`). Always
include `Reviewed__c` in the SELECT.

```bash
sf data query --target-org <alias> --query "SELECT Id, Name, Interface__c, FailQuantity__c, Status__c, Reviewed__c, Date__c, User__r.Name, CreatedDate FROM Log__c WHERE CreatedDate = TODAY AND Reviewed__c = false ORDER BY CreatedDate DESC"
```

Failures only (recommended filter):
```bash
sf data query --target-org <alias> --query "SELECT Id, Name, Interface__c, FailQuantity__c, Reviewed__c, Date__c, User__r.Name FROM Log__c WHERE CreatedDate = TODAY AND FailQuantity__c > 0 AND Reviewed__c = false ORDER BY CreatedDate DESC"
```

Useful date literals: `TODAY`, `YESTERDAY`, `LAST_N_DAYS:7`, `THIS_WEEK`,
`THIS_MONTH`. Filter by source with `AND Interface__c = 'Some Trigger'`.

### Step 2 — open the items of each failure header
```bash
sf data query --target-org <alias> --query "SELECT Id, Name, Item__c, FailDescription__c, Message__c FROM LogItem__c WHERE Log__c = '<LOG_ID>' ORDER BY CreatedDate ASC" --json
```
Use `--json` when `FailDescription__c` is large (stack traces with line breaks).

### Step 3 — diagnose
Read `FailDescription__c`, identify the originating class/method, and, if helpful,
read the source code of that class with read/grep tools to confirm the root cause.

### Step 4 — mark the reviewed logs
After reporting, mark every header reviewed in this run — successes and failures —
so they are not picked up again. One record at a time:
```bash
sf data update record --target-org <alias> --sobject Log__c --record-id <LOG_ID> --values "Reviewed__c=true"
```
Only ever set `Reviewed__c=true` — never touch any other field.

## How to Read an Error

`FailDescription__c` usually looks like:
```
Operation: AFTER_UPDATE | Records: 1

<exception message>

Class.<Class>.<method>: line N, column 1
Class.<Handler>.run: line N, column 1
Trigger.<Name>Trigger: line N, column 1
```
- **Top of the stack trace** = where the exception was thrown (most relevant).
- **Bottom** = entry point (trigger/batch/class that started it).
- `Item__c` gives the quick category.

### Common patterns
| Error in the message | Nature | Routing |
| --- | --- | --- |
| `UNABLE_TO_LOCK_ROW` | Lock contention; usually transient | If recurring: make the save async (Queueable) or order locks |
| `Too many SOQL queries: 101` / `Too many DML statements: 151` | SOQL/DML in a loop | [reviewing-apex-governor-limits](../reviewing-apex-governor-limits/SKILL.md) |
| `CPU time limit exceeded` / heap | Processing limit | [reviewing-apex-governor-limits](../reviewing-apex-governor-limits/SKILL.md) |
| `FIELD_CUSTOM_VALIDATION_EXCEPTION` | A validation rule blocked the DML | Check the rule and the data |
| `REQUIRED_FIELD_MISSING` / `FIELD_INTEGRITY_EXCEPTION` | Required field/integrity | Builder/service that assembles the record |
| `System.NullPointerException` | Null dereference | [generating-apex-service-class](../generating-apex-service-class/SKILL.md) / [building-apex-triggers](../building-apex-triggers/SKILL.md) (fix the guard) |
| `System.CalloutException` / timeout | External integration failed | Check endpoint/credential; usually transient |
| `INSUFFICIENT_ACCESS_OR_READONLY` | Permission/sharing | Profile/locked record |

## How to Report

1. **Header:** which org was queried and which period.
2. **Summary table** of the headers found.
3. For each failure: error detail (type, operation, affected record, summarized stack trace).
4. **Diagnosis:** likely root cause + transient vs recurring.
5. **Suggested next steps** (monitor / fix code via the right skill). Never apply the fix yourself.
6. **Reviewed flag:** mark every reviewed header and state how many were marked.

If there are no failure logs in the period, say so explicitly.

## Worked Example (reference)

Question: "take a look at today's logs".

1. Target org from the user's context.
2. The headers query returns 1 record: `LOG-00042` | Interface `Some Trigger` |
   `FailQuantity__c = 1` | Status `Fail` | user Jane Doe.
3. The items query for `LOG-00042` returns an item whose `FailDescription__c` is:
   ```
   Operation: AFTER_UPDATE | Records: 1
   Upsert failed. First exception on row 0 with id 006XXXXXXXXXXXXXXX;
   first error: UNABLE_TO_LOCK_ROW, unable to obtain exclusive access to this record: []
   Class.AbstractRepository.save: line 12, column 1
   Class.OpportunityRollupService.countChildContracts: line 37, column 1
   Class.CountChildContractsHandler.run: line 16, column 1
   Trigger.ContractTrigger: line 21, column 1
   ```
4. **Diagnosis:** `UNABLE_TO_LOCK_ROW` while saving the parent Opportunity in
   `OpportunityRollupService.countChildContracts` — lock contention from a
   concurrent edit. Transient; occurred once. Recommendation: monitor; if
   recurring, make the recalculation asynchronous.
5. **Marked reviewed:** `sf data update record ... --sobject Log__c --record-id <Id> --values "Reviewed__c=true"`.

## Gotchas

| Pitfall | Resolution |
|---------|------------|
| Filtering on the `Status__c` formula | It is derived; filter on `FailQuantity__c > 0` instead |
| Truncated stack traces in table output | Add `--json` so long `FailDescription__c` is not garbled |
| Re-reviewing logs every run | Default to `Reviewed__c = false`; only flip it to `true` |
| Querying without a period filter | Always bound by `CreatedDate`/`Date__c` (project rule: real `WHERE`) |
| Flipping other fields "while you're there" | Only ever set `Reviewed__c = true`; never touch anything else |
| Exposing sensitive payloads | Report only the IDs/messages the diagnosis needs |

## Constraints

- **Almost read-only:** the only allowed write is `sf data update record ... --sobject Log__c ... --values "Reviewed__c=true"`. Never set any other field; never run `sf data create/delete`, `sf apex run`, deploys, or anything that changes data/metadata.
- Only ever flip `Reviewed__c` to `true`, and only on headers actually reviewed this run.
- Every SOQL must have a `WHERE` — always filter by period and, by default, `Reviewed__c = false`.
- Do not expose sensitive data beyond what the diagnosis needs (IDs and error messages are fine).
