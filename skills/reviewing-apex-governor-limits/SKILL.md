---
name: reviewing-apex-governor-limits
description: "Review newly written or changed Apex for Salesforce governor-limit violations and resource-consumption risks (SOQL/DML in loops, CPU, heap, callouts, async). TRIGGER when: user asks to review Apex for limits/performance, or right after Apex is written/modified. DO NOT TRIGGER when: generating the code (use generating-apex-service-class), running tests (use validating-apex-changes), or diagnosing runtime logs (use investigating-runtime-errors)."
license: TBD
metadata:
  version: "1.0"
---

# reviewing-apex-governor-limits: Governor Limit & Resource Review

Use this skill to review **recently written or modified Apex** for real or
potential governor-limit violations and resource-consumption risks. By default
review only the diff / mentioned files, not the whole repository, unless asked.

## When This Skill Owns the Task

Use `reviewing-apex-governor-limits` right after code is written, or when the
user asks for a limits/performance review. If it is unclear which code to review,
ask before proceeding.

Delegate elsewhere when the user is:
- generating or fixing the code itself -> [generating-apex-service-class](../generating-apex-service-class/SKILL.md)
- running tests / coverage -> [validating-apex-changes](../validating-apex-changes/SKILL.md)
- diagnosing a runtime error from logs -> [investigating-runtime-errors](../investigating-runtime-errors/SKILL.md)

## Required Context to Gather First

- exactly which files/diff to review (default: only the changed code)
- the execution context (trigger, batch, queueable, schedulable, sync controller)
- expected data volume (single record vs bulk / batch scope size)
- whether the code is sync or async (limits differ — see below)

## Governor Limits (per synchronous transaction)

- **SOQL queries:** max 100 (sync) / 200 (async). Never inside loops. Every query needs a real `WHERE`.
- **Rows returned by SOQL:** max 50,000 per transaction.
- **DML statements:** max 150. Never `insert`/`update`/`delete`/`upsert` inside loops — bulkify via collections.
- **Records processed by DML:** max 10,000 per transaction.
- **SOSL queries:** max 20; rows per SOSL: 2,000.
- **CPU time:** 10,000 ms (sync) / 60,000 ms (async). Watch nested loops, repeated sorting, O(n^2) work.
- **Heap size:** 6 MB (sync) / 12 MB (async). Watch queries loading many fields/records.
- **HTTP callouts:** max 100 per transaction; cumulative timeout 120 s. No callouts in loops, none after uncommitted DML.
- **Async:** max 50 `@future`; Queueable chain depth; max 5 concurrent batches.

## Risk Patterns to Hunt

1. **SOQL in a loop** — the most common and serious error.
2. **DML in a loop** — accumulate in `List<SObject>`, run a single DML after the loop.
3. **Lack of bulkification** — code assuming a single record in a trigger/batch context.
4. **Queries without `WHERE`** — full scan.
5. **Nested loops over large collections** — CPU risk.
6. **Callouts in a loop or after DML.**
7. **Uncontrolled trigger recursion.**
8. **`@future`/Queueable/Batch triggered inside loops.**
9. **Excessive heap loading.**
10. **Missing guard before DML** — processing records that did not change.

## Review Methodology

1. Read the target code; identify all SOQL, DML, callouts, loops, and async calls.
2. Classify each finding by severity: **Critical**, **High**, **Medium**, **Info**.
3. Present findings one at a time — never a single undifferentiated list.
4. For each finding, give the concrete fix direction (bulkify, add `WHERE`, move out of loop, etc.).

## Output Format (per finding)

```text
Finding: <one-line summary>
Location: <class / method / line>
Severity: Critical | High | Medium | Info
Risk: <which limit it threatens and under what data volume>
Fix: <specific, bulk-safe action>
```

## Worked Example

```text
Finding: SOQL inside a for-loop over trigger records
Location: ContractService.recalculate, line 42
Severity: Critical
Risk: 1 query per record -> exceeds 100 SOQL in bulk updates (>100 contracts)
Fix: Query once before the loop filtered by the collected parent Ids, group the
     results into a Map, then read from the Map inside the loop.
```

## Severity Guide

| Severity | Meaning |
|---|---|
| Critical | Will hit a hard limit in realistic bulk volumes |
| High | Likely to fail at scale or under concurrency |
| Medium | Inefficient; risky as data grows |
| Info | Style/optimization opportunity, no immediate limit risk |
