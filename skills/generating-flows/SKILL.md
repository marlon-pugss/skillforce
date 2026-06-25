---
name: generating-flows
description: "Generate production-ready Salesforce Flow metadata (Screen, Autolaunched, Record-Triggered before/after-save, Scheduled) through a grounded MCP generation pipeline. TRIGGER when: user asks to create/build/generate a Flow, or uses flow language ('when a record is created', 'trigger daily at', 'automate', 'send an email when'). DO NOT TRIGGER when: writing Flow tests (use generating-flow-tests) or Apex automation (use generating-apex-service-class / building-apex-triggers)."
license: TBD
metadata:
  version: "1.0"
---

# generating-flows: Salesforce Flow Metadata Generator

Use this skill to generate Flow metadata through the grounded MCP pipeline. It
covers all Flow types: Screen, Autolaunched, Record-Triggered (before/after-save),
and Scheduled. Author Flow **tests** with
[generating-flow-tests](../generating-flow-tests/SKILL.md).

## Core Responsibility

Generate Flow metadata **exclusively** through the mandatory 3-step MCP pipeline:
1. `fetchGroundedObjectMetadata`
2. `flowElementSelection`
3. `flowElementGeneration` (loop until complete)

**Never hand-write or hand-edit Flow XML** — except when the user explicitly asks
you to fix validation/deployment errors in already-generated XML.

## Required Context to Gather First

- the Flow type (see the table below)
- the object and, for record-triggered, the timing (before-save vs after-save)
- the entry/trigger conditions and what the flow must do
- whether it calls Apex actions or subflows
- the custom objects/fields to ground via `inflightMetadata`

## Choosing the Flow Type

| Type | Use when |
|------|----------|
| Screen | the user interacts (wizard, guided input) |
| Record-Triggered (before-save) | fast field updates on the **same** record |
| Record-Triggered (after-save) | related records, emails, async actions |
| Autolaunched | invoked by Apex, another flow, or a process |
| Scheduled | run on a schedule over a batch of records |

## The 3-Step Pipeline (mandatory, no exceptions)

All three steps use a single MCP tool (e.g. `execute_metadata_action`); the
`action` parameter selects the step.

### Step 1 — `fetchGroundedObjectMetadata` (always first)
- `userPrompt` (STRING): the user's natural-language request for this flow.
- `inflightMetadata` (ARRAY): custom objects/fields from the local SFDX project; `[]` if none.
- Output: `groundingMetadata` — pass directly to Step 2.

### Step 2 — `flowElementSelection` (after Step 1)
- `userPrompt` (STRING): **exact same value** as Step 1.
- `groundingMetadata` (STRING): **exact string** from Step 1 — do not re-serialize.
- `operationId` (STRING): `""` for the first call.
- Output: `operationId` — pass to Step 3.

### Step 3 — `flowElementGeneration` (loop until complete)
- `operationId` (STRING): same value every iteration.
- Loop until `isComplete` is `true`. Never stop early.
- Extract XML from `result` only when `isComplete` is `true`.

## inflightMetadata Rules

- Data type: ARRAY (never string).
- Scan the local SFDX project for custom objects/fields relevant to the flow.
- Correct property names: `apiName` (not `name`), `type` (not `fieldType`), `referenceTo` (not `relatedTo`).

## Project Awareness

- Follow the org's existing custom field naming convention consistently (e.g. some
  orgs use `MyField__c` camelCase, others `My_Field__c`) — match what the target org uses.
- Use the org's picklist/status values; never invent values. Centralize shared
  values in a `Constants` class when generating companion Apex.
- For guard-before-DML behavior, ensure record-triggered flow entry conditions check
  for actual field changes (ISCHANGED/PRIORVALUE) instead of running every time.
- Always read the target object/flow metadata before generating.

## Multiple Flows: separate sequential pipelines

1. Split the request into individual single-flow descriptions.
2. Run a complete separate 3-step pipeline for each flow, sequentially.
3. Never combine multiple flows into one `userPrompt`.
4. Never run pipelines in parallel.

## XML Output Rules

- Do not modify, add, or remove nodes from the returned XML.
- Present the XML exactly as returned by the pipeline.
- Exception: targeted manual edits to fix explicit validation/deployment errors.

## Gotchas

| Pitfall | Resolution |
|---------|------------|
| Hand-editing the generated XML | Only allowed to fix an explicit deploy/validation error |
| Re-serializing `groundingMetadata` | Pass the **exact** Step 1 string into Step 2 |
| `inflightMetadata` sent as a string | It must be an ARRAY |
| Stopping Step 3 early | Loop until `isComplete` is `true` |
| Before-save flow doing DML on other objects | Use after-save for related-record changes |
| Record-triggered flow updating its own record without ISCHANGED | Add change conditions to avoid recursive re-fires |

## Pre-Flight Checklist

- [ ] Flow type chosen deliberately.
- [ ] All 3 steps called in strict order.
- [ ] `userPrompt` identical in Step 1 and Step 2.
- [ ] `inflightMetadata` is an ARRAY.
- [ ] `groundingMetadata` passed directly from Step 1 to Step 2.
- [ ] `operationId` from Step 2 used in all Step 3 calls.
- [ ] Step 3 looped until `isComplete` is `true`.
- [ ] XML returned unmodified.
