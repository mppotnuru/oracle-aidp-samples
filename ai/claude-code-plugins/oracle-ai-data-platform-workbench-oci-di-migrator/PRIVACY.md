# Privacy

The **Oracle AIDP Migrator for OCI Data Integration** runs locally and is
designed to keep your data in your own environment.

## What it does with data
- **Inventory** performs *read-only* OCI Data Integration API calls (projects,
  folders, data flows, pipelines, tasks, connections, data assets) using your
  own OCI credentials. It reads resource metadata (names, operator graphs,
  SQL-task bodies, data-asset endpoints) to build a local JSON manifest.
- **Plan / migrate / verify** run entirely on your machine and write local
  artifacts (a manifest, a plan, generated PySpark notebooks, and a report).
  Migration translation is **deterministic** — rules are named Python functions;
  no network calls, no LLM round-trip.
- The optional **MCP server** exposes the same four verbs to a local MCP client;
  it spawns the local CLI and returns its output. No data is sent to Oracle,
  Anthropic, OpenAI, or any third party by the migrator itself.

## What it does NOT do
- It does not transmit your source metadata, operator definitions, SQL task
  bodies, or credentials to any external service. The generated AIDP artifacts
  are written to disk for you to review and promote.

## Your responsibility
- Live OCI-DI and AIDP calls use credentials you supply (standard OCI auth chains
  — `~/.oci/config` profile, resource principal, instance principal).
- The optional `[llm]` extra enables LLM-powered narrative generation for
  flagged items *only*. If enabled, the flagged snippet is sent to the model
  endpoint you configure — review your tenancy's data-handling policy before
  turning it on. The core migration path never calls an LLM.

Questions or concerns: open a GitHub issue on the repository.
