---
description: Dry-run each migrated AIDP artifact and emit an evidence report. Confirms notebooks load, jobs resolve, connectors can be opened, row counts land where expected.
---

Run the verify step after `/migrate --apply`.

Shell:
    oci-di-aidp verify --manifest ./out/aidp-artifacts/manifest.json

Report lands at `./out/verify-report-<timestamp>.html` + .json.

For each migrated artifact:
- Loaded on cluster? (yes/no + error)
- Compiled without exception?
- Row count delta vs source (if a sample pipeline was executed)
- Any deterministic translation flagged as "needs review"

Nothing is "verified" unless it executed on AIDP. Dry-run-only artifacts are marked explicitly as "not execution-verified" (same pattern as the AWS plugin).
