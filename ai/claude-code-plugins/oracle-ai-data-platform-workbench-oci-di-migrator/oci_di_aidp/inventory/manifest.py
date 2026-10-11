"""Build the inventory manifest for an OCI-DI workspace."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Optional
import json
from pathlib import Path

from ..oci_di_client import OCIDataIntegrationClient
from ..fixtures import fixture_path


@dataclass
class WorkspaceInventory:
    workspace_id:   str
    workspace_name: str
    compartment_id: str
    projects:       list[dict] = field(default_factory=list)
    folders:        list[dict] = field(default_factory=list)
    data_flows:     list[dict] = field(default_factory=list)
    pipelines:      list[dict] = field(default_factory=list)
    tasks:          list[dict] = field(default_factory=list)
    connections:    list[dict] = field(default_factory=list)
    data_assets:    list[dict] = field(default_factory=list)

    def summary(self) -> dict[str, int]:
        return {
            "projects":    len(self.projects),
            "folders":     len(self.folders),
            "data_flows":  len(self.data_flows),
            "pipelines":   len(self.pipelines),
            "tasks":       len(self.tasks),
            "connections": len(self.connections),
            "data_assets": len(self.data_assets),
        }

    def to_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), default=str, indent=2))


def _summ(obj: Any) -> dict:
    """Shrink an oci model object to a JSON-safe dict."""
    if obj is None:
        return {}
    d = {}
    for attr in ("key", "name", "identifier", "description", "object_version",
                 "object_status", "model_type", "model_version"):
        v = getattr(obj, attr, None)
        if v is not None:
            d[attr] = v
    # project / folder refs
    parent_ref = getattr(obj, "parent_ref", None)
    if parent_ref is not None:
        d["parent_key"] = getattr(parent_ref, "parent", None)
        d["root_doc_id"] = getattr(parent_ref, "root_doc_id", None)
    return d


def load_fixture(name: str) -> WorkspaceInventory:
    """Load a bundled fixture manifest instead of hitting the OCI API — demo mode."""
    data = json.loads(fixture_path(name).read_text())
    inv = WorkspaceInventory(
        workspace_id=data.get("workspace_id", ""),
        workspace_name=data.get("workspace_name", ""),
        compartment_id=data.get("compartment_id", ""),
    )
    for attr in ("projects","folders","data_flows","pipelines","tasks","connections","data_assets"):
        setattr(inv, attr, data.get(attr) or [])
    return inv


def build_inventory(workspace_id: str, compartment_id: str,
                    client: Optional[OCIDataIntegrationClient] = None) -> WorkspaceInventory:
    """Enumerate everything we care about in a DI workspace."""
    c = client or OCIDataIntegrationClient()
    ws = c.get_workspace(workspace_id)
    inv = WorkspaceInventory(
        workspace_id=workspace_id,
        workspace_name=getattr(ws, "display_name", None) or getattr(ws, "name", "") or "",
        compartment_id=compartment_id,
    )
    inv.projects    = [_summ(p) for p in c.list_projects(workspace_id)]
    inv.folders     = [_summ(f) for f in c.list_folders(workspace_id)]
    inv.data_flows  = [_summ(d) for d in c.list_data_flows(workspace_id)]
    inv.pipelines   = [_summ(p) for p in c.list_pipelines(workspace_id)]
    inv.tasks       = [_summ(t) for t in c.list_tasks(workspace_id)]
    # Data assets first, then connections per asset
    raw_assets = c.list_data_assets(workspace_id)
    inv.data_assets = [_summ(a) for a in raw_assets]
    conns = []
    for asset in raw_assets:
        asset_key = getattr(asset, "key", None)
        if not asset_key:
            continue
        for conn in c.list_connections(workspace_id, asset_key):
            d = _summ(conn)
            d["data_asset_key"] = asset_key
            conns.append(d)
    inv.connections = conns
    return inv
