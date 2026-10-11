---
description: Translate every planned OCI-DI resource into AIDP notebooks + jobs. Writes PySpark notebooks for data flows, AIDP jobs for pipelines, connectors for data assets.
---

Run the migrate step after `/plan`.

Required inputs:
- Path to the plan JSON produced by `/plan`
- `--apply` to actually publish to AIDP (default: dry-run, lands in ./out/aidp-artifacts/)

Shell:
    oci-di-aidp migrate --plan ./out/plan.json           # dry run
    oci-di-aidp migrate --plan ./out/plan.json --apply   # publish

Output structure under `./out/aidp-artifacts/`:
    notebooks/<data_flow_name>.ipynb
    jobs/<pipeline_name>.json
    connectors/<asset_name>.json
    manifest.json         (what was created, with AIDP OCIDs/IDs when --apply)

Next step: `/verify` against the live AIDP workspace to prove the artifacts load + run.
