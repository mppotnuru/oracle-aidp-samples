# Changelog

All notable changes to this project are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); versions follow semver.

## [0.2.0] — 2026-09-11

### Added
- **Glue ETL → PySpark translator** (`translate/glue_to_spark.py`) — 11 deterministic
  rules; DynamicFrame-only transforms (ApplyMapping, ResolveChoice, Join, …) are
  flagged for manual review, never silently dropped.
- **Live AWS testing path** — `scripts/live_seed.py` / `live_teardown.py` seed and
  remove a small, tagged, idempotent AWS test stack (S3 + Glue catalog + Athena).
- **Claude Code plugin** — `.claude-plugin/plugin.json` + `marketplace.json`,
  `skills/aws-aidp-migrator/SKILL.md`, and `commands/{inventory,plan,migrate,verify}.md`.
- **MCP server** (`aws_aidp/mcp_server.py`, `aws-aidp-mcp` entry point) exposing the
  four verbs to Codex / Cursor / Claude Desktop. Requires Python 3.10+.
- Docs: `TESTING.md`, `docs/FDE_PRESENTATION.md` (+ generated deck), `docs/MCP.md`,
  `docs/DEMO_VIDEO_SCRIPT.md`.

### Fixed (found via live testing against a real AWS account)
- Athena inventory crashed on `list_work_groups` — it is not a boto3 paginator;
  replaced with a manual `NextToken` loop.
- `CROSS JOIN UNNEST(split(col, ';'))` fell through unrewritten **and** unflagged
  (false "OK"). Array-expression regex now allows one level of nested parens, plus a
  safety-net flag so any residual `CROSS JOIN UNNEST` is always flagged.
- Inline `frame=DynamicFrame.fromDF(df, …)` in `write_dynamic_frame.from_options`
  produced a broken `DynamicFrame.write…`; the `fromDF` collapse now runs before the
  from_options rules so it resolves to `df.write…`.

### Tests
- 15 standalone tests (8 Glue + 7 Athena), including regressions for all three bugs.

## [0.1.0] — 2026-06-28

### Added
- Initial POC: `inventory`, `plan`, `migrate --demo`, `verify` verbs.
- Athena (Presto/Trino) → Spark SQL translator with deterministic rewrite rules.
- Fixture-driven demo (Acme Insurance) via `demo.sh`.
