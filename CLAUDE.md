# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

MCP server exposing Polarion ALM as 42 tools, built on **pylero** (the SOAP/WSDL SDK) rather than
Polarion's REST v1 API — REST lacks deletes, test steps, attachments and approvals. See `README.md`
for the full tool table and the env-var/MCP config.

## Commands

```bash
uv sync                          # install deps into .venv
uv run mcp-polarion              # run the server over stdio (needs live credentials)
uvx --from . mcp-polarion        # run as an end user would
```

There is no test suite, linter config or CI. Verification is manual, against a live Polarion.

## The one thing that shapes everything: import means connect

`pylero/work_item.py` executes `BasePolarion()` + `get_valid_field_values("workitem-type")` **at module
import time** and synthesizes one `_SpecificWorkItem` subclass per work-item type into its own
namespace. Consequences:

- Importing `mcp_polarion.server` (or any `tools/*` module) **requires valid credentials and network
  reachability**. You cannot smoke-test imports offline, and startup costs ~12s on the first WSDL fetch.
- Credentials come from `POLARION_*` env vars, read by pylero itself (falling back to `~/.pylero`).
  This package never passes them explicitly — it only reads `POLARION_PROJECT` via `default_project()`.
- `POLARION_VERIFY_SSL=false` is honoured by a module-level monkeypatch of `ssl._create_default_https_context`
  in `pylero_client.py`. **Every tool module must import from `mcp_polarion.pylero_client` before it
  imports anything from `pylero`** — the existing import ordering is load-bearing, not stylistic.

## Structure

`_app.py` owns the single `FastMCP` instance and `_err()`. Each `tools/*.py` module imports `mcp` from
it and registers tools via `@mcp.tool()`; `server.py` is a pure entrypoint whose imports *are* the
registration. Adding a tool module means adding an import line to `server.py`.

Every tool follows the same contract: returns a **JSON string**, takes `project_id: Optional[str] = None`
defaulting to `default_project()`, and wraps its whole body in `try/except` returning `_err(e)` — errors
are never raised to the MCP layer. `pylero_client.py` holds the `serialize_*` helpers that flatten
pylero/suds objects into JSON-safe dicts (`_safe`) and strip HTML from rich text (`_strip_html`).

## Custom fields — the trap `_custom_fields.py` exists for

Custom fields **cannot** be set on the base `_WorkItem`. pylero builds validating, batching property
setters only on the per-type dynamic subclasses; assigning on the base class stores a dead instance
attribute that the SOAP layer silently drops (no error). So:

- `type_specific_class(type)` finds the subclass by `_wi_type`, and `resolve_local_name()` maps a
  Polarion field id (`userStory`) to pylero's snake_cased property (`user_story`).
- `_cls_suds_map` must be populated first — by constructing a type-specific instance, or by calling
  `cls.get_custom_fields(pid)` (see `create.py`).
- `update_work_item` fetches on the base class, then re-wraps the already-fetched `_suds_object` as the
  type-specific class to avoid a second round-trip; all fields then batch into one `update()`.

Beware two vocabularies for a work-item type: the **id** (`testcase`, used by all tool arguments and
`_wi_type`) and the pylero **class name** (`TestCase`, which is what `get_work_item_types` returns).

## What the read tools deliberately don't return

Serialization is lossy, so callers hitting a wall are often hitting this rather than a Polarion limit:
`_strip_html` discards all markup from descriptions, comments and test steps; `serialize_work_item`
emits a fixed field set and never custom fields; `get_attachments` lists metadata but no binary
content; and `manage_hyperlinks` can add and remove but not list. Reaching any of those means going to
pylero (or the WSDL) directly. Widening a `serialize_*` helper changes every tool that uses it.
