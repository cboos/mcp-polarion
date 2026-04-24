"""Read / Inspect tools (12)."""

from __future__ import annotations

import json
import re
from typing import Optional

from mcp_polarion._app import mcp, _err
from mcp_polarion.pylero_client import (
    default_project,
    serialize_document,
    serialize_linked_item,
    serialize_test_record,
    serialize_test_run,
    serialize_work_item,
    _safe,
    _strip_html,
)

from pylero.document import Document
from pylero.test_run import TestRun
from pylero.work_item import _WorkItem, TestCase


@mcp.tool()
def get_work_item(
    work_item_id: str,
    project_id: Optional[str] = None,
) -> str:
    """Get a work item by ID with all fields.

    Args:
        work_item_id: Work item ID (e.g. "PROJ-1234").
        project_id: Polarion project ID.
    """
    try:
        pid = project_id or default_project()
        wi = _WorkItem(project_id=pid, work_item_id=work_item_id)
        return json.dumps(serialize_work_item(wi))
    except Exception as e:
        return _err(e)


@mcp.tool()
def get_document(
    space_id: str,
    document_name: str,
    project_id: Optional[str] = None,
) -> str:
    """Get a document by space and name.

    Args:
        space_id: Document space (e.g. "Testing", "_default").
        document_name: Internal document name.
        project_id: Polarion project ID.
    """
    try:
        pid = project_id or default_project()
        doc = Document(project_id=pid, doc_with_space=f"{space_id}/{document_name}")
        result = serialize_document(doc)
        content = getattr(doc, "home_page_content", "")
        if content:
            wi_ids = list(dict.fromkeys(re.findall(r"id=([A-Z]+-\d+)", str(content))))
            result["embedded_work_item_ids"] = wi_ids
        return json.dumps(result)
    except Exception as e:
        return _err(e)


@mcp.tool()
def get_test_run(
    test_run_id: str,
    project_id: Optional[str] = None,
) -> str:
    """Get a test run by ID.

    Args:
        test_run_id: Test run ID.
        project_id: Polarion project ID.
    """
    try:
        pid = project_id or default_project()
        tr = TestRun(test_run_id=test_run_id, project_id=pid)
        result = serialize_test_run(tr)
        records = getattr(tr, "records", []) or []
        passed = sum(1 for r in records if getattr(r, "result", "") == "passed")
        failed = sum(1 for r in records if getattr(r, "result", "") == "failed")
        blocked = sum(1 for r in records if getattr(r, "result", "") == "blocked")
        result["statistics"] = {
            "total": len(records), "passed": passed,
            "failed": failed, "blocked": blocked,
        }
        return json.dumps(result)
    except Exception as e:
        return _err(e)


@mcp.tool()
def get_test_records(
    test_run_id: str,
    project_id: Optional[str] = None,
) -> str:
    """List test records (individual results) within a test run.

    Args:
        test_run_id: Test run ID.
        project_id: Polarion project ID.
    """
    try:
        pid = project_id or default_project()
        tr = TestRun(test_run_id=test_run_id, project_id=pid)
        records = getattr(tr, "records", []) or []
        items = [serialize_test_record(r) for r in records]
        return json.dumps({"test_run_id": test_run_id, "total": len(items), "records": items})
    except Exception as e:
        return _err(e)


@mcp.tool()
def get_linked_work_items(
    work_item_id: str,
    project_id: Optional[str] = None,
) -> str:
    """Get forward (outgoing) links from a work item.

    Args:
        work_item_id: Work item ID.
        project_id: Polarion project ID.
    """
    try:
        pid = project_id or default_project()
        wi = _WorkItem(project_id=pid, work_item_id=work_item_id)
        links = getattr(wi, "linked_work_items", []) or []
        items = [serialize_linked_item(lnk) for lnk in links]
        return json.dumps({"work_item_id": work_item_id, "linked_items": items})
    except Exception as e:
        return _err(e)


@mcp.tool()
def get_back_linked_work_items(
    work_item_id: str,
    project_id: Optional[str] = None,
) -> str:
    """Get reverse (incoming) links to a work item.

    Args:
        work_item_id: Work item ID.
        project_id: Polarion project ID.
    """
    try:
        pid = project_id or default_project()
        wi = _WorkItem(project_id=pid, work_item_id=work_item_id)
        links = getattr(wi, "linked_work_items_derived", []) or []
        items = [serialize_linked_item(lnk) for lnk in links]
        return json.dumps({"work_item_id": work_item_id, "back_linked_items": items})
    except Exception as e:
        return _err(e)


@mcp.tool()
def get_test_steps(
    work_item_id: str,
    project_id: Optional[str] = None,
) -> str:
    """Read test steps from a test case work item.

    Args:
        work_item_id: Test case work item ID.
        project_id: Polarion project ID.
    """
    try:
        pid = project_id or default_project()
        tc = TestCase(project_id=pid, work_item_id=work_item_id)
        steps_obj = tc.get_test_steps()
        result: list[dict] = []
        if steps_obj and getattr(steps_obj, "steps", None):
            raw_keys = getattr(steps_obj, "keys", ["step", "expectedResult"])
            keys = [getattr(k, "enum_id", str(k)) if hasattr(k, "enum_id") else str(k) for k in raw_keys]
            for step in steps_obj.steps:
                vals = getattr(step, "values", [])
                row = {}
                for i, key in enumerate(keys):
                    row[key] = _strip_html(vals[i]) if i < len(vals) else ""
                result.append(row)
        return json.dumps({"work_item_id": work_item_id, "steps": result})
    except Exception as e:
        return _err(e)


@mcp.tool()
def get_workflow_actions(
    work_item_id: Optional[str] = None,
    test_run_id: Optional[str] = None,
    project_id: Optional[str] = None,
) -> str:
    """Get available workflow transitions for a work item or test run.

    Args:
        work_item_id: Work item ID (provide this OR test_run_id).
        test_run_id: Test run ID (provide this OR work_item_id).
        project_id: Polarion project ID.
    """
    try:
        pid = project_id or default_project()
        if work_item_id:
            entity = _WorkItem(project_id=pid, work_item_id=work_item_id)
            entity_id = work_item_id
        elif test_run_id:
            entity = TestRun(test_run_id=test_run_id, project_id=pid)
            entity_id = test_run_id
        else:
            return json.dumps({"status": "error", "detail": "Provide work_item_id or test_run_id."})
        actions = entity.get_available_actions()
        items = []
        for a in actions:
            items.append({
                "action_id": getattr(a, "action_id", ""),
                "action_name": getattr(a, "action_name", ""),
                "native_action_id": getattr(a, "native_action_id", ""),
                "target_status": _safe(getattr(a, "target_status", None)),
            })
        return json.dumps({"entity_id": entity_id, "actions": items})
    except Exception as e:
        return _err(e)


@mcp.tool()
def get_revisions(
    work_item_id: str,
    project_id: Optional[str] = None,
) -> str:
    """Get revision/change history for a work item.

    Args:
        work_item_id: Work item ID.
        project_id: Polarion project ID.
    """
    try:
        pid = project_id or default_project()
        wi = _WorkItem(project_id=pid, work_item_id=work_item_id)
        revisions = wi.get_revisions(wi.uri)
        items = []
        for rev in revisions:
            items.append({
                "name": getattr(rev, "name", ""),
                "author": _safe(getattr(rev, "author", None)),
                "created": _safe(getattr(rev, "created", None)),
                "message": getattr(rev, "message", ""),
            })
        return json.dumps({"work_item_id": work_item_id, "revisions": items})
    except Exception as e:
        return _err(e)


@mcp.tool()
def get_comments(
    work_item_id: str,
    project_id: Optional[str] = None,
) -> str:
    """List comments on a work item.

    Args:
        work_item_id: Work item ID.
        project_id: Polarion project ID.
    """
    try:
        pid = project_id or default_project()
        wi = _WorkItem(project_id=pid, work_item_id=work_item_id)
        comments = getattr(wi, "comments", []) or []
        items = []
        for c in comments:
            items.append({
                "author": _safe(getattr(c, "author", None)),
                "created": _safe(getattr(c, "created", None)),
                "text": _strip_html(getattr(c, "text", None)),
            })
        return json.dumps({"work_item_id": work_item_id, "comments": items})
    except Exception as e:
        return _err(e)


@mcp.tool()
def get_attachments(
    work_item_id: str,
    project_id: Optional[str] = None,
) -> str:
    """List attachments on a work item.

    Args:
        work_item_id: Work item ID.
        project_id: Polarion project ID.
    """
    try:
        pid = project_id or default_project()
        wi = _WorkItem(project_id=pid, work_item_id=work_item_id)
        attachments = getattr(wi, "attachments", []) or []
        items = []
        for att in attachments:
            items.append({
                "id": getattr(att, "attachment_id", ""),
                "file_name": getattr(att, "file_name", ""),
                "title": getattr(att, "title", ""),
            })
        return json.dumps({"work_item_id": work_item_id, "attachments": items})
    except Exception as e:
        return _err(e)


@mcp.tool()
def which_test_runs(
    work_item_id: str,
    project_id: Optional[str] = None,
) -> str:
    """Find all test runs that contain a given test case.

    Args:
        work_item_id: Test case work item ID.
        project_id: Polarion project ID.
    """
    try:
        pid = project_id or default_project()
        tc = TestCase(project_id=pid, work_item_id=work_item_id)
        runs = tc.which_test_runs()
        items = [{"test_run_id": getattr(r, "test_run_id", str(r))} for r in runs]
        return json.dumps({"work_item_id": work_item_id, "test_runs": items})
    except Exception as e:
        return _err(e)
