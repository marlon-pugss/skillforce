---
name: operating-sf-cli
description: "Plan and run Salesforce CLI operations safely: deployments, retrievals, Apex test runs, static analysis, and destructive changes — with evidence and explicit approval for mutating actions. TRIGGER when: user needs to run/plan sf CLI commands (deploy, retrieve, test, analyze). DO NOT TRIGGER when: validating one Apex change's tests (use validating-apex-changes) or reviewing CI workflows (use reviewing-github-actions)."
license: TBD
metadata:
  version: "1.0"
---

# operating-sf-cli: Safe SF CLI Operations

Use this skill to execute, validate, and plan **Salesforce CLI** operations with
safety-first discipline and zero tolerance for commands that silently hide
failures or mutate orgs without evidence.

## When This Skill Owns the Task

Use `operating-sf-cli` for deploys, retrieves, test runs, static analysis, and
destructive changes via the `sf` CLI.

Delegate elsewhere when the user is:
- producing validation evidence for a specific Apex change -> [validating-apex-changes](../validating-apex-changes/SKILL.md)
- reviewing CI/CD workflows -> [reviewing-github-actions](../reviewing-github-actions/SKILL.md)

## Required Context to Gather First

- the target org alias and whether it is a scratch/sandbox/production org
- the exact operation (deploy, retrieve, test, analyze, destructive)
- the narrowest scope that achieves it (specific files/manifest, not the whole repo)
- whether the action mutates the org (then approval + dry-run first)

## Step 0: Pre-Execution Checklist

- [ ] Project root confirmed — `force-app/main/default` exists.
- [ ] CLI help checked — run `--help` for the specific command family.
- [ ] Org alias supplied by the user or locally verified — never expose private usernames.
- [ ] Command does not include helper repo folders or unrelated source paths.
- [ ] Source/metadata/manifest scope is narrow and inspected before use.
- [ ] Test level and named tests are explicitly justified.
- [ ] Dry run or validation ran before a real deploy when possible.
- [ ] Code Analyzer ran, or the reason for skipping is documented.

## Safe Inspection & Validation Commands

| Command pattern | Use |
|---|---|
| `sf project deploy start --dry-run --source-dir force-app/main/default/classes/MyClass.cls --target-org <alias>` | Dry run for narrow source |
| `sf project deploy validate --source-dir force-app/main/default --target-org <alias> --test-level RunLocalTests` | Production-style validation |
| `sf project deploy report --job-id <id> --target-org <alias> --wait 30` | Poll deploy status |
| `sf project deploy quick --job-id <validated-job-id> --target-org <alias>` | Quick deploy after validation |
| `sf apex run test --target-org <alias> --test-level RunSpecifiedTests --tests MyClassTest --result-format human --wait 30` | Focused Apex tests |
| `sf project retrieve start --manifest manifest/package.xml --target-org <alias>` | Retrieve metadata |
| `sf code-analyzer run --target force-app/main/default --view table` | Static analysis |

## Test Level Guidance

| Test level | Use |
|---|---|
| `NoTestRun` | Development-org deploys when allowed |
| `RunSpecifiedTests` | Narrow validation with focused tests |
| `RunLocalTests` | Production default for Apex-containing deploys |
| `RunAllTestsInOrg` | Highest confidence or org policy requirement |

## Destructive Deployment Safety

Destructive commands require **explicit user approval** before execution:
1. State clearly this is a destructive operation.
2. Request explicit user approval.
3. Use `--post-destructive-changes` for the standard safer shape.
4. Do not use `--purge-on-delete` unless explicitly accepted.

## Failure-Hiding Flags — strict prohibition

Never use these without explicit approval and documented risk:
`--ignore-errors`, `--ignore-warnings`, `--ignore-conflicts`, `--purge-on-delete`.

## Mutating Commands Requiring Explicit Approval

| Command | Why |
|---|---|
| `sf project deploy start` (no `--dry-run`) | Mutates org metadata |
| `sf project deploy quick` | Mutates org metadata |
| `sf project retrieve start` | Overwrites source files |
| `sf apex run --file <file>` | Executes Apex in an org |
| `sf data import tree` | Inserts data |

## Gotchas

| Pitfall | Resolution |
|---------|------------|
| Acting on the wrong default org | Always pass `--target-org <alias>` explicitly |
| Deploying all of `force-app` for one file | Scope with `--source-dir` or a manifest |
| Forgetting `--wait` | Long ops return before completion; always wait or poll with `report` |
| `retrieve start` clobbering local edits | Review/stash local changes first; retrieve into a clean tree |
| Source-tracking conflicts | Inspect with `--dry-run`/status before forcing; never use `--ignore-conflicts` blindly |
| Treating validate as deployed | `validate` only validates; promote with `deploy quick` (with approval) |

## Output & Reporting Standards

After every operation, report:
1. **Command executed** (full, redact private usernames).
2. **Scope** (source, metadata types, or manifest).
3. **Test level and tests.**
4. **Result status**: dry-run pass | validation pass | quick deploy pass | real deploy pass | fail | skipped.
5. **Job ID** when available.
6. **Risks or anomalies.**
7. **Next recommended action.**
