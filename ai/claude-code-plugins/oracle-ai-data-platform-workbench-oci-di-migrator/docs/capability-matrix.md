# OCI-DI → AIDP Migrator — Capability Matrix

For the Monday scoping call. Leave the CSS column blank until their team walks
through theirs — this doc is a neutral prompt, not a pitch.

Dates:
- 2026-10-10 — initial draft, FDE columns reflect state at commit `47aadf6` of
  `mppotnuru/oci-di-aidp-migrator`.

Legend: ✅ live & tested · 🔜 scaffolded, build pending · 🚫 not planned · ? unknown

---

## 1. Discovery (inventory)

| Capability                                                   | FDE scaffold | CSS tool |
|--------------------------------------------------------------|:---:|:---:|
| Enumerate projects                                           | ✅ | ? |
| Enumerate folders (nested, per-project)                      | ✅ | ? |
| Enumerate data flows (with parent-ref hierarchy)             | ✅ | ? |
| Enumerate pipelines                                          | ✅ | ? |
| Enumerate tasks (integration, SQL, data-loader, OCI Function)| ✅ | ? |
| Enumerate data assets (ADW, ATP, Object Storage, generic REST)| ✅ | ? |
| Enumerate connections per data asset                         | ✅ | ? |
| Pagination via `oci.pagination` (no result caps)             | ✅ | ? |
| Offline fixture mode (no OCI auth required)                  | ✅ | ? |
| Live-tested against real OCI-DI workspace                    | ✅ | ? |
| JSON manifest output (versioned, diff-able)                  | ✅ | ? |

## 2. Translation

| Capability                                                   | FDE scaffold | CSS tool |
|--------------------------------------------------------------|:---:|:---:|
| Data flow operator → PySpark (source/filter/join/lookup/     |     |   |
| aggregate/union/target — 7 of 10 core operators)             | ✅ fixture-tested | ? |
| Data flow operator — pivot / split / SQL op                  | 🔜 | ? |
| Expression language → Spark expressions (deterministic table)| 🔜 | ? |
| SQL task body → Spark SQL (via sqlglot)                      | 🔜 | ? |
| Pipeline task graph → AIDP job graph                         | 🔜 | ? |
| Data asset → AIDP connector (ADW/ATP/OS/REST)                | 🔜 | ? |
| Deterministic-first (named rule per rewrite)                 | ✅ | ? |
| Flag-don't-guess for unsupported constructs (named reason)   | ✅ fixture-tested | ? |
| Zero LLM calls in core translation path                      | ✅ grep-audited | ? |
| DAG topo-sort for node ordering                              | ✅ | ? |

## 3. Validation & verification

| Capability                                                   | FDE scaffold | CSS tool |
|--------------------------------------------------------------|:---:|:---:|
| Dry-run mode (publish only on explicit `--apply`)            | 🔜 | ? |
| Evidence report (per-artifact PASS / REVIEW / FAIL / SKIP)   | 🔜 | ? |
| Row-count delta vs source (sampled)                          | 🔜 | ? |
| HTML + JSON report formats                                   | 🔜 | ? |

## 4. Packaging & distribution

| Capability                                                   | FDE scaffold | CSS tool |
|--------------------------------------------------------------|:---:|:---:|
| Claude Code plugin (`.claude-plugin/plugin.json`)            | ✅ | ? |
| Codex CLI plugin (`.codex-plugin/plugin.json`)               | ✅ | ? |
| MCP server for Codex/Cursor (`.mcp.json`)                    | ✅ stub | ? |
| Pure Python CLI (`oci-di-aidp`), venv-installable            | ✅ | ? |
| 4 slash commands (`/inventory`, `/plan`, `/migrate`, `/verify`) | ✅ | ? |
| Skill package for agent-driven invocation                    | ✅ | ? |
| Published to `oracle-samples/oracle-aidp-samples`            | 🔜 (post review) | ? |

## 5. Deployment story — directly addresses Ahmed's constraints

| Capability                                                   | FDE scaffold | CSS tool |
|--------------------------------------------------------------|:---:|:---:|
| Runs in corporate Codex without a Claude API key             | ✅ | ? |
| Runs in corporate Codex without any LLM API key              | ✅ | ? |
| Token cost per migrated job: deterministic path = $0         | ✅ | ? |
| Token cost: optional narrative only on reviewer-flagged items| ✅ opt-in | ? |
| Repeatable, deterministic output across runs                 | ✅ | ? |

## 6. Family alignment (part of a 6-plugin set)

| Capability                                                   | FDE scaffold | CSS tool |
|--------------------------------------------------------------|:---:|:---:|
| Same `inventory → plan → migrate → verify` grammar as other 5| ✅ | n/a |
| Same manifest shape (so cross-source orchestration possible) | ✅ | ? |
| Same CLI binary conventions                                  | ✅ | ? |
| Reuses patterns from AWS/Snowflake/Fabric/Informatica/DBX    | ✅ | ? |

---

## Discussion questions for the call

Rather than framing CSS vs FDE as a competition, these are the questions
whose answers decide the collaboration shape:

1. **Scope coverage.** For the 300 Kaiser jobs, what fraction does the CSS
   tool today translate end-to-end deterministically? Where does it fall back
   to manual rewrite?
2. **Reproducibility.** If the same OCI-DI job is run through the CSS tool
   twice, is the AIDP output byte-identical? (Deterministic-first is the
   principle; manual steps break this.)
3. **Flagged-items contract.** How does the CSS tool surface things it can't
   translate — reviewer-friendly flag with a rebuild path, or silent skip?
4. **Install footprint.** What does CSS need on a laptop / in corporate Codex
   to run their tool? Any Claude or external LLM dependency?
5. **Hand-off model.** Does CSS run the 300-job migration themselves, or does
   Kaiser's team drive it with CSS tooling + support?
6. **Convergence options.**
   - **(a) Converge:** adopt one tool, retire the others
   - **(b) Extend:** CSS tool stays primary, FDE adds translators/validators
     where coverage gaps exist
   - **(c) Complementary:** CSS tool handles current scope, FDE plugin
     handles anything net-new or edge-case
   Which model does Kaiser actually need for Oct 15 commitments and the
   post-15 bulk run?

---

## Next-steps (post-call)

- Lock on one of (a) / (b) / (c) above with named owner per workstream.
- Confirm acceptance criteria for the pilot (1-2 representative jobs) —
  automation %, functional equivalence, performance, scheduling, monitoring.
- Define definition-of-done for the 300-job run.
