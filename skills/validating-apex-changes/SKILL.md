---
name: validating-apex-changes
description: "Run the correct validation commands after Apex changes (focused test runs, dry-run deploys, static analysis) and report results with command output as evidence. TRIGGER when: user asks to validate/verify Apex changes, run specific tests, or produce deploy evidence. DO NOT TRIGGER when: writing the code (use generating-apex-* skills) or planning broader CLI operations/deployments (use operating-sf-cli)."
license: TBD
metadata:
  version: "1.0"
---

# validating-apex-changes: Validation Evidence for Apex Work

Use this skill to execute the right validation commands after Apex changes,
interpret the results, and report **evidence** (real command output). It proves
work is correct; it does not write the code.

## When This Skill Owns the Task

Use `validating-apex-changes` when the user needs proof that changes pass:
focused test runs, a dry-run deploy, and static analysis.

Delegate elsewhere when the user is:
- writing/fixing the code -> [generating-apex-service-class](../generating-apex-service-class/SKILL.md)
  or [generating-apex-integration-tests](../generating-apex-integration-tests/SKILL.md)
- planning a real (mutating) deploy or broader CLI work -> [operating-sf-cli](../operating-sf-cli/SKILL.md)
- diagnosing a runtime failure already in the logs -> [investigating-runtime-errors](../investigating-runtime-errors/SKILL.md)

## Required Context to Gather First

- the org alias to validate against (never expose private usernames)
- which classes changed and their corresponding test classes
- whether a deploy dry-run is needed or just a focused test run
- the narrowest scope that still proves the change

## Validation Commands

- `sf apex run test --tests <TestClass> --target-org <alias> --result-format human --wait 10`
- `sf project deploy start --dry-run --source-dir force-app/main/default/classes --target-org <alias>`
- `sf code-analyzer run --target force-app/main/default --view table`

## Execution Workflow

1. Identify the change type (new class, test, trigger, handler, etc.).
2. Resolve the org alias from user context or locally authenticated orgs.
3. Resolve the test class names from the changed files.
4. Run sequentially: Tests -> Deploy Dry Run -> Static Analysis.
5. Report structured results with PASS/FAIL per gate.

## Absolute Rules

- Never claim success without showing command output.
- Never run broad deploys when a narrow scope is enough.
- Never fabricate or infer command output.
- If a gate is skipped, document why — skipped is not a pass.

## Interpreting Common Failures

| Symptom in output | Likely cause | Next step |
|---|---|---|
| `Class.X: line N ... System.AssertException` | Assertion mismatch | Fix the test expectation or the production bug it exposes |
| `CANNOT_EXECUTE_FLOW_TRIGGER` | Missing required field for an active Flow | Add a guard / required field (see generating-apex-integration-tests) |
| `Too many SOQL queries: 101` | SOQL in a loop | Route to [reviewing-apex-governor-limits](../reviewing-apex-governor-limits/SKILL.md) |
| `Code coverage ... is N%` below threshold | Insufficient coverage | Add tests via [generating-apex-integration-tests](../generating-apex-integration-tests/SKILL.md) |
| `Required field ... missing` on dry-run | Metadata/field not deployed | Include the dependency in scope |

## Gotchas

| Pitfall | Resolution |
|---------|------------|
| Running all org tests for one change | Use `--tests <TestClass>` to stay focused and fast |
| Forgetting `--wait` | Without it the command returns before results — always wait |
| Treating a dry-run as a deploy | `--dry-run` validates only; a real deploy needs explicit approval (operating-sf-cli) |
| Reporting PASS without output | Always paste the key output lines as evidence |

## Evidence Format (per command)

1. **Command executed** (full, with all flags).
2. **Scope** (which files/classes).
3. **Result status**: PASS | FAIL | SKIPPED (with reason).
4. **Output excerpt** (key lines from the command output).
5. **Next recommended action.**
