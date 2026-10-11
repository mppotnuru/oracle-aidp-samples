"""Shared env/config for the plugin."""
import os

OCI_PROFILE  = os.environ.get("OCI_CONFIG_PROFILE", "OASEFDE")
OCI_REGION   = os.environ.get("OCI_REGION", "us-ashburn-1")
COMPARTMENT  = os.environ.get("COMPARTMENT_OCID", "")
WORKSPACE_ID = os.environ.get("DI_WORKSPACE_OCID", "")

AIDP_WORKBENCH_OCID = os.environ.get("AIDP_WORKBENCH_OCID", "")
AIDP_WORKSPACE_ID   = os.environ.get("AIDP_WORKSPACE_ID", "")

DEFAULT_OUTPUT_DIR = os.environ.get("OCI_DI_AIDP_OUT", "./out")
