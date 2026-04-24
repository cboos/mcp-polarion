"""Delete tools (3)."""

from __future__ import annotations

import json
from typing import Optional

from mcp_polarion._app import mcp, _err
from mcp_polarion.pylero_client import default_project

from pylero.base_polarion import BasePolarion
from pylero.document import Document
from pylero.plan import Plan
from pylero.work_item import _WorkItem


@mcp.tool()
def delete_work_item(
    work_item_id: str,
    project_id: Optional[str] = None,
) -> str:
    """Permanently delete a work item. USE WITH CAUTION.

    Args:
        work_item_id: Work item ID to delete.
        project_id: Polarion project ID.
    """
    try:
        pid = project_id or default_project()
        wi = _WorkItem(project_id=pid, work_item_id=work_item_id)
        uri = wi.uri
        BasePolarion.session.tracker_client.service.deleteWorkItem(uri)
        return json.dumps({"status": "deleted", "work_item_id": work_item_id})
    except Exception as e:
        return _err(e)


@mcp.tool()
def delete_document(
    space_id: str,
    document_name: str,
    project_id: Optional[str] = None,
) -> str:
    """Permanently delete a document. USE WITH CAUTION.

    Args:
        space_id: Document space.
        document_name: Document name.
        project_id: Polarion project ID.
    """
    try:
        pid = project_id or default_project()
        doc = Document(project_id=pid, doc_with_space=f"{space_id}/{document_name}")
        doc.delete()
        return json.dumps({"status": "deleted", "space": space_id, "document_name": document_name})
    except Exception as e:
        return _err(e)


@mcp.tool()
def delete_plan(
    plan_id: str,
    project_id: Optional[str] = None,
) -> str:
    """Permanently delete a plan. USE WITH CAUTION.

    Args:
        plan_id: Plan ID to delete.
        project_id: Polarion project ID.
    """
    try:
        pid = project_id or default_project()
        Plan.delete_plans(pid, [plan_id])
        return json.dumps({"status": "deleted", "plan_id": plan_id})
    except Exception as e:
        return _err(e)
