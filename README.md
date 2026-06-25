# skillforce

**Salesforce Apex & automation agent skills.** A community library focused on
enterprise Apex architecture, automation, and delivery: service/domain classes,
the repository pattern, trigger frameworks, integrated testing, batch jobs,
Flows, CI/CD review, and SF CLI operations.

Each skill is a self-contained directory following the open
[Agent Skills specification](https://agentskills.io/) and works with any AI tool
that supports skills (OpenCode, Claude Code, Codex, Cursor, and others).

## Structure

```
.
├── skills/
│   ├── generating-apex-service-class/
│   ├── generating-apex-repository/
│   ├── building-apex-triggers/
│   ├── generating-apex-integration-tests/
│   ├── orchestrating-apex-delivery/
│   ├── reviewing-apex-governor-limits/
│   ├── validating-apex-changes/
│   ├── generating-apex-batch/
│   ├── generating-flows/
│   ├── generating-flow-tests/
│   ├── reviewing-github-actions/
│   ├── operating-sf-cli/
│   ├── investigating-runtime-errors/
│   ├── managing-product-backlog/
│   └── orchestrating-salesforce-development/
└── README.md
```

## Usage

Install into any compatible AI coding tool via the open skills registry:

```bash
npx skills add marlon-pugss/skillforce
```

Or clone this repository and point your tool at the `skills/` directory.

## Skill catalog

| Skill | What it does |
|-------|--------------|
| `generating-apex-service-class` | Business-logic (service/domain) classes orchestrating repositories + builders |
| `generating-apex-repository` | Repository classes (AbstractRepository pattern, safe dynamic SOQL) |
| `building-apex-triggers` | Triggers + handlers on a TriggerDispatcher / TriggerAction framework |
| `generating-apex-integration-tests` | Integrated Apex tests (real DML, BDD naming) |
| `orchestrating-apex-delivery` | Coordinates a full multi-layer Apex feature across the skills above |
| `reviewing-apex-governor-limits` | Reviews Apex for governor-limit and resource-consumption risks |
| `validating-apex-changes` | Runs tests, dry-run deploys, and static analysis as validation evidence |
| `generating-apex-batch` | Batch Apex class + meta-xml + test from the repository pattern |
| `generating-flows` | Generates Flow metadata through a grounded MCP pipeline |
| `generating-flow-tests` | Authors `.flowtest-meta.xml` declarative Flow tests |
| `reviewing-github-actions` | Reviews GitHub Actions workflows for Salesforce DX CI/CD |
| `operating-sf-cli` | Plans and runs safe SF CLI operations (deploy, retrieve, test, analyze) |
| `investigating-runtime-errors` | Investigates runtime error logs captured in a custom logging object |
| `managing-product-backlog` | Writes, prioritizes, and scores product backlog items |
| `orchestrating-salesforce-development` | Routing guide: which skill to use for each kind of task |

## Conventions shared by these skills

- **Layered architecture:** Trigger -> Handler -> Service/Logic class.
- **No SOQL/DML in loops**; every query has a real `WHERE` clause (no full scans).
- **Repository pattern** for all persistence; **Builder pattern** for record assembly.
- **No hardcoded** picklist/status values — use a central `Constants` class.
- **Integrated tests** with real DML, `Assert.areEqual`, and BDD naming.

## License

License is **not yet decided** for this repository. Each skill currently carries
`license: TBD` in its front matter. Choose a license (for example MIT or
Apache-2.0), add a `LICENSE` file at the root, and update the `license` field in
every `SKILL.md` before publishing.

## Contributing & feedback

Open an issue or a pull request with suggested changes.
