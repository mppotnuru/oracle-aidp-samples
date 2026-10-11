"""Thin SDK wrapper for OCI Data Integration — the only module that talks to DI."""
from __future__ import annotations
from functools import cached_property
from typing import Iterator, Optional

import oci
from oci.data_integration import DataIntegrationClient
from oci.pagination import list_call_get_all_results

from .._env import OCI_PROFILE, OCI_REGION


class OCIDataIntegrationClient:
    """Narrow surface over oci.data_integration. All inventory modules go through here."""

    def __init__(self, profile: str = OCI_PROFILE, region: Optional[str] = None):
        self._config = oci.config.from_file(profile_name=profile)
        if region:
            self._config["region"] = region
        else:
            self._config.setdefault("region", OCI_REGION)

    @cached_property
    def _c(self) -> DataIntegrationClient:
        return DataIntegrationClient(self._config)

    # -- workspace / project ---------------------------------------------------
    def list_workspaces(self, compartment_id: str) -> list:
        return list_call_get_all_results(
            self._c.list_workspaces, compartment_id=compartment_id
        ).data

    def get_workspace(self, workspace_id: str):
        return self._c.get_workspace(workspace_id).data

    def list_projects(self, workspace_id: str) -> list:
        return list_call_get_all_results(
            self._c.list_projects, workspace_id=workspace_id
        ).data

    def list_folders(self, workspace_id: str, project_key: Optional[str] = None) -> list:
        kwargs = {"workspace_id": workspace_id}
        if project_key:
            kwargs["aggregator_key"] = project_key
        return list_call_get_all_results(self._c.list_folders, **kwargs).data

    # -- data flows ------------------------------------------------------------
    def list_data_flows(self, workspace_id: str,
                        folder_key: Optional[str] = None,
                        project_key: Optional[str] = None) -> list:
        kwargs = {"workspace_id": workspace_id}
        if folder_key:  kwargs["folder_id"] = folder_key
        if project_key: kwargs["aggregator_key"] = project_key
        return list_call_get_all_results(self._c.list_data_flows, **kwargs).data

    def get_data_flow(self, workspace_id: str, data_flow_key: str):
        return self._c.get_data_flow(workspace_id, data_flow_key, expand_references="all").data

    # -- pipelines + tasks -----------------------------------------------------
    def list_pipelines(self, workspace_id: str,
                       folder_key: Optional[str] = None,
                       project_key: Optional[str] = None) -> list:
        kwargs = {"workspace_id": workspace_id}
        if folder_key:  kwargs["folder_id"] = folder_key
        if project_key: kwargs["aggregator_key"] = project_key
        return list_call_get_all_results(self._c.list_pipelines, **kwargs).data

    def get_pipeline(self, workspace_id: str, pipeline_key: str):
        return self._c.get_pipeline(workspace_id, pipeline_key).data

    def list_tasks(self, workspace_id: str,
                   folder_key: Optional[str] = None) -> list:
        kwargs = {"workspace_id": workspace_id}
        if folder_key: kwargs["folder_id"] = folder_key
        return list_call_get_all_results(self._c.list_tasks, **kwargs).data

    # -- data assets + their connections ---------------------------------------
    def list_data_assets(self, workspace_id: str) -> list:
        return list_call_get_all_results(
            self._c.list_data_assets, workspace_id=workspace_id
        ).data

    def list_connections(self, workspace_id: str, data_asset_key: str) -> list:
        """Connections are scoped to a data asset — iterate assets to collect all."""
        return list_call_get_all_results(
            self._c.list_connections,
            workspace_id=workspace_id,
            data_asset_key=data_asset_key,
        ).data
