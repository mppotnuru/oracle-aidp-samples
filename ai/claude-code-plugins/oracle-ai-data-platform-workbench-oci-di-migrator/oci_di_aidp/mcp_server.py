"""MCP server exposing the four verbs (inventory / plan / migrate / verify) to Codex / Cursor.

Mirrors the aws-aidp pattern: thin wrapper around the CLI entrypoints so an
MCP-aware agent can call them as tools.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

# Deferred imports — mcp_server is also used as a plain CLI subcommand host when
# the mcp package isn't installed; we don't want import to fail at package load.

def _inventory(workspace_id: str, compartment_id: str, out_dir: str = "./out") -> dict:
    from .inventory.manifest import build_inventory
    inv = build_inventory(workspace_id, compartment_id)
    out_path = Path(out_dir) / f"inventory-{workspace_id[-8:]}.json"
    inv.to_json(out_path)
    return {"workspace": inv.workspace_name, "summary": inv.summary(), "manifest": str(out_path)}


def _plan(manifest_path: str) -> dict:
    return {"status": "not_implemented", "manifest": manifest_path}


def _migrate(plan_path: str, apply: bool = False) -> dict:
    return {"status": "not_implemented", "plan": plan_path, "apply": apply}


def _verify(manifest_path: str) -> dict:
    return {"status": "not_implemented", "manifest": manifest_path}


def main() -> None:
    """Entry point for `python -m oci_di_aidp.mcp_server`.

    When MCP SDK is available, boot a stdio MCP server exposing the four tools.
    Without it, print the tool catalog as JSON (useful for local inspection).
    """
    try:
        from mcp.server.fastmcp import FastMCP   # type: ignore
    except Exception:
        print(json.dumps({
            "server": "oci-di-aidp",
            "version": "0.1.0",
            "tools": ["inventory", "plan", "migrate", "verify"],
            "note": "Install `mcp` to run as a stdio MCP server (used by Codex/Cursor).",
        }, indent=2))
        return

    server = FastMCP("oci-di-aidp")

    @server.tool()
    def inventory(workspace_id: str, compartment_id: str, out_dir: str = "./out") -> dict:
        """Enumerate every project / folder / data-flow / pipeline / task / connection / data-asset in an OCI-DI workspace."""
        return _inventory(workspace_id, compartment_id, out_dir)

    @server.tool()
    def plan(manifest_path: str) -> dict:
        """Produce a translation plan + risk flags from an inventory manifest."""
        return _plan(manifest_path)

    @server.tool()
    def migrate(plan_path: str, apply: bool = False) -> dict:
        """Translate each data flow / pipeline into AIDP notebooks + jobs."""
        return _migrate(plan_path, apply)

    @server.tool()
    def verify(manifest_path: str) -> dict:
        """Dry-run the generated AIDP artifacts and emit an evidence report."""
        return _verify(manifest_path)

    server.run()


if __name__ == "__main__":
    main()
