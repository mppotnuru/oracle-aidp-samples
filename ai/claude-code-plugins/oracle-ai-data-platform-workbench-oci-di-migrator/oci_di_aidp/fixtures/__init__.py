"""Bundled fixture manifests — offline/demo mode for the migrator."""
from __future__ import annotations
import re
from importlib.resources import files
from pathlib import Path

_FIXTURE_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


def fixture_path(name: str) -> Path:
    """Resolve a bundled fixture by name (no traversal allowed)."""
    if not _FIXTURE_NAME_RE.match(name):
        raise ValueError("invalid fixture name; use 1-64 letters/digits/_/-")
    resource = files("oci_di_aidp.fixtures").joinpath(f"{name}-manifest.json")
    if not resource.is_file():
        raise ValueError(f"bundled fixture not found: {name}")
    return Path(str(resource))
