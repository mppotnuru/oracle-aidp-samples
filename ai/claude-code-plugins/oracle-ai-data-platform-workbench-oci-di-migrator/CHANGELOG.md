# Changelog

All notable changes to this project are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); versions follow semver.

## [0.1.0] — 2026-10-11

Initial release — sixth entry in the AIDP migrator family (Databricks /
Snowflake / Informatica / Fabric / AWS / **OCI-DI**).

### Added
- **CLI** `oci-di-aidp` with four verbs (`inventory`, `plan`, `migrate`,
  `verify`) following the shared migrator grammar.
- **Inventory module** (`oci_di_aidp/inventory/manifest.py`) that enumerates
  projects, folders, data flows, pipelines, tasks, connections, and data assets
  for a workspace via the OCI DI SDK. Live-tested against a real workspace;
  manifest shape is JSON and diff-able across runs.
- **Translator** (`oci_di_aidp/translate/data_flow_to_pyspark.py`) — operator
  dispatcher + topo-sort walker, deterministic PySpark emission for 7 of the 10
  common operator types: SOURCE, FILTER, JOIN, LOOKUP, AGGREGATOR, UNION,
  TARGET. Unknown operators are *flagged* with a named reason, not guessed.
- **Offline fixture mode** (`--fixture demo` / `--fixture demo-dataflow`) so
  demos and tests run with no OCI auth.
- **Claude Code plugin manifest** (`.claude-plugin/plugin.json`,
  `marketplace.json`) + 4 slash commands under `commands/`.
- **MCP server** (`oci_di_aidp/mcp_server.py`) exposing the four verbs; stub
  mode prints the tool catalog without the `mcp` package installed.
- **Skill package** (`skills/oci-di-aidp-migrator/SKILL.md`) for agent-driven
  invocation.
- **Capability matrix** (`docs/capability-matrix.md`) comparing the plugin
  to other OCI-DI migration approaches, including Thoughtworks' XConf
  methodology.

### Design principles (shared with the migrator family)
- **Deterministic-first.** Every translation is a named Python rule with a
  reason. No LLM in the core migration path — zero API-key dependency, zero
  per-job token cost, repeatable across runs.
- **Flag-don't-guess.** Any construct not covered by a rule emits a
  `# [FLAG]` sentinel in the output with a rebuild path for the reviewer.
- **Offline-first.** Fixture mode bypasses OCI auth entirely so the plugin
  can be adopted in air-gapped / corporate Codex environments.

### Known gaps (next release)
- 3 operator types still pending: `PIVOT`, `SPLIT`, `SQL`.
- Pipeline-level task-graph → AIDP-job translation not yet wired (data flow
  only in 0.1.0).
- Verify step is a stub; evidence-report generation lands in 0.2.0.
