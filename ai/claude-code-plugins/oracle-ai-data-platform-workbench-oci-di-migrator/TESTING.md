# Testing guide

Thanks for helping test **oci-di-aidp-migrator** — a Claude Code plugin that
migrates an Oracle Cloud Infrastructure Data Integration (OCI-DI) workspace
to Oracle AIDP.

You do **not** need an OCI account for the core test pass — everything runs
offline against bundled fixtures. Budget ~20–30 min for a full pass.

---

## 1. Setup (3 min)

```bash
git clone https://github.com/oracle-samples/oracle-aidp-samples.git
cd oracle-aidp-samples/ai/claude-code-plugins/oracle-ai-data-platform-workbench-oci-di-migrator
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

Requirements: **Python 3.9+**. Runtime deps: `oci`, `sqlglot`, `click`, `rich`,
`pyyaml`. Optional extras: `[mcp]` (requires Python 3.10+), `[llm]` (optional
narrative generation).

---

## 2. Smoke test — offline, no OCI auth

### a. Inventory with a bundled fixture

```bash
oci-di-aidp inventory --fixture demo
```

**Expected:** prints `workspace=acme_etl_prod` + counts (3 projects, 3 folders,
5 data flows, 2 pipelines, 6 tasks, 4 connections, 4 data assets) and writes
`out/inventory-demo.json`.

✅ **Pass** if counts match and the JSON file is well-formed.

### b. Migrate a data flow with a bundled fixture

```bash
oci-di-aidp migrate --fixture demo-dataflow --out ./out
```

**Expected:** prints `nodes=6 flagged=0` and writes `out/gl_bronze_load.py`.

Open the generated file. You should see 6 PySpark statements (2 sources, a
filter, a left-outer join, an aggregate, a target write) in topological order,
with `{catalog}` / `{landing_bucket}` / `{namespace}` placeholders for the AIDP
job runner to substitute.

✅ **Pass** if the file compiles with `python -c "exec(open('out/gl_bronze_load.py').read())"`
   (ignore `SparkSession.builder.getOrCreate()` import complaints — Spark isn't
   installed by the plugin; the shape of the code is what you're verifying).

### c. Flag-don't-guess path

Feed the translator a payload with an unknown operator (any `model_type` not in
the registry):

```python
from oci_di_aidp.translate.data_flow_to_pyspark import translate
print(translate({
    "name": "flag_test",
    "nodes": [
        {"key":"src","name":"s","model_type":"SOURCE_OPERATOR",
         "operator":{"format":"parquet","object":"raw/*.parquet"},
         "output_ports":["s.out"]},
        {"key":"custom","name":"odd","model_type":"CUSTOM_UNKNOWN_OPERATOR",
         "operator":{},
         "input_ports":["s.out"],"output_ports":["odd.out"]},
    ],
}))
```

**Expected:** a `# [FLAG] unsupported operator model_type='CUSTOM_UNKNOWN_OPERATOR'`
line in the output, and the footer shows `flagged=1`.

✅ **Pass** if the unknown operator is flagged, not silently emitted as something
   else.

---

## 3. Live test (optional — needs OCI auth)

```bash
export OCI_CONFIG_PROFILE=DEFAULT   # or whichever profile has DI access
export COMPARTMENT_OCID=ocid1.compartment.oc1..<your-compartment>
export DI_WORKSPACE_OCID=ocid1.disworkspace.oc1.<region>.<your-workspace>

oci-di-aidp inventory
```

**Expected:** reads your workspace, prints resource counts, writes
`out/inventory-<last-8>.json`.

✅ **Pass** if counts match what you see in the OCI Console under Data Integration.

---

## 4. What to file a bug for

- Any traceback from the CLI or any command
- A translator that produces runnable-looking code for an unsupported operator
  (should be flagged)
- A `migrate` output with silently dropped nodes (topo-sort coverage gap)
- Missing files in the generated plugin tree after `pip install -e .`
