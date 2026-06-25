---
name: generating-flow-tests
description: "Create, validate, and modify Salesforce Flow test metadata (.flowtest-meta.xml) using the FlowTest metadata API. TRIGGER when: user asks to write automated tests for a Flow or touches *.flowtest-meta.xml files. DO NOT TRIGGER when: generating the Flow itself (use generating-flows) or writing Apex tests (use generating-apex-integration-tests)."
license: TBD
metadata:
  version: "1.0"
---

# generating-flow-tests: Declarative Flow Tests

Use this skill to create and maintain declarative automated tests for Salesforce
Flows using the `FlowTest` metadata API. Generate the Flow itself with
[generating-flows](../generating-flows/SKILL.md).

## When This Skill Owns the Task

Use `generating-flow-tests` for `.flowtest-meta.xml` work: authoring scenarios,
input records, and post-run assertions for an existing Flow.

## Required Context to Gather First

- the `flowApiName` of the Flow under test (and read its `.flow-meta.xml` first)
- the entry criteria, decisions, and assignments the Flow performs
- the happy path **and** at least one alternate/exception path
- the expected end-state to assert (which `$Record` field, which value)

## Technical Guidelines

### File location and naming
- Save files in `force-app/main/default/flowtests/` with the suffix `<testName>.flowtest-meta.xml`.

### Required fields
- `flowApiName`: API name of the Flow under test (e.g. `Account_Process_Flow`).
- `label`: friendly display label for the test.
- `testType`: `WithAssertion` for tests that validate conditions.

### testPoints rules
- Order matters — Salesforce executes them in the exact order they appear.
- `elementApiName` accepts only `Start` or `Finish`.
- At `Start`: configure input values before the flow runs.
  - For `InputTriggeringRecordInitial` / `InputTriggeringRecordUpdated`: `leftValueReference`
    **must** be `$Record`; provide the value as JSON in `<sobjectValue>`.
  - For `ScheduledPath`: `leftValueReference` **must** be `ScheduledPathApiName`.
- At `Finish` (`assertions`): conditions validated after execution, each with an `errorMessage`.

### Valid condition operators
`EqualTo`, `NotEqualTo`, `GreaterThan`, `LessThan`, `Contains`, `StartsWith`,
`EndsWith`, `IsNull`, `IsBlank`, `WasVisited`.

### Value tag by data type
| Field/value type | XML tag |
|---|---|
| Text / String | `<stringValue>` |
| Number / Decimal / Currency | `<numberValue>` |
| Checkbox / Boolean | `<booleanValue>` |
| Date | `<dateValue>` |
| Date/Time | `<dateTimeValue>` |
| Whole input record | `<sobjectValue>` (JSON) |

## Reference Template

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowTest xmlns="http://soap.sforce.com/2006/04/metadata">
    <flowApiName>Account_Process_Flow</flowApiName>
    <label>Verify Industry Update</label>
    <testPoints>
        <elementApiName>Start</elementApiName>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordInitial</type>
            <value>
                <sobjectValue>{"Name":"Test Account","AnnualRevenue":100000}</sobjectValue>
            </value>
        </parameters>
    </testPoints>
    <testPoints>
        <elementApiName>Finish</elementApiName>
        <assertions>
            <conditions>
                <leftValueReference>$Record.Industry</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>Other</stringValue>
                </rightValue>
            </conditions>
            <errorMessage>Industry was not set to 'Other' as expected by the flow.</errorMessage>
        </assertions>
    </testPoints>
    <testType>WithAssertion</testType>
</FlowTest>
```

## Workflow

1. **Analyze the Flow:** read the `.flow-meta.xml` to understand entry criteria, variables, decisions, and assignments.
2. **Design scenarios:** identify happy paths and exception paths; design realistic input data as JSON for `<sobjectValue>`.
3. **Generate the XML:** follow the template exactly; map each data type tag correctly.

## Constraints

- Never invent XML tags outside the official specification.
- Lookup fields cannot be used as `isolatedObjectExternalKeys` — warn the user if asked.
- Field and object API names in the `$Record` JSON must match the Flow metadata exactly.

## Gotchas

| Pitfall | Resolution |
|---------|------------|
| Wrong value tag for the field type | Match the data type (see the value-tag table) |
| `testPoints` in the wrong order | Salesforce runs them in document order; `Start` before `Finish` |
| `elementApiName` other than Start/Finish | Only `Start` and `Finish` are valid |
| `leftValueReference` wrong for a record input | Must be `$Record` |
| API names that do not match the Flow | Field/object names must match the Flow metadata exactly |
| No alternate path tested | Add at least one exception/negative scenario |

## Project Awareness

- Match the org's custom field naming convention when building `$Record` JSON.
- Use only picklist/status values that exist in the target org.
- Always read the target Flow file before writing any test.
