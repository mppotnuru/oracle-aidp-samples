---
name: oci-di-aidp-migrator
description: "Migrate an Oracle Cloud Infrastructure Data Integration (OCI-DI) workspace to Oracle AI Data Platform (AIDP). Use when the user wants to inventory an OCI-DI workspace, plan a migration to AIDP, translate OCI-DI data flows / pipelines / tasks to Spark on AIDP, or verify a migration's output. Wraps the `oci-di-aidp` CLI with the four verbs inventory, plan, migrate, and verify."
---

# OCI-DI → Oracle AIDP migrator

This skill drives the `oci-di-aidp` CLI, which migrates an OCI Data Integration
workspace to Oracle AIDP in four verbs. The translators are **deterministic-first**:
each rewrite is a named rule with a reason, and anything that can't be safely
rewritten is **flagged and left in place**, never silently changed. Preserve that
principle — never hand-edit a flagged construct into a silent rewrite.

## Prerequisite

The CLI must be installed:

```bash
pip install -e .                          # from the plugin directory
pip install -e "${CLAUDE_PLUGIN_ROOT}"    # or, when installed as a plugin
```

Live OCI-DI mode uses the standard oci SDK auth chain (`OCI_CONFIG_PROFILE`,
`~/.oci/config`, resource principal). Offline/demo mode needs no OCI account.

## The four verbs (run in order)

```bash
oci-di-aidp inventory --workspace-id <OCID> --compartment <OCID>   # read-only DI scan → manifest JSON
oci-di-aidp plan      --manifest ./out/inventory-<id>.json          # manifest → AIDP translation plan
oci-di-aidp migrate   --plan ./out/plan.json [--apply]              # translate; without --apply = dry run
oci-di-aidp verify    --manifest ./out/aidp-artifacts/manifest.json # evidence report
```

## What gets translated

- **Data flows** — operator graph (source, filter, join, lookup, aggregate, pivot, union, split, target, SQL op) → PySpark notebook on AIDP
- **Pipelines** — task orchestration → AIDP job graph
- **Tasks** — SQL tasks → Spark SQL (sqlglot-based); data-loader tasks → notebook steps; OCI Function tasks → flagged
- **Data assets** — OCI DB (ADB/ADW/ATP), Object Storage, Autonomous JSON → equivalent AIDP connectors
- **Expressions** — DI expression language → Spark expressions via a deterministic translation table

## What gets flagged (not translated)

- Custom OCI Function tasks (opaque code)
- Streaming data flows (no AIDP equivalent yet)
- Task triggers / schedules (map separately to AIDP job cron)
- Encrypted parameters without keys in the destination compartment

Flagged items appear in the plan output with a named reason + rebuild path.

## Related skills in the migrator family

Databricks, Snowflake, Informatica, Fabric, AWS — same `inventory → plan →
migrate → verify` grammar across all six plugins.
