"""`oci-di-aidp` CLI — same shape as sibling plugins (inventory / plan / migrate / verify)."""
from __future__ import annotations
import json
import sys
from pathlib import Path

import click

import json

from ._env import COMPARTMENT, WORKSPACE_ID, DEFAULT_OUTPUT_DIR
from .inventory.manifest import build_inventory, load_fixture
from .translate.data_flow_to_pyspark import translate as translate_data_flow
from .fixtures import fixture_path


@click.group()
def main():
    """OCI Data Integration → Oracle AI Data Platform migrator."""


# ---------------------------------------------------------------------------
# inventory
# ---------------------------------------------------------------------------
@main.command()
@click.option("--workspace-id",  default=WORKSPACE_ID, show_default=True,
              help="OCI-DI workspace OCID (or DI_WORKSPACE_OCID env var)")
@click.option("--compartment",   default=COMPARTMENT,  show_default=True,
              help="Target compartment OCID (or COMPARTMENT_OCID env var)")
@click.option("--out",           default=DEFAULT_OUTPUT_DIR, show_default=True,
              help="Output directory for the manifest JSON")
@click.option("--fixture",       default=None,
              help="Load a bundled fixture (e.g. 'demo') instead of hitting the OCI API — no auth needed.")
def inventory(workspace_id: str, compartment: str, out: str, fixture: str):
    """Discover every project / folder / data-flow / pipeline / task / connection / data-asset in a DI workspace."""
    if fixture:
        try:
            inv = load_fixture(fixture)
        except ValueError as e:
            click.echo(f"[error] {e}", err=True)
            sys.exit(2)
        tag = fixture
        click.echo(f"[fixture] using '{fixture}' bundled manifest (no OCI calls)")
    else:
        if not workspace_id or not compartment:
            click.echo("[error] workspace-id + compartment required (flags or env), OR use --fixture demo", err=True)
            sys.exit(2)
        inv = build_inventory(workspace_id, compartment)
        tag = workspace_id[-8:]
    out_path = Path(out) / f"inventory-{tag}.json"
    inv.to_json(out_path)
    click.echo(f"[inventory] workspace={inv.workspace_name}")
    for k, v in inv.summary().items():
        click.echo(f"  {k:<12} {v:>5}")
    click.echo(f"[inventory] manifest → {out_path}")


# ---------------------------------------------------------------------------
# plan / translate / migrate / verify  — stubs for now
# ---------------------------------------------------------------------------
@main.command()
def plan():
    """Produce a translation plan + risk flags from the inventory. [stub]"""
    click.echo("plan: not implemented yet")


@main.command()
@click.option("--data-flow-json", type=click.Path(exists=True, dir_okay=False),
              help="Path to a single OCI-DI data flow payload (as returned by get_data_flow(expand_references='all')).")
@click.option("--fixture", default=None,
              help="Use a bundled data-flow fixture (e.g. 'demo-dataflow') instead of a live file.")
@click.option("--out", default=DEFAULT_OUTPUT_DIR, show_default=True,
              help="Output directory for the generated .py notebook")
def migrate(data_flow_json: str, fixture: str, out: str):
    """Translate a data flow payload into a PySpark notebook (.py)."""
    if fixture:
        try:
            path = fixture_path(fixture)
        except ValueError as e:
            click.echo(f"[error] {e}", err=True); sys.exit(2)
        payload = json.loads(path.read_text())
        click.echo(f"[fixture] using '{fixture}' bundled data-flow (no OCI calls)")
    elif data_flow_json:
        payload = json.loads(Path(data_flow_json).read_text())
    else:
        click.echo("[error] need --data-flow-json <path> OR --fixture <name>", err=True); sys.exit(2)

    code = translate_data_flow(payload)
    out_path = Path(out) / f'{payload.get("name") or "data_flow"}.py'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(code)
    flagged = sum(1 for line in code.splitlines() if line.startswith("# [FLAG]"))
    nodes = len(payload.get("nodes") or [])
    click.echo(f"[migrate] data_flow={payload.get('name')}  nodes={nodes}  flagged={flagged}")
    click.echo(f"[migrate] wrote → {out_path}")


@main.command()
def verify():
    """Dry-run the generated AIDP artifacts and emit an evidence report. [stub]"""
    click.echo("verify: not implemented yet")


if __name__ == "__main__":
    main()
