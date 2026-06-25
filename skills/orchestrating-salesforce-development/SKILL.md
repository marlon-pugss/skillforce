---
name: orchestrating-salesforce-development
description: "Routing and sequencing guide for Salesforce development work: decides which specialist skill to use for each request and the recommended validation sequence. TRIGGER when: user has a broad/ambiguous Salesforce task and you need to pick the right skill(s), or wants the end-to-end workflow. DO NOT TRIGGER when: the right skill is already obvious — go straight to it."
license: TBD
metadata:
  version: "1.0"
---

# orchestrating-salesforce-development: Skill Routing Guide

Use this skill as the tactical guide for **which specialist skill to use** for
each kind of Salesforce request, plus the recommended sequencing and a shared
Definition of Done.

## Skill Referral Guide

| If the user wants to... | Use skill |
| :--- | :--- |
| Create/edit business logic (service / fill-fields / rollup) | [generating-apex-service-class](../generating-apex-service-class/SKILL.md) |
| Create/refactor Repository classes | [generating-apex-repository](../generating-apex-repository/SKILL.md) |
| Create/edit Triggers or Handlers | [building-apex-triggers](../building-apex-triggers/SKILL.md) |
| Create/fix integrated tests (BDD) | [generating-apex-integration-tests](../generating-apex-integration-tests/SKILL.md) |
| Build a complete multi-layer feature | [orchestrating-apex-delivery](../orchestrating-apex-delivery/SKILL.md) |
| Review governor limits / performance | [reviewing-apex-governor-limits](../reviewing-apex-governor-limits/SKILL.md) |
| Validate code (tests, dry-run, static analysis) | [validating-apex-changes](../validating-apex-changes/SKILL.md) |
| Create a Batch class from scratch | [generating-apex-batch](../generating-apex-batch/SKILL.md) |
| Create/generate Salesforce Flows | [generating-flows](../generating-flows/SKILL.md) |
| Write Flow test metadata (`.flowtest-meta.xml`) | [generating-flow-tests](../generating-flow-tests/SKILL.md) |
| Create/review GitHub Actions for SFDX | [reviewing-github-actions](../reviewing-github-actions/SKILL.md) |
| Run manual SF CLI commands | [operating-sf-cli](../operating-sf-cli/SKILL.md) |
| Investigate runtime error logs | [investigating-runtime-errors](../investigating-runtime-errors/SKILL.md) |
| Manage/prioritize backlog cards | [managing-product-backlog](../managing-product-backlog/SKILL.md) |

## Recommended Flows

### 1. Feature Development Cycle
1. **Requirements:** [managing-product-backlog](../managing-product-backlog/SKILL.md) to detail the card.
2. **Logic:** [generating-apex-service-class](../generating-apex-service-class/SKILL.md).
3. **Trigger:** [building-apex-triggers](../building-apex-triggers/SKILL.md).
4. **Test:** [generating-apex-integration-tests](../generating-apex-integration-tests/SKILL.md).
5. **Validation:** [validating-apex-changes](../validating-apex-changes/SKILL.md).

### 2. Bug Fix Cycle
1. **Research:** [investigating-runtime-errors](../investigating-runtime-errors/SKILL.md), plus grep/read to trace it.
2. **Fix:** the skill of the affected layer ([generating-apex-service-class](../generating-apex-service-class/SKILL.md) or [building-apex-triggers](../building-apex-triggers/SKILL.md)).
3. **Review:** [reviewing-apex-governor-limits](../reviewing-apex-governor-limits/SKILL.md) if the fix touches a loop.
4. **Validate:** [validating-apex-changes](../validating-apex-changes/SKILL.md) running the failing test specifically.

### 3. Code Review Cycle
1. **Static + tests:** [validating-apex-changes](../validating-apex-changes/SKILL.md).
2. **Limits:** [reviewing-apex-governor-limits](../reviewing-apex-governor-limits/SKILL.md).
3. **Patterns:** [generating-apex-repository](../generating-apex-repository/SKILL.md) if it is a repository.

### 4. Full Feature (single delivery)
Use [orchestrating-apex-delivery](../orchestrating-apex-delivery/SKILL.md) — it coordinates all layers.

## Routing Gotchas

| Ambiguous request | How to route |
|-------------------|--------------|
| "Automate when a record changes" | Decide declarative vs programmatic: [generating-flows](../generating-flows/SKILL.md) or [building-apex-triggers](../building-apex-triggers/SKILL.md) |
| "Fix this error in production" | Start with [investigating-runtime-errors](../investigating-runtime-errors/SKILL.md), then the affected layer |
| "It's slow / hit a limit" | [reviewing-apex-governor-limits](../reviewing-apex-governor-limits/SKILL.md) |
| "Write a test" | Apex -> [generating-apex-integration-tests](../generating-apex-integration-tests/SKILL.md); Flow -> [generating-flow-tests](../generating-flow-tests/SKILL.md) |
| Single layer vs whole feature | One layer -> that skill; trigger+logic+test together -> [orchestrating-apex-delivery](../orchestrating-apex-delivery/SKILL.md) |

## Definition of Done

- [ ] Layered architecture respected: Trigger -> Handler -> Logic Class.
- [ ] Every new `.cls` file has its `.cls-meta.xml`.
- [ ] Tests use real DML, `Assert.areEqual`, and BDD naming.
- [ ] No SOQL/DML inside loops; every query has a real `WHERE`.
- [ ] Validation-bypass flag set for any guarded status change in tests.
- [ ] Validation run and returned PASS.
