"""Setup / Discovery tools (4)."""

from __future__ import annotations

import json
from typing import Optional

from mcp_polarion._app import mcp, _err
from mcp_polarion.pylero_client import default_project

from pylero.project import Project
from pylero.work_item import _WorkItem


@mcp.tool()
def test_connection(project_id: Optional[str] = None) -> str:
    """Verify pylero auth and project access.

    Args:
        project_id: Polarion project ID (defaults to POLARION_PROJECT).
    """
    try:
        pid = project_id or default_project()
        p = Project(project_id=pid)
        return json.dumps({
            "status": "connected",
            "project_id": p.project_id,
            "project_name": p.name,
        })
    except Exception as e:
        return _err(e)


@mcp.tool()
def get_enum_options(
    field_id: str,
    project_id: Optional[str] = None,
) -> str:
    """List valid values for a work-item field.

    Args:
        field_id: Field name (e.g. "status", "severity", "type",
                  "priority", "caseimportance").
        project_id: Polarion project ID.
    """
    try:
        pid = project_id or default_project()
        wi = _WorkItem(project_id=pid)
        values = wi.get_valid_field_values(field_id)
        options = [str(v) for v in values] if values else []
        return json.dumps({"field": field_id, "options": options})
    except Exception as e:
        return _err(e)


@mcp.tool()
def get_custom_fields(
    work_item_type: str,
    project_id: Optional[str] = None,
) -> str:
    """List required and optional custom fields for a work item type.

    Args:
        work_item_type: Type name (e.g. "TestCase", "Requirement").
                        Use get_work_item_types to discover available types.
        project_id: Polarion project ID.
    """
    try:
        pid = project_id or default_project()
        wi_type = work_item_type.lower()
        fields = _WorkItem.get_defined_custom_field_types(pid, wi_type)
        result = []
        for cf in fields:
            entry: dict = {
                "id": str(getattr(cf, "cft_id", "")),
                "name": str(getattr(cf, "name", "")),
                "type": str(getattr(cf, "type", "")),
                "required": getattr(cf, "required", False),
                "multi": getattr(cf, "multi", False),
            }
            desc = getattr(cf, "description", None)
            if desc:
                entry["description"] = str(desc)
            dep = getattr(cf, "depends_on", None)
            if dep:
                entry["depends_on"] = str(dep)
            result.append(entry)
        return json.dumps({"type": work_item_type, "fields": result})
    except Exception as e:
        return _err(e)


@mcp.tool()
def get_work_item_types(project_id: Optional[str] = None) -> str:
    """List all work item types defined in this Polarion installation.

    Args:
        project_id: Polarion project ID.
    """
    try:
        types = _WorkItem.get_defined_work_item_types()
        return json.dumps({"types": [t.__name__ for t in types]})
    except Exception as e:
        return _err(e)
