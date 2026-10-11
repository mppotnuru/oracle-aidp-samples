---
description: Inventory an OCI Data Integration workspace — list projects, folders, data flows, pipelines, tasks, connections, and data assets. First step in the OCI-DI → AIDP migration.
---

Run the inventory step of the OCI-DI → AIDP migrator.

Required inputs (ask if missing):
- OCI-DI workspace OCID (ocid1.disworkspace.oc1...)
- Target compartment OCID
- OCI config profile to use (default OASEFDE)

Shell:
    oci-di-aidp inventory --workspace-id <OCID> --compartment <OCID> --out ./out

The manifest lands at `./out/inventory-<last-8>.json`. Summarize the counts for the user and surface anything that looks unusual (e.g. zero data flows, zero connections — usually means wrong workspace OCID).

Next step: run `/plan` with the manifest.
