"""Create tools (5)."""

from __future__ import annotations

import json
from typing import Optional

from mcp_polarion._app import mcp, _err
from mcp_polarion._custom_fields import resolve_local_name, type_specific_class
from mcp_polarion.pylero_client import default_project

from pylero.document import Document
from pylero.plan import Plan
from pylero.test_run import TestRun
from pylero.work_item import _WorkItem


@mcp.tool()
def create_work_item(
    title: str,
    work_item_type: str,
    project_id: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    priority: Optional[str] = None,
    custom_fields: Optional[str] = None,
) -> str:
    """Create a new work item. Use get_custom_fields first to discover required fields.

    Args:
        title: Work item title.
        work_item_type: Type (e.g. "testcase", "defect", "requirement").
        project_id: Polarion project ID.
        description: Description text.
        status: Initial status.
        severity: Severity level.
        priority: Priority level.
        custom_fields: JSON string of additional kwargs
                       (e.g. '{"caseimportance": "high"}').
    """
    try:
        pid = project_id or default_project()
        kwargs: dict = {}
        if severity:
            kwargs["severity"] = severity
        if priority:
            kwargs["priority"] = priority
        if custom_fields:
            # Custom fields must go through the type-specific subclass: the base
            # _WorkItem.create() would set them as dead instance attributes that
            # the SOAP layer silently drops. The type-specific create() also
            # validates required custom fields. Resolve each id to its pylero
            # snake_cased property name so the property setter handles it.
            cls = type_specific_class(work_item_type)
            cls.get_custom_fields(pid)  # populate _cls_suds_map for name resolution
            for field_id, value in json.loads(custom_fields).items():
                kwargs[resolve_local_name(cls, field_id)] = value
            wi = cls.create(pid, title, description or "", status or "open", **kwargs)
        else:
            wi = _WorkItem.create(
                pid, work_item_type, title,
                description or "", status or "open", **kwargs,
            )
        return json.dumps({
            "status": "created",
            "work_item_id": wi.work_item_id,
            "type": work_item_type,
            "title": title,
        })
    except Exception as e:
        return _err(e)


@mcp.tool()
def create_test_run(
    test_run_id: str,
    template_id: str,
    project_id: Optional[str] = None,
    title: Optional[str] = None,
    assignee: Optional[str] = None,
    plannedin: Optional[str] = None,
    status: Optional[str] = None,
    description: Optional[str] = None,
) -> str:
    """Create a test run from a template.

    Args:
        test_run_id: Unique ID for the new test run.
        template_id: Template ID to base the run on.
        project_id: Polarion project ID.
        title: Optional title.
        assignee: Assignee user ID.
        plannedin: Plan ID to associate with.
        status: Initial status (e.g. "notrun").
        description: Description text.
    """
    try:
        pid = project_id or default_project()
        kwargs: dict = {}
        if assignee:
            kwargs["assignee"] = assignee
        if plannedin:
            kwargs["plannedin"] = plannedin
        if status:
            kwargs["status"] = status
        if description:
            kwargs["description"] = description
        tr = TestRun.create(pid, test_run_id, template_id, **kwargs)
        if title:
            tr.title = title
            tr.update()
        return json.dumps({
            "status": "created",
            "test_run_id": tr.test_run_id,
            "template": template_id,
        })
    except Exception as e:
        return _err(e)


@mcp.tool()
def create_test_run_template(
    template_id: str,
    project_id: Optional[str] = None,
    select_test_cases_by: str = "staticQueryResult",
    query: Optional[str] = None,
    doc_with_space: Optional[str] = None,
    parent_template_id: str = "Empty",
) -> str:
    """Create a test run template defining how test cases are selected.

    Selection modes: staticQueryResult, dynamicQueryResult, staticLiveDoc,
    dynamicLiveDoc, manualSelection, automatedProcess.

    Args:
        template_id: Unique ID for the template.
        project_id: Polarion project ID.
        select_test_cases_by: Selection mode.
        query: Lucene query (for query-based selection).
        doc_with_space: Document path (for LiveDoc selection, e.g. "Testing/spec").
        parent_template_id: Parent template to inherit from.
    """
    try:
        pid = project_id or default_project()
        kwargs: dict = {
            "select_test_cases_by": select_test_cases_by,
            "parent_template_id": parent_template_id,
        }
        if query:
            kwargs["query"] = query
        if doc_with_space:
            kwargs["doc_with_space"] = doc_with_space
        template = TestRun.create_template(pid, template_id, **kwargs)
        return json.dumps({
            "status": "created",
            "template_id": template.test_run_id,
            "select_test_cases_by": select_test_cases_by,
        })
    except Exception as e:
        return _err(e)


@mcp.tool()
def create_document(
    space_id: str,
    document_name: str,
    title: str,
    project_id: Optional[str] = None,
    document_type: Optional[str] = None,
    allowed_wi_types: Optional[str] = None,
    home_page_content: Optional[str] = None,
) -> str:
    """Create a new document in a space.

    Args:
        space_id: Space name (e.g. "Testing", "_default").
        document_name: Internal name for the document.
        title: Display title.
        project_id: Polarion project ID.
        document_type: Type (e.g. "testspecification").
        allowed_wi_types: JSON array of allowed work item types
                          (e.g. '["testcase"]').
        home_page_content: Initial HTML content.
    """
    try:
        pid = project_id or default_project()
        wi_types = json.loads(allowed_wi_types) if allowed_wi_types else ["testcase"]
        doc_type = document_type or "generic"
        kwargs: dict = {}
        if home_page_content:
            kwargs["home_page_content"] = home_page_content
        doc = Document.create(
            pid, space_id, document_name, title, wi_types, doc_type, **kwargs,
        )
        return json.dumps({
            "status": "created",
            "document_id": doc.document_id,
            "title": title,
            "space": space_id,
        })
    except Exception as e:
        return _err(e)


@mcp.tool()
def create_plan(
    plan_id: str,
    name: str,
    project_id: Optional[str] = None,
    parent_id: Optional[str] = None,
    template_id: Optional[str] = None,
) -> str:
    """Create a new plan.

    Args:
        plan_id: Unique plan ID.
        name: Display name.
        project_id: Polarion project ID.
        parent_id: Parent plan ID (for nesting).
        template_id: Plan template ID (e.g. "iteration").
    """
    try:
        pid = project_id or default_project()
        plan = Plan.create(plan_id, name, pid, parent_id, template_id or "iteration")
        return json.dumps({
            "status": "created",
            "plan_id": plan.plan_id,
            "name": name,
        })
    except Exception as e:
        return _err(e)
