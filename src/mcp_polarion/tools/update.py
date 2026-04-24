"""Update tools (8)."""

from __future__ import annotations

import datetime
import json
from typing import Optional

from mcp_polarion._app import mcp, _err
from mcp_polarion.pylero_client import default_project

from pylero.base_polarion import BasePolarion
from pylero.document import Document
from pylero.plan import Plan
from pylero.test_run import TestRun
from pylero.test_step import TestStep
from pylero.text import Text
from pylero.work_item import _WorkItem, TestCase


@mcp.tool()
def update_work_item(
    work_item_id: str,
    project_id: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    priority: Optional[str] = None,
    custom_fields: Optional[str] = None,
) -> str:
    """Update a work item's fields.

    Args:
        work_item_id: Work item ID.
        project_id: Polarion project ID.
        title: New title.
        description: New description.
        status: New status.
        severity: New severity.
        priority: New priority.
        custom_fields: JSON string of custom field updates
                       (e.g. '{"caseimportance": "critical"}').
    """
    try:
        pid = project_id or default_project()
        wi = _WorkItem(project_id=pid, work_item_id=work_item_id)
        if title:
            wi.title = title
        if description:
            wi.description = description
        if status:
            wi.status = status
        if severity:
            wi.severity = severity
        if priority:
            wi.priority = priority
        if custom_fields:
            for k, v in json.loads(custom_fields).items():
                wi.set_custom_field(k, v)
        wi.update()
        return json.dumps({"status": "updated", "work_item_id": work_item_id})
    except Exception as e:
        return _err(e)


@mcp.tool()
def set_test_steps(
    work_item_id: str,
    steps_json: str,
    project_id: Optional[str] = None,
) -> str:
    """Write/replace test steps on a test case.

    Args:
        work_item_id: Test case work item ID.
        steps_json: JSON array of steps, each with "step" and "expectedResult"
                    (e.g. '[{"step": "Do X", "expectedResult": "Y happens"}]').
        project_id: Polarion project ID.
    """
    try:
        pid = project_id or default_project()
        tc = TestCase(project_id=pid, work_item_id=work_item_id)
        steps_data = json.loads(steps_json)

        step_objects = []
        for s in steps_data:
            step = TestStep()
            step.values = [
                Text(content=s.get("step", "")),
                Text(content=s.get("expectedResult", "")),
            ]
            step_objects.append(step)
        tc.set_test_steps(step_objects)
        return json.dumps({
            "status": "updated",
            "work_item_id": work_item_id,
            "step_count": len(step_objects),
        })
    except Exception as e:
        return _err(e)


@mcp.tool()
def record_test_result(
    test_run_id: str,
    test_case_id: str,
    result: str,
    project_id: Optional[str] = None,
    comment: Optional[str] = None,
    executed_by: Optional[str] = None,
    duration: Optional[float] = None,
) -> str:
    """Add a test result to a test run.

    Args:
        test_run_id: Test run ID.
        test_case_id: Test case work item ID.
        result: Result value (passed, failed, blocked).
        project_id: Polarion project ID.
        comment: Optional comment.
        executed_by: User ID who executed (defaults to current user).
        duration: Execution duration in seconds.
    """
    try:
        pid = project_id or default_project()
        tr = TestRun(test_run_id=test_run_id, project_id=pid)
        tr.add_test_record_by_fields(
            test_case_id=test_case_id,
            test_result=result,
            test_comment=comment or "",
            executed_by=executed_by or BasePolarion.logged_in_user_id,
            executed=datetime.datetime.now(),
            duration=duration if duration is not None else 0.0,
        )
        return json.dumps({
            "status": "recorded",
            "test_run_id": test_run_id,
            "test_case_id": test_case_id,
            "result": result,
        })
    except Exception as e:
        return _err(e)


@mcp.tool()
def update_test_record(
    test_run_id: str,
    test_case_id: str,
    result: str,
    project_id: Optional[str] = None,
    comment: Optional[str] = None,
    executed_by: Optional[str] = None,
    duration: Optional[float] = None,
) -> str:
    """Update an existing test record in a test run.

    Args:
        test_run_id: Test run ID.
        test_case_id: Test case work item ID.
        result: New result (passed, failed, blocked).
        project_id: Polarion project ID.
        comment: Updated comment.
        executed_by: User who executed.
        duration: Duration in seconds.
    """
    try:
        pid = project_id or default_project()
        tr = TestRun(test_run_id=test_run_id, project_id=pid)
        tr.update_test_record_by_fields(
            test_case_id=test_case_id,
            test_result=result,
            test_comment=comment or "",
            executed_by=executed_by or BasePolarion.logged_in_user_id,
            executed=datetime.datetime.now(),
            duration=duration if duration is not None else 0.0,
        )
        return json.dumps({
            "status": "updated",
            "test_run_id": test_run_id,
            "test_case_id": test_case_id,
            "result": result,
        })
    except Exception as e:
        return _err(e)


@mcp.tool()
def perform_workflow_action(
    action_id: str,
    work_item_id: Optional[str] = None,
    test_run_id: Optional[str] = None,
    project_id: Optional[str] = None,
) -> str:
    """Transition a work item or test run to a new workflow state.

    Use get_workflow_actions first to discover available transitions.
    Pass the numeric action_id from the action list (e.g. "3", "4").

    Args:
        action_id: The numeric workflow action ID (from get_workflow_actions).
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
        try:
            aid = int(action_id)
        except ValueError:
            aid = action_id
        entity.perform_workflow_action(aid)
        return json.dumps({"status": "transitioned", "entity_id": entity_id, "action": action_id})
    except Exception as e:
        return _err(e)


@mcp.tool()
def update_document(
    space_id: str,
    document_name: str,
    project_id: Optional[str] = None,
    title: Optional[str] = None,
    home_page_content: Optional[str] = None,
) -> str:
    """Update a document's title or content.

    Args:
        space_id: Document space.
        document_name: Document name.
        project_id: Polarion project ID.
        title: New title.
        home_page_content: New HTML content.
    """
    try:
        pid = project_id or default_project()
        doc = Document(project_id=pid, doc_with_space=f"{space_id}/{document_name}")
        if title:
            doc.title = title
        if home_page_content:
            doc.home_page_content = home_page_content
        doc.update()
        return json.dumps({"status": "updated", "document_id": doc.document_id})
    except Exception as e:
        return _err(e)


@mcp.tool()
def update_test_run(
    test_run_id: str,
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    assignee: Optional[str] = None,
    plannedin: Optional[str] = None,
    description: Optional[str] = None,
) -> str:
    """Update a test run's fields.

    Args:
        test_run_id: Test run ID.
        project_id: Polarion project ID.
        status: New status.
        assignee: New assignee user ID.
        plannedin: Plan ID.
        description: New description.
    """
    try:
        pid = project_id or default_project()
        tr = TestRun(test_run_id=test_run_id, project_id=pid)
        if status:
            tr.status = status
        if assignee:
            tr.assignee = assignee
        if plannedin:
            tr.plannedin = plannedin
        if description:
            tr.description = description
        tr.update()
        return json.dumps({"status": "updated", "test_run_id": test_run_id})
    except Exception as e:
        return _err(e)


@mcp.tool()
def update_plan(
    plan_id: str,
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    capacity: Optional[str] = None,
    start_date: Optional[str] = None,
    due_date: Optional[str] = None,
) -> str:
    """Update a plan's fields.

    Args:
        plan_id: Plan ID.
        project_id: Polarion project ID.
        status: New status.
        capacity: Capacity string.
        start_date: Start date (YYYY-MM-DD).
        due_date: Due date (YYYY-MM-DD).
    """
    try:
        pid = project_id or default_project()
        plan = Plan(plan_id=plan_id, project_id=pid)
        if status:
            plan.status = status
        if capacity:
            plan.capacity = capacity
        if start_date:
            plan.start_date = start_date
        if due_date:
            plan.due_date = due_date
        plan.update()
        return json.dumps({"status": "updated", "plan_id": plan_id})
    except Exception as e:
        return _err(e)
