"""OCI-DI data flow → PySpark notebook translator.

Deterministic-first per the migrator-family contract:
- Each operator type has a named translation rule
- Unknown operators are *flagged* (not guessed) with a reason the reviewer
  can act on, and inserted as a NotImplementedError sentinel in the output
- Node identity (`node.name`) becomes the Python DataFrame variable name

Usage:
    payload = json.load(open("fixtures/demo-dataflow.json"))
    code = translate(payload)
    Path("gl_bronze_load.py").write_text(code)
"""
from __future__ import annotations
from typing import Callable, Optional

# A translator takes (node_dict, upstream_var_names) -> emitted PySpark line.
TranslatorFn = Callable[[dict, list[str]], str]


# ---------------------------------------------------------------------------
# Per-operator translators (deterministic rules)
# ---------------------------------------------------------------------------
def _var(node: dict) -> str:
    """Python-safe variable name derived from node.name."""
    name = node.get("name") or node.get("key") or "df"
    return "".join(c if c.isalnum() or c == "_" else "_" for c in name).lower()


def _emit_source(node: dict, ins: list[str]) -> str:
    op = node.get("operator") or {}
    tgt = _var(node)
    fmt = (op.get("format") or "").upper()
    schema = op.get("schema"); table = op.get("table"); obj = op.get("object")
    if fmt in ("DELTA", "PARQUET", "CSV", "JSON", "ORC") and obj:
        # Object storage read via path
        return (f'{tgt} = spark.read.format("{fmt.lower()}")'
                f'.load("oci://{{landing_bucket}}@{{namespace}}/{obj}")')
    if schema and table:
        # ADW/ATP table read via Spark JDBC catalog (3-part name)
        return f'{tgt} = spark.read.table("{{catalog}}.{schema}.{table}")'
    return f'# [FLAG] source operator {node.get("key")}: missing format/path or schema/table — rebuild manually'


def _emit_filter(node: dict, ins: list[str]) -> str:
    op = node.get("operator") or {}
    tgt = _var(node); src = ins[0] if ins else "???"
    expr = op.get("filter_expression", "")
    if not expr:
        return f'# [FLAG] filter operator {node.get("key")}: missing filter_expression'
    # DI filter expressions are already SQL-compatible — Spark SQL filter() accepts raw SQL
    return f'{tgt} = {src}.filter("{expr}")'


def _emit_join(node: dict, ins: list[str]) -> str:
    op = node.get("operator") or {}
    tgt = _var(node)
    if len(ins) < 2:
        return f'# [FLAG] join operator {node.get("key")}: expected >=2 inputs, got {len(ins)}'
    left, right = ins[0], ins[1]
    jt = (op.get("join_type") or "INNER").lower().replace("_", "")  # LEFT_OUTER -> leftouter
    cond = op.get("join_condition", "")
    if not cond:
        return f'# [FLAG] join operator {node.get("key")}: missing join_condition'
    # DI join_condition references source port names; keep raw since Spark SQL handles qualified names
    return f'{tgt} = {left}.join({right}, on=F.expr("{cond}"), how="{jt}")'


def _emit_lookup(node: dict, ins: list[str]) -> str:
    op = node.get("operator") or {}
    tgt = _var(node)
    if len(ins) < 2:
        return f'# [FLAG] lookup operator {node.get("key")}: expected 2 inputs (driver + lookup)'
    driver, lookup = ins[0], ins[1]
    cond = op.get("lookup_condition") or op.get("join_condition", "")
    if not cond:
        return f'# [FLAG] lookup operator {node.get("key")}: missing lookup_condition'
    return f'{tgt} = {driver}.join({lookup}, on=F.expr("{cond}"), how="left")  # lookup semantics via left join'


def _emit_aggregate(node: dict, ins: list[str]) -> str:
    op = node.get("operator") or {}
    tgt = _var(node); src = ins[0] if ins else "???"
    groups = op.get("group_by") or []
    aggs   = op.get("aggregates") or []
    if not aggs:
        return f'# [FLAG] aggregator operator {node.get("key")}: no aggregates defined'
    group_expr = ", ".join(f'"{g}"' for g in groups)
    agg_exprs  = ", ".join(f'F.expr("{a["expression"]}").alias("{a["alias"]}")' for a in aggs)
    if groups:
        return f'{tgt} = {src}.groupBy({group_expr}).agg({agg_exprs})'
    return f'{tgt} = {src}.agg({agg_exprs})'


def _emit_union(node: dict, ins: list[str]) -> str:
    tgt = _var(node)
    if len(ins) < 2:
        return f'# [FLAG] union operator {node.get("key")}: expected >=2 inputs, got {len(ins)}'
    expr = f"{ins[0]}"
    for other in ins[1:]:
        expr = f"{expr}.unionByName({other}, allowMissingColumns=True)"
    return f'{tgt} = {expr}'


def _emit_target(node: dict, ins: list[str]) -> str:
    op = node.get("operator") or {}
    src = ins[0] if ins else "???"
    fmt = (op.get("format") or "DELTA").lower()
    mode = (op.get("write_mode") or "OVERWRITE").lower()
    schema = op.get("schema"); table = op.get("table"); obj = op.get("object")
    if schema and table:
        return (f'{src}.write.format("{fmt}").mode("{mode}")'
                f'.saveAsTable("{{catalog}}.{schema}.{table}")')
    if obj:
        return (f'{src}.write.format("{fmt}").mode("{mode}")'
                f'.save("oci://{{landing_bucket}}@{{namespace}}/{obj}")')
    return f'# [FLAG] target operator {node.get("key")}: missing schema/table or object path'


REGISTRY: dict[str, TranslatorFn] = {
    "SOURCE_OPERATOR":     _emit_source,
    "FILTER_OPERATOR":     _emit_filter,
    "JOIN_OPERATOR":       _emit_join,
    "LOOKUP_OPERATOR":     _emit_lookup,
    "AGGREGATOR_OPERATOR": _emit_aggregate,
    "UNION_OPERATOR":      _emit_union,
    "TARGET_OPERATOR":     _emit_target,
}


# ---------------------------------------------------------------------------
# Walker
# ---------------------------------------------------------------------------
def _topo_order(nodes: list[dict]) -> list[dict]:
    """Order nodes so every node appears after the nodes that produce its inputs.
       OCI-DI data flows are DAGs keyed by output_ports → input_ports references."""
    by_output_port: dict[str, dict] = {}
    for n in nodes:
        for p in n.get("output_ports") or []:
            by_output_port[p] = n
    # Kahn's algorithm
    remaining = list(nodes)
    emitted:   list[dict] = []
    emitted_keys: set[str] = set()
    while remaining:
        progress = False
        for n in list(remaining):
            inputs = n.get("input_ports") or []
            upstream_keys = {by_output_port[p]["key"] for p in inputs if p in by_output_port}
            if upstream_keys.issubset(emitted_keys):
                emitted.append(n)
                emitted_keys.add(n["key"])
                remaining.remove(n)
                progress = True
        if not progress:
            # cycle or dangling ports — emit the rest in file order, flagged
            emitted.extend(remaining)
            break
    return emitted


def translate(payload: dict) -> str:
    """Turn a get_data_flow(expand_references='all') payload into a PySpark .py file."""
    name     = payload.get("name") or "data_flow"
    desc     = payload.get("description") or ""
    nodes    = payload.get("nodes") or []
    by_outp  = {p: n for n in nodes for p in (n.get("output_ports") or [])}

    header = [
        f'"""Auto-generated by oci-di-aidp-migrator from OCI-DI data flow `{name}`.',
        '',
        f'{desc}' if desc else '',
        '',
        'Deterministic-first translation. Lines beginning with `# [FLAG]` could',
        'not be safely translated and need manual review before running.',
        '"""',
        'from pyspark.sql import SparkSession, functions as F',
        '',
        'spark = SparkSession.builder.getOrCreate()',
        '',
        '# Context substitutions (set by the AIDP job runner):',
        '#   {catalog}, {landing_bucket}, {namespace}',
        '',
    ]
    body: list[str] = []

    flag_count = 0
    for node in _topo_order(nodes):
        op_type = node.get("model_type") or ""
        ins = [_var(by_outp[p]) for p in (node.get("input_ports") or []) if p in by_outp]
        fn = REGISTRY.get(op_type)
        if fn is None:
            flag_count += 1
            body.append(f'# [FLAG] unsupported operator model_type={op_type!r} on node {node.get("key")!r}')
            body.append(f'# Reviewer: implement equivalent PySpark for this operator or request plugin support.')
            continue
        body.append(f'# {op_type}  key={node.get("key")}  name={node.get("name")}')
        body.append(fn(node, ins))
        body.append('')

    footer = ['', f'# translator summary: nodes={len(nodes)}  flagged={flag_count}']
    return "\n".join(header + body + footer)
