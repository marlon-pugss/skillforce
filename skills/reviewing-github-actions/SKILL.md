---
name: reviewing-github-actions
description: "Design, write, and review GitHub Actions workflows for a Salesforce DX project (CI quality gates, deploy safety, secret hygiene). TRIGGER when: user works on .github/workflows/*.yml for an SFDX repo, or asks to review CI/CD pipelines. DO NOT TRIGGER when: running ad-hoc CLI commands locally (use operating-sf-cli) or validating a specific Apex change (use validating-apex-changes)."
license: TBD
metadata:
  version: "1.0"
---

# reviewing-github-actions: Salesforce DX CI/CD Review

Use this skill to design and review **GitHub Actions workflows** for Salesforce
DX projects — enforcing quality gates, safe deploys, and secret hygiene.

## When This Skill Owns the Task

Use `reviewing-github-actions` for `.github/workflows/*.yml` work in an SFDX repo.

Delegate elsewhere when the user is:
- running CLI operations locally -> [operating-sf-cli](../operating-sf-cli/SKILL.md)
- validating one Apex change -> [validating-apex-changes](../validating-apex-changes/SKILL.md)

## Required Context to Gather First

- the workflow trigger (pull_request, push, workflow_dispatch, schedule)
- the target org(s)/environment(s) and how they authenticate (auth URL vs JWT)
- whether the workflow validates only (dry-run) or actually deploys
- which quality gates are required (analyzer, prettier, tests, dry-run)

## Quality Gates to Enforce

- Markdown links: a Markdown link-checker action.
- Public safety: secret/path pattern scan.
- Code Analyzer: `sf code-analyzer run`.
- Apex formatting: `npm run prettier:check`.
- Deploy validation: `sf project deploy start --dry-run`.

## Security Non-Negotiables

- Never print secrets in workflow output.
- All secrets referenced via `${{ secrets.* }}`.
- Pin third-party actions to a specific commit SHA or verified tag.
- Mutating deploy workflows must be manual (`workflow_dispatch`) and environment-protected.

## Example Validation Job (PR gate)

```yaml
name: Validate
on: [pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<commit-sha>      # pin third-party actions to a SHA
      - uses: actions/setup-node@<commit-sha>
        with:
          node-version: '20'
      - run: npm ci
      - run: npm install --global @salesforce/cli
      - name: Authenticate (auth URL stored as a secret)
        run: echo "$SF_AUTH_URL" | sf org login sfdx-url --sfdx-url-stdin --alias ci
        env:
          SF_AUTH_URL: ${{ secrets.SF_AUTH_URL }}
      - run: sf project deploy start --dry-run --source-dir force-app --target-org ci --test-level RunLocalTests
      - run: sf code-analyzer run --target force-app --view table
```

## Gotchas

| Pitfall | Resolution |
|---------|------------|
| Floating tag (`@v3`) for a third-party action | Pin to a commit SHA (supply-chain safety) |
| Secret echoed to the log | Never `echo` a secret; pipe via stdin or pass via `env` |
| Auth URL committed in plaintext | Store as a repo/environment secret; log in via `sfdx-url` |
| Mutating deploy on every push | Gate real deploys behind `workflow_dispatch` + protected environment |
| Production deploy without a test level | Use `RunLocalTests` (or stricter) for prod-bound deploys |
| Errors swallowed with `|| true` | Let gates fail the job; do not mask failures |

## Review Checklist

- [ ] No secrets exposed in logs or echo statements.
- [ ] All third-party actions pinned to SHA or verified tag.
- [ ] Mutating deploys protected by `workflow_dispatch` and environment gates.
- [ ] All quality gates present: Code Analyzer, Prettier check, dry-run deploy.
- [ ] Production-bound deploys specify an appropriate test level.
- [ ] Failure modes handled — no silent swallowing of errors.
