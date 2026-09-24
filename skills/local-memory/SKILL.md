---
name: local-memory
description: "Project-local long-term memory for coding agents, stored as Markdown conversations and indexed with SQLite FTS5. TRIGGER when: starting any task that may depend on previous work, decisions, bugs, or preferences; and before ending every task to preserve the session. DO NOT TRIGGER when: the project explicitly forbids local conversation storage."
license: TBD
metadata:
  version: "1.0"
---

# local-memory: Project Conversation Memory

Use this skill to preserve context across agent sessions without an external service. Memory is private to the project under `.memory/`, while this skill and its example remain versioned.

## Privacy rules

- Never save credentials, access tokens, personal data, or confidential business data.
- Keep `.memory/` ignored by Git. Never commit or push it.
- Save only information needed to continue technical work.
- Follow project-specific retention and privacy requirements.

## Setup

Run commands from the project root. Locate this installed skill's directory and set the script path accordingly:

```bash
python3 <skill-directory>/scripts/memctl.py list
```

Add this entry to the project's `.gitignore` if it is not already present:

```gitignore
.memory/
```

The script creates `.memory/conversations/` and `.memory/index.db` on first save.

## Start of a task

Search before changing code when prior work may matter:

```bash
python3 <skill-directory>/scripts/memctl.py search "meaningful feature or bug terms"
python3 <skill-directory>/scripts/memctl.py show <id>
python3 <skill-directory>/scripts/memctl.py list
```

Try relevant synonyms if the first search returns no result. Treat retrieved memory as context, then verify it against the current codebase.

## End of every task

Write a temporary Markdown body, then save it:

```bash
python3 <skill-directory>/scripts/memctl.py save \
  --title "Short task title" \
  --source "agent-name" \
  --tags "feature,area" \
  --summary "What changed and the resulting state" \
  --outcome code \
  --file /tmp/session-summary.md
```

Valid outcomes are `code`, `decision`, `research`, and `blocked`.

Use this body structure:

```markdown
# Task title

## Context
What the user requested and the starting point.

## Work completed
Changes and important technical reasoning.

## Blockers or follow-ups
Remaining work, or `None`.

## Files changed
Paths and commits, if any.

## Conversation transcript
**User:** Original request.

**Agent:** Final response or a faithful condensed response if very long.

## Reusable facts
Decisions and discoveries useful in future sessions.
```

## Maintenance

The Markdown files are the source of truth. Rebuild a missing or stale SQLite index with:

```bash
python3 <skill-directory>/scripts/memctl.py reindex
```

See [the fictional conversation](examples/example-conversation.md) for a complete, safe example.
