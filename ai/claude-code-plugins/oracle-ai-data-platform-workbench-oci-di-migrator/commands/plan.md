---
description: Produce a translation plan from an OCI-DI inventory — maps each data flow / pipeline / task to its AIDP equivalent, flags risks, estimates effort.
---

Run the plan step after `/inventory`.

Required inputs:
- Path to the manifest JSON produced by `/inventory`
- Target AIDP workspace ID (optional, read from env if present)

Shell:
    oci-di-aidp plan --manifest ./out/inventory-<id>.json

The plan should list, for each DI resource:
- Target AIDP artifact (notebook, job, connector)
- Translation confidence (deterministic / needs review / unparseable)
- Risk flags (custom OCI Function, streaming data flow, unsupported operator)
- Approximate effort band (XS / S / M / L)

Next step: `/migrate --plan ./out/plan.json --apply` once the plan is reviewed.
