"""Link / Relate / Manage tools (6)."""

from __future__ import annotations

import json
from typing import Optional

from mcp_polarion._app import mcp, _err
from mcp_polarion.pylero_client import default_project, _safe, _strip_html

from pylero.work_item import _WorkItem


@mcp.tool()
def manage_links(
    work_item_id: str,
    target_work_item_id: str,
    role: str,
    action: str = "add",
    project_id: Optional[str] = None,
) -> str:
    """Add or remove a typed link between two work items.

    Common roles: verifies, parent, relates_to, depends_on, duplicates.

    Args:
        work_item_id: Source work item ID.
        target_work_item_id: Target work item ID.
        role: Link role.
        action: "add" or "remove".
        project_id: Polarion project ID.
    """
    try:
        pid = project_id or default_project()
        wi = _WorkItem(project_id=pid, work_item_id=work_item_id)
        if action == "add":
            wi.add_linked_item(target_work_item_id, role)
            return json.dumps({"status": "linked", "source": work_item_id, "target": target_work_item_id, "role": role})
        elif action == "remove":
            wi.remove_linked_item(target_work_item_id, role)
            return json.dumps({"status": "unlinked", "source": work_item_id, "target": target_work_item_id, "role": role})
        else:
            return json.dumps({"status": "error", "detail": f"Unknown action: {action}"})
    except Exception as e:
        return _err(e)


@mcp.tool()
def manage_assignees(
    work_item_id: str,
    user_id: Optional[str] = None,
    action: str = "list",
    project_id: Optional[str] = None,
) -> str:
    """Add, remove, or list assignees on a work item.

    Args:
        work_item_id: Work item ID.
        user_id: User ID to add/remove. Required for add/remove actions.
        action: "add", "remove", or "list".
        project_id: Polarion project ID.
    """
    try:
        pid = project_id or default_project()
        wi = _WorkItem(project_id=pid, work_item_id=work_item_id)
        if action == "add" and user_id:
            wi.add_assignee(user_id)
            wi.update()
            return json.dumps({"status": "assigned", "user": user_id})
        elif action == "remove" and user_id:
            wi.remove_assignee(user_id)
            wi.update()
            return json.dumps({"status": "unassigned", "user": user_id})
        elif action == "list":
            assignees = getattr(wi, "assignee", []) or []
            if not isinstance(assignees, list):
                assignees = [assignees]
            return json.dumps({"assignees": [_safe(a) for a in assignees]})
        else:
            return json.dumps({"status": "error", "detail": "Action must be add/remove/list. user_id required for add/remove."})
    except Exception as e:
        return _err(e)


@mcp.tool()
def manage_attachments(
    work_item_id: str,
    action: str = "list",
    file_path: Optional[str] = None,
    title: Optional[str] = None,
    attachment_id: Optional[str] = None,
    project_id: Optional[str] = None,
) -> str:
    """Add, list, or delete attachments on a work item.

    Args:
        work_item_id: Work item ID.
        action: "add", "list", or "delete".
        file_path: Local file path (required for add).
        title: Attachment title (for add).
        attachment_id: Attachment ID (required for delete).
        project_id: Polarion project ID.
    """
    try:
        pid = project_id or default_project()
        wi = _WorkItem(project_id=pid, work_item_id=work_item_id)
        if action == "add" and file_path:
            wi.create_attachment(file_path, title or "")
            return json.dumps({"status": "attached", "file": file_path})
        elif action == "delete" and attachment_id:
            wi.delete_attachment(attachment_id)
            return json.dumps({"status": "deleted", "attachment_id": attachment_id})
        elif action == "list":
            attachments = getattr(wi, "attachments", []) or []
            items = [{"id": getattr(a, "attachment_id", ""), "file_name": getattr(a, "file_name", ""), "title": getattr(a, "title", "")} for a in attachments]
            return json.dumps({"attachments": items})
        else:
            return json.dumps({"status": "error", "detail": "Action must be add/list/delete with required params."})
    except Exception as e:
        return _err(e)


@mcp.tool()
def manage_comments(
    work_item_id: str,
    action: str = "list",
    content: Optional[str] = None,
    project_id: Optional[str] = None,
) -> str:
    """Create or list comments on a work item.

    Args:
        work_item_id: Work item ID.
        action: "add" or "list".
        content: Comment text (required for add).
        project_id: Polarion project ID.
    """
    try:
        pid = project_id or default_project()
        wi = _WorkItem(project_id=pid, work_item_id=work_item_id)
        if action == "add" and content:
            wi.create_comment(content)
            return json.dumps({"status": "commented", "work_item_id": work_item_id})
        elif action == "list":
            comments = getattr(wi, "comments", []) or []
            items = [{"author": _safe(getattr(c, "author", None)), "created": _safe(getattr(c, "created", None)), "text": _strip_html(getattr(c, "text", None))} for c in comments]
            return json.dumps({"comments": items})
        else:
            return json.dumps({"status": "error", "detail": "Action must be add/list. content required for add."})
    except Exception as e:
        return _err(e)


@mcp.tool()
def manage_approvals(
    work_item_id: str,
    action: str = "list",
    user_id: Optional[str] = None,
    approval_status: Optional[str] = None,
    project_id: Optional[str] = None,
) -> str:
    """Manage approvals on a work item.

    Args:
        work_item_id: Work item ID.
        action: "add_approvee", "set_status", or "list".
        user_id: User ID (required for add_approvee and set_status).
        approval_status: "approved", "disapproved", or "waiting"
                         (required for set_status).
        project_id: Polarion project ID.
    """
    try:
        pid = project_id or default_project()
        wi = _WorkItem(project_id=pid, work_item_id=work_item_id)
        if action == "add_approvee" and user_id:
            wi.add_approvee(user_id)
            return json.dumps({"status": "approvee_added", "user": user_id})
        elif action == "set_status" and user_id and approval_status:
            wi.edit_approval(user_id, approval_status)
            return json.dumps({"status": "approval_set", "user": user_id, "approval_status": approval_status})
        elif action == "list":
            approvals = getattr(wi, "approvals", []) or []
            items = [_safe(a) for a in approvals]
            return json.dumps({"approvals": items})
        else:
            return json.dumps({"status": "error", "detail": "Action must be add_approvee/set_status/list."})
    except Exception as e:
        return _err(e)


@mcp.tool()
def manage_hyperlinks(
    work_item_id: str,
    url: str,
    action: str = "add",
    role: str = "reference",
    project_id: Optional[str] = None,
) -> str:
    """Add or remove an external hyperlink on a work item.

    Args:
        work_item_id: Work item ID.
        url: The URL to link.
        action: "add" or "remove".
        role: Link role (default "reference" for external reference).
        project_id: Polarion project ID.
    """
    try:
        pid = project_id or default_project()
        wi = _WorkItem(project_id=pid, work_item_id=work_item_id)
        if action == "add":
            wi.add_hyperlink(url, role)
            return json.dumps({"status": "hyperlink_added", "url": url})
        elif action == "remove":
            wi.remove_hyperlink(url)
            return json.dumps({"status": "hyperlink_removed", "url": url})
        else:
            return json.dumps({"status": "error", "detail": "Action must be add or remove."})
    except Exception as e:
        return _err(e)
