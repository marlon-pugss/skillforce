---
title: Add retry settings to the weather client
source: coding-agent
tags: weather-client,retries,configuration
summary: Added configurable retry attempts to the fictional weather client and covered the default behavior with tests.
outcome: code
created_at: 2026-01-15T14:30:00+00:00
---

# Add retry settings to the weather client

## Context
The user asked for configurable retries in a fictional command-line weather application. The client already retried twice with a hardcoded value.

## Work completed
Added a `retry_attempts` setting with a default of two, passed it into the HTTP client, and added tests for default and custom values. The existing timeout behavior was unchanged.

## Blockers or follow-ups
None.

## Files changed
- `src/weather/config.py`
- `src/weather/client.py`
- `tests/test_client.py`

## Conversation transcript
**User:** Make the number of weather API retries configurable, but preserve the current default.

**Agent:** Implemented `retry_attempts` with a default of two and added tests for default and custom configurations. All tests pass.

## Reusable facts
The weather client receives configuration through its constructor. Retry values must be non-negative integers.
