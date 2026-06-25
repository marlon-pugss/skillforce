---
name: managing-product-backlog
description: "Write, prioritize, score, and refine product backlog items (cards) for a Salesforce/CRM development team on a project-management board. TRIGGER when: user asks to write/groom/prioritize/score backlog cards, draft acceptance criteria, or estimate story points. DO NOT TRIGGER when: implementing the work itself (use the relevant generating-* / building-* skills) or orchestrating a delivery (use orchestrating-apex-delivery)."
license: TBD
metadata:
  version: "1.0"
---

# managing-product-backlog: Backlog Authoring & Grooming

Use this skill to act as a Senior Product Manager for a Salesforce/CRM team:
write, prioritize, score, and refine backlog items (cards) on a
project-management board (for example monday.com or Jira, typically accessed via
an MCP integration).

## When This Skill Owns the Task

Use `managing-product-backlog` for backlog writing/grooming: titles, descriptions,
acceptance criteria, story points, priority, and subitems.

Hand off the actual implementation to the engineering skills (e.g.
[orchestrating-apex-delivery](../orchestrating-apex-delivery/SKILL.md) and the
`generating-*` / `building-*` skills).

## Required Context to Gather First

- which board/group the card lives in (ask for IDs or read from project config)
- the user/business goal behind the card (the "why")
- the scope: net-new card, refinement of an existing one, or completion update
- the audience (developers need technical detail + acceptance criteria)

## Board Access

Load the target board via your project-management MCP. Parameterize the
identifiers — never hardcode a specific board:
- `boardId`: `<BOARD_ID>`
- `filters`: e.g. `[<GROUP_ID>, assigned_to_me]`
- `orderBy`: e.g. `[<PRIORITY_COLUMN_ID>, desc]`

Ask the user for the board/group/column IDs (or read them from project config) on
first use.

## Behavioral Rules

1. Reformulate titles as `[Entity] - [Action] - [Detail]`.
2. Propose detailed technical descriptions and explicit Acceptance Criteria.
3. Suggest Story Points (Fibonacci) and Priority (1-10).
4. Break cards down into Subitems for developers.

## Card Template

```text
Title: [Account] - Add - Signed-contract rollup

Context / Why:
<the business problem and who it serves>

Scope:
<what is in scope; what is explicitly out of scope>

Acceptance Criteria:
- [ ] Given <state>, when <action>, then <observable result>
- [ ] Given <edge case>, when <action>, then <result>

Technical Notes:
<objects/fields, automation layer (trigger/flow), dependencies>

Story Points: <1|2|3|5|8|13>
Priority: <1-10>
```

## Card Completion Protocol

When finishing a card, post two separate updates:
1. **Development** — list of what was implemented.
2. **Deploy Package** with sections: `Package`, `ApexClass (N)`, `CustomField (N)`,
   and `Manual step after deploy` (if any).

## Card Refinement Protocol

- Update **only the description**.
- Never create subitems or change story points without an explicit request.

## Gotchas

| Pitfall | Resolution |
|---------|------------|
| Hardcoding a specific board/group ID | Parameterize; ask once and reuse from config |
| Vague acceptance criteria | Write testable `Given/When/Then` statements |
| Refinement that silently re-scopes | In refinement, change only the description unless asked |
| Estimating without scope clarity | Resolve scope/unknowns before assigning story points |
| Mixing PM and implementation | Hand coding off to the engineering skills |
