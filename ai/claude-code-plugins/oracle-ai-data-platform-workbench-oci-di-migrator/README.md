# oci-di-aidp-migrator

Oracle Cloud Infrastructure Data Integration (OCI-DI) → Oracle AI Data Platform (AIDP) migrator plugin.

Sixth entry in the AIDP migrator family (DBX / Snowflake / Informatica / Fabric / AWS / **OCI-DI**).
Same grammar as the other five: **inventory → plan → migrate → verify**.

## Status

- 2026-10-10 — scaffolded.
- Inventory module (OCI-DI workspaces/projects/data-flows/pipelines) first; translation + migrate stubs behind it.

## Scope (pilot)

Target: one representative OCI-DI pipeline → equivalent AIDP job + PySpark notebooks.

Covers:
- **Workspaces, projects, folders** — discovery
- **Data flows** — operator-by-operator translation to PySpark (source, filter, join, lookup, aggregate, pivot, union, split, SQL op, target)
- **Pipelines** — orchestration → AIDP job graph
- **Data assets** — OCI DB (ADB/ADW/ATP), Object Storage, Autonomous JSON, Oracle on-prem → AIDP connectors
- **Expressions** — DI expression language → Spark expressions (deterministic translation table)

Out of scope (pilot):
- Scheduling task triggers (map to AIDP job cron separately)
- Delta Live Tables-style streaming data flows
- Custom OCI Functions in pipelines (flagged, not translated)

## Directory layout (mirrors aws-aidp-migrator)

    oci_di_aidp/
      oci_di_client/     — OCI Data Integration SDK wrapper
      aidp_client/       — AIDP REST / CLI wrapper (shared pattern)
      inventory/         — one module per DI resource type
      plan/              — translation plan + risk flags
      translate/         — operator → PySpark, expression → Spark
      migrate/           — notebook / job writers
      verify/            — dry-run + verify
      state/             — manifests, caches
      fixtures/          — demo DI payload fixtures
      run/               — top-level orchestration
      cli.py             — `oci-di-aidp` entrypoint
      mcp_server.py      — MCP server exposure (for Claude Code / Codex integration)

    commands/            — Claude Code slash command markdown
    skills/              — plugin skill package
    docs/                — architecture + customer-facing notes
    scripts/             — one-shot utilities
    tests/               — unit + fixture-driven integration

## Install (dev)

    pip install -e .                            # core (CLI + inventory + translate)
    pip install -e ".[mcp]"                     # + MCP server (requires Python 3.10+)
    pip install -e ".[llm]"                     # + optional LLM narrative dep
    oci-di-aidp --help

## Offline / demo mode

No OCI auth needed — bundled fixture:

    oci-di-aidp inventory --fixture demo

## Deterministic-first guarantee

The core migration path (inventory → plan → translate → migrate → verify) makes
**zero LLM calls**. All translation is deterministic Python + sqlglot rewrites.
Any construct that can't be safely rewritten is **flagged with a named reason**,
never silently guessed.

The `[llm]` optional extra enables LLM-powered **narrative generation** on
flagged items only, behind an env-var gate — useful for reviewer context, not
required for migration. CSS / corporate Codex deployments do not need any
Claude or OpenAI key for the migration itself.

## Related plugins

    oracle-ai-data-platform-workbench-aws-migrator          — Mounika Potnuru
    oracle-ai-data-platform-workbench-databricks-migrator   — Nishant Patel
    oracle-ai-data-platform-workbench-fabric-migrator       — Mohammad Aitelkadi
    oracle-ai-data-platform-workbench-informatica-migrator  — Veera Raghavendra Koka
    oracle-ai-data-platform-workbench-snowflake-migrator    — Lucas de Almeida Reis, Navid Heydari

## License

Oracle Internal.
