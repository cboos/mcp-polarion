"""Query / Search tools (4)."""

from __future__ import annotations

import json
from typing import Optional

from mcp_polarion._app import mcp, _err
from mcp_polarion.pylero_client import (
    default_project,
    serialize_document,
    serialize_plan,
    serialize_test_run,
    serialize_work_item,
)

from pylero.document import Document
from pylero.plan import Plan
from pylero.test_run import TestRun
from pylero.work_item import _WorkItem


@mcp.tool()
def search_work_items(
    query: str,
    fields: str = "work_item_id,title,type,status",
    sort: Optional[str] = None,
    limit: int = 50,
    is_sql: bool = False,
    project_id: Optional[str] = None,
) -> str:
    """Search work items with Lucene or SQL query.

    Args:
        query: Lucene query (e.g. "type:testcase AND status:approved")
               or SQL query if is_sql=True.
        fields: Comma-separated field names to return.
        sort: Field to sort by.
        limit: Max results (-1 for unlimited).
        is_sql: If true, query is SQL instead of Lucene.
        project_id: Polarion project ID.
    """
    try:
        field_list = [f.strip() for f in fields.split(",")]
        kwargs: dict = {"fields": field_list, "limit": limit}
        if sort:
            kwargs["sort"] = sort
        if is_sql:
            kwargs["is_sql"] = True
        results = _WorkItem.query(query, **kwargs)
        items = [serialize_work_item(wi) for wi in results]
        return json.dumps({"total": len(items), "work_items": items})
    except Exception as e:
        return _err(e)


@mcp.tool()
def search_test_runs(
    query: str,
    fields: str = "test_run_id,status,created,author",
    sort: Optional[str] = None,
    limit: int = 50,
    search_templates: bool = False,
) -> str:
    """Search test runs.

    Args:
        query: Lucene query for test runs.
        fields: Comma-separated field names.
        sort: Field to sort by.
        limit: Max results (-1 for unlimited).
        search_templates: If true, search templates instead of runs.
    """
    try:
        field_list = [f.strip() for f in fields.split(",")]
        kwargs: dict = {
            "fields": field_list,
            "limit": limit,
            "search_templates": search_templates,
        }
        if sort:
            kwargs["sort"] = sort
        results = TestRun.search(query, **kwargs)
        runs = [serialize_test_run(tr) for tr in results]
        return json.dumps({"total": len(runs), "test_runs": runs})
    except Exception as e:
        return _err(e)


@mcp.tool()
def search_plans(
    query: str,
    fields: str = "plan_id,name,status",
    sort: Optional[str] = None,
    limit: int = 50,
) -> str:
    """Search plans.

    Args:
        query: Lucene query for plans.
        fields: Comma-separated field names.
        sort: Field to sort by.
        limit: Max results (-1 for unlimited).
    """
    try:
        field_list = [f.strip() for f in fields.split(",")]
        kwargs: dict = {"limit": limit, "fields": field_list}
        if sort:
            kwargs["sort"] = sort
        results = Plan.search(query, **kwargs)
        plans = [serialize_plan(p) for p in results]
        return json.dumps({"total": len(plans), "plans": plans})
    except Exception as e:
        return _err(e)


@mcp.tool()
def search_documents(
    query: Optional[str] = None,
    space: Optional[str] = None,
    project_id: Optional[str] = None,
) -> str:
    """Search documents by query, or list all documents in a space.

    Args:
        query: Lucene query (e.g. "type:testspecification").
        space: Space name to list all docs from (e.g. "Testing").
               If both query and space are given, query takes priority.
        project_id: Polarion project ID.
    """
    try:
        pid = project_id or default_project()
        if query:
            results = Document.query(query, fields=["document_id", "document_name", "title", "author", "created"])
        elif space:
            results = Document.get_documents(pid, space)
        else:
            return json.dumps({"status": "error", "detail": "Provide either query or space."})
        docs = [serialize_document(d) for d in results]
        return json.dumps({"total": len(docs), "documents": docs})
    except Exception as e:
        return _err(e)
