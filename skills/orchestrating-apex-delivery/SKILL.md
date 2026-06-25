---
name: orchestrating-apex-delivery
description: "Coordinate a complete multi-layer Apex feature (service logic + trigger/handler + integrated test) in a single delivery, delegating each layer to the right skill. TRIGGER when: user asks for a full feature spanning trigger -> handler -> logic -> test together. DO NOT TRIGGER when: the request touches a single layer — go straight to that layer's skill."
license: TBD
metadata:
  version: "1.0"
---

# orchestrating-apex-delivery: Multi-Layer Apex Feature Orchestrator

Use this skill to coordinate Apex deliveries that span **multiple layers**
(service/logic class + trigger/handler + integrated test). It decides the
sequence, reads the existing code for conventions, and delegates each layer to
the matching specialist skill.

## When This Skill Owns the Task

Use `orchestrating-apex-delivery` when the user wants an end-to-end feature:
business rule + trigger wiring + test, delivered together.

If the request only touches one layer, skip orchestration and use that layer
directly.

## Required Context to Gather First

Before delegating anything, establish:
- the business requirement in one sentence (what must happen and when)
- the SObject(s) and the trigger events involved (insert/update/delete)
- whether a new Repository finder or Builder setter is needed
- existing conventions in the codebase (read a comparable feature first)
- the acceptance criteria the integrated test must prove

## Execution Sequence

1. **Study the codebase:** read real examples of each layer (trigger, handler,
   service, test) and mirror existing conventions.
2. **Logic class:** delegate to [generating-apex-service-class](../generating-apex-service-class/SKILL.md).
3. **Repository (if a finder/aggregate is missing):** delegate to
   [generating-apex-repository](../generating-apex-repository/SKILL.md).
4. **Handler + trigger registration:** delegate to [building-apex-triggers](../building-apex-triggers/SKILL.md).
5. **Integrated test:** delegate to [generating-apex-integration-tests](../generating-apex-integration-tests/SKILL.md).
6. **Validate the delivery:** delegate to [validating-apex-changes](../validating-apex-changes/SKILL.md)
   and confirm meta-xml, layer separation, and the principles below.

## Cross-Skill Integration

| Need | Delegate to |
|------|-------------|
| Business rule / rollup logic | [generating-apex-service-class](../generating-apex-service-class/SKILL.md) |
| Missing finder / aggregate | [generating-apex-repository](../generating-apex-repository/SKILL.md) |
| Trigger + handler wiring | [building-apex-triggers](../building-apex-triggers/SKILL.md) |
| Integrated coverage | [generating-apex-integration-tests](../generating-apex-integration-tests/SKILL.md) |
| Limits / performance review | [reviewing-apex-governor-limits](../reviewing-apex-governor-limits/SKILL.md) |
| Validation evidence | [validating-apex-changes](../validating-apex-changes/SKILL.md) |

## Non-negotiable Principles

- Strict layering: Trigger -> Handler -> Logic Class.
- No SOQL/DML outside a Repository.
- No hardcoding — use a central `Constants` class.
- Builder for all record assembly/updates.
- Guard clauses before any DML.
- Every new `.cls` file needs a `.cls-meta.xml`.

## Gotchas

| Pitfall | Resolution |
|---------|------------|
| Writing all layers inline yourself | Delegate each layer to its specialist skill; you only sequence and integrate |
| Skipping the codebase study | Read a comparable existing feature first so conventions match |
| Inventing a Repository finder/Builder setter | If missing, route to the repository skill instead of inlining SOQL |
| Wrong handler order | Fill/rollup before consumers (see building-apex-triggers) |
| Declaring "done" without validation | Always finish with validating-apex-changes evidence |

## Delivery Checklist

- [ ] Each layer produced by its specialist skill.
- [ ] Layer separation respected (no logic in triggers/handlers).
- [ ] Repository + Builder used; no inline SOQL/DML.
- [ ] Integrated test covers the full path (happy + edge).
- [ ] Validation run and reported.
