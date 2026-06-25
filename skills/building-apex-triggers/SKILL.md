---
name: building-apex-triggers
description: "Create and edit Apex Triggers and Trigger Handlers on a TriggerDispatcher / TriggerAction framework, keeping triggers logic-free and handlers thin. TRIGGER when: user creates/edits a *.trigger, a *Handler class, or wires handler execution order. DO NOT TRIGGER when: writing the business rule itself (use generating-apex-service-class), tests (use generating-apex-integration-tests), or batch jobs (use generating-apex-batch)."
license: TBD
metadata:
  version: "1.0"
---

# building-apex-triggers: Trigger & Handler Framework

Use this skill to create and change **triggers and handlers** using a
`TriggerDispatcher` + `TriggerAction` framework. Triggers stay logic-free;
handlers delegate to a service/logic class.

## When This Skill Owns the Task

Use `building-apex-triggers` when the work involves:
- a `<Object>Trigger` that registers actions in a dispatcher
- a `<Name>Handler` that extends `TriggerAction`
- ordering handlers within `addAction`

Delegate elsewhere when the user is:
- implementing the business rule the handler calls -> [generating-apex-service-class](../generating-apex-service-class/SKILL.md)
- writing tests for the trigger path -> [generating-apex-integration-tests](../generating-apex-integration-tests/SKILL.md)

## Required Context to Gather First

Ask for or infer before writing code:
- the SObject and which DML events fire the logic (insert/update/delete; before/after)
- whether the work belongs in **before-save** (mutate the record in place) or **after-save** (related DML)
- which service/logic class each handler delegates to
- the required order relative to existing handlers on the same object

## Strict Rules

1. **Triggers contain no business rules.**
2. **Triggers** register actions in the `TriggerDispatcher`.
3. **Handlers** always extend `TriggerAction`.
4. **Handlers** implement `getAllowedOperations()`.
5. **Handlers** delegate to a logic class (service/class).
6. No inline logic in the `run()` method.
7. **One trigger per object** — all logic flows through its dispatcher.

## Trigger Example (`ContractTrigger.trigger`)

The trigger only wires actions and runs the dispatcher — zero logic.

```apex
trigger ContractTrigger on Contract (after insert, after update) {
    TriggerDispatcher dispatcher = new TriggerDispatcher();
    dispatcher.addAction(new FillContractFieldsHandler());   // fill/rollup first
    dispatcher.addAction(new CountChildContractsHandler());  // consumers after
    dispatcher.run();
}
```

## Handler Pattern

```apex
public class CountChildContractsHandler extends TriggerAction {
    private OpportunityRollupService rollupService;

    public CountChildContractsHandler() {
        rollupService = new OpportunityRollupService();
    }

    override public Set<TriggerOperation> getAllowedOperations() {
        return new Set<TriggerOperation> {
            TriggerOperation.AFTER_INSERT,
            TriggerOperation.AFTER_UPDATE
        };
    }

    override public void run() {
        rollupService.countChildContracts(context.newRecords);
    }
}
```

## Order of Handlers in `addAction`

- Fill/rollup handlers (`Fill*` / `*Rollup*`) come before handlers that read those fields.
- Field-filling handlers generally come before `Update*Status` handlers.

## Gotchas

| Pitfall | Resolution |
|---------|------------|
| Re-entrant recursion (a `save` re-fires the trigger) | Guard with a static flag or change detection; keep handlers idempotent |
| `context.oldRecordsMap` is `null` on insert | Only read old values on update/delete |
| Record Ids missing in `before insert` | Use `after insert` when you need the new record Id |
| Setting fields in after-save without DML | Before-save: mutate in place. After-save: build + update via the service/repository |
| Multiple triggers on one object | Consolidate into a single trigger + dispatcher (execution order is otherwise undefined) |
| Logic creeping into the trigger body | Move it to a handler -> service; the trigger only wires actions |

## Delivery Checklist

- [ ] Trigger only registers actions in the dispatcher — zero logic.
- [ ] One trigger per object.
- [ ] Handler extends `TriggerAction` and implements `getAllowedOperations()`.
- [ ] Handler delegates to a service/logic class — no inline business logic.
- [ ] Fill/rollup handlers ordered before handlers that consume their output.
- [ ] Recursion guarded where a handler triggers further DML on the same object.
- [ ] `.cls-meta.xml` and `.trigger-meta.xml` created for new files.
