"""pylero init + JSON serialization helpers."""

from __future__ import annotations

import os
import re
import ssl
from datetime import date, datetime
from typing import Any

if os.environ.get("POLARION_VERIFY_SSL", "true").lower() == "false":
    ssl._create_default_https_context = ssl._create_unverified_context


def default_project() -> str:
    return os.environ.get("POLARION_PROJECT", "")


# ---------------------------------------------------------------------------
# Serialization helpers -- turn pylero objects into JSON-safe dicts
# ---------------------------------------------------------------------------

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(val: Any) -> str:
    if val is None:
        return ""
    s = str(val)
    if hasattr(val, "content"):
        s = str(val.content) if val.content else ""
    return _HTML_TAG_RE.sub("", s).strip()


def _safe(val: Any) -> Any:
    """Convert a pylero value to something JSON-serializable."""
    if val is None:
        return None
    if isinstance(val, (str, int, float, bool)):
        return val
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, list):
        return [_safe(v) for v in val]
    if hasattr(val, "__dict__"):
        return {k: _safe(v) for k, v in vars(val).items() if not k.startswith("_")}
    return str(val)


def serialize_work_item(wi: Any) -> dict:
    d: dict[str, Any] = {
        "id": getattr(wi, "work_item_id", ""),
        "type": getattr(wi, "type", ""),
        "title": getattr(wi, "title", ""),
        "status": getattr(wi, "status", ""),
        "severity": getattr(wi, "severity", ""),
        "priority": getattr(wi, "priority", ""),
        "author": getattr(wi, "author", ""),
        "created": _safe(getattr(wi, "created", None)),
        "updated": _safe(getattr(wi, "updated", None)),
        "description": _strip_html(getattr(wi, "description", None)),
    }
    assignees = getattr(wi, "assignee", None)
    if assignees:
        d["assignees"] = [_safe(a) for a in assignees] if isinstance(assignees, list) else [_safe(assignees)]
    return d


def serialize_test_run(tr: Any) -> dict:
    return {
        "id": getattr(tr, "test_run_id", ""),
        "title": getattr(tr, "title", ""),
        "status": getattr(tr, "status", ""),
        "author": _safe(getattr(tr, "author", None)),
        "created": _safe(getattr(tr, "created", None)),
        "assignee": _safe(getattr(tr, "assignee", None)),
        "select_test_cases_by": getattr(tr, "select_test_cases_by", ""),
        "plannedin": _safe(getattr(tr, "plannedin", None)),
        "is_template": getattr(tr, "is_template", False),
    }


def serialize_test_record(rec: Any) -> dict:
    return {
        "test_case_id": getattr(rec, "test_case_id", ""),
        "result": getattr(rec, "result", ""),
        "executed_by": _safe(getattr(rec, "executed_by", None)),
        "executed": _safe(getattr(rec, "executed", None)),
        "duration": _safe(getattr(rec, "duration", None)),
        "comment": _strip_html(getattr(rec, "comment", None)),
    }


def serialize_document(doc: Any) -> dict:
    return {
        "id": getattr(doc, "document_id", ""),
        "name": getattr(doc, "document_name", ""),
        "title": getattr(doc, "title", ""),
        "type": getattr(doc, "type", ""),
        "status": getattr(doc, "status", ""),
        "space": getattr(doc, "space", ""),
        "author": _safe(getattr(doc, "author", None)),
        "created": _safe(getattr(doc, "created", None)),
        "updated": _safe(getattr(doc, "updated", None)),
    }


def serialize_plan(plan: Any) -> dict:
    return {
        "id": getattr(plan, "plan_id", ""),
        "name": getattr(plan, "name", ""),
        "status": getattr(plan, "status", ""),
        "start_date": _safe(getattr(plan, "start_date", None)),
        "due_date": _safe(getattr(plan, "due_date", None)),
        "capacity": _safe(getattr(plan, "capacity", None)),
        "author": _safe(getattr(plan, "author", None)),
    }


def serialize_linked_item(link: Any) -> dict:
    return {
        "work_item_id": getattr(link, "work_item_id", ""),
        "role": getattr(link, "role", ""),
        "suspect": getattr(link, "suspect", False),
    }
