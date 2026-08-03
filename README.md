# mcp-polarion

MCP server for Polarion ALM via **pylero** (SOAP/WSDL SDK). Provides 42 tools for full CRUD on work items, test runs, documents, plans, links, attachments, comments, approvals, test steps, and workflow actions.

## Quick start

```bash
uvx --from ./mcp-polarion mcp-polarion
```

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `POLARION_URL` | Yes | Base URL ending with `/polarion` |
| `POLARION_USERNAME` | Yes | Login username (needed for WSDL auth) |
| `POLARION_TOKEN` | Yes | Personal access token |
| `POLARION_PROJECT` | Yes | Default project ID |
| `POLARION_VERIFY_SSL` | No | `true` (default) or `false` |
| `POLARION_DISABLE_MANUAL_AUTH` | No | Any non-empty value (the default). Empty restores pylero's interactive token prompt — which an MCP server cannot answer, so a bad token would hang instead of failing |

At startup the server loads `~/.mcp-polarion.env` (a plain `KEY=value` file) into
the environment, so the token lives in **one** place instead of being copied into
every project's `.mcp.json`:

```sh
POLARION_URL=https://polarion.example.com/polarion
POLARION_USERNAME=your-user
POLARION_TOKEN=your-token
POLARION_PROJECT=your-project
POLARION_VERIFY_SSL=true
```

Variables already set in the environment always win, so an explicit `env` block or
CI-injected credentials override the file. A missing file is not an error.

### MCP config entry

With `~/.mcp-polarion.env` in place, no `env` block is needed — which makes the
entry safe to register once at user scope and reuse across projects. Use an
absolute path or a git URL for `--from`: a relative one resolves against the
server's working directory, which differs per project.

```json
{
  "polarion": {
    "command": "uvx",
    "args": ["--from", "git+https://github.com/cboos/mcp-polarion", "mcp-polarion"]
  }
}
```

To override per project (or to skip the file entirely), add the variables back:

```json
{
  "polarion": {
    "command": "uvx",
    "args": ["--from", "/path/to/mcp-polarion", "mcp-polarion"],
    "env": {
      "POLARION_URL": "https://polarion.example.com/polarion",
      "POLARION_USERNAME": "your-user",
      "POLARION_TOKEN": "your-token",
      "POLARION_PROJECT": "your-project",
      "POLARION_VERIFY_SSL": "true"
    }
  }
}
```

## Tools (42)

### Setup / Discovery

| Tool | Description |
|------|-------------|
| `test_connection` | Verify auth and project access |
| `get_enum_options` | List valid values for any field |
| `get_custom_fields` | Required + optional custom fields per work item type |
| `get_work_item_types` | List all installation-specific types |

### Query / Search

| Tool | Description |
|------|-------------|
| `search_work_items` | Lucene + SQL query with field selection, sort, limit |
| `search_test_runs` | Query test runs, filter by template |
| `search_plans` | Query plans |
| `search_documents` | Query documents or list by space |

### Read / Inspect

| Tool | Description |
|------|-------------|
| `get_work_item` | Fetch by ID with all fields |
| `get_document` | Fetch document, extract embedded work item IDs |
| `get_test_run` | Fetch test run with pass/fail statistics |
| `get_test_records` | List test results within a run |
| `get_linked_work_items` | Forward (outgoing) links |
| `get_back_linked_work_items` | Reverse (incoming) links |
| `get_test_steps` | Read test case steps |
| `get_workflow_actions` | Available transitions for work item or test run |
| `get_revisions` | Revision/change history |
| `get_comments` | List comments |
| `get_attachments` | List attachments |
| `which_test_runs` | Find all test runs containing a test case |

### Create

| Tool | Description |
|------|-------------|
| `create_work_item` | Any type with custom field support |
| `create_test_run` | From template with assignee, plan |
| `create_test_run_template` | Define test case selection mode |
| `create_document` | New document in a space |
| `create_plan` | New plan with optional parent |

### Update

| Tool | Description |
|------|-------------|
| `update_work_item` | Modify fields, status, custom fields |
| `set_test_steps` | Write/replace test steps |
| `record_test_result` | Add pass/fail/blocked test record |
| `update_test_record` | Modify existing test record |
| `perform_workflow_action` | Transition work item or test run state |
| `update_document` | Modify document title/content |
| `update_test_run` | Modify test run fields |
| `update_plan` | Modify plan dates/capacity/status |

### Link / Relate

| Tool | Description |
|------|-------------|
| `manage_links` | Add/remove typed links between work items |
| `manage_assignees` | Add/remove/list assignees |
| `manage_attachments` | Add/list/delete attachments |
| `manage_comments` | Create/list comments |
| `manage_approvals` | Manage approval reviewers and status |
| `manage_hyperlinks` | Add/remove external hyperlinks |

### Delete

| Tool | Description |
|------|-------------|
| `delete_work_item` | Permanently delete a work item |
| `delete_document` | Permanently delete a document |
| `delete_plan` | Permanently delete a plan |

## Dependencies

- [fastmcp](https://pypi.org/project/fastmcp/) >= 3.0.0
- [pylero](https://pypi.org/project/pylero/) >= 0.2.0

## Architecture

```
mcp_polarion/
  __init__.py          Loads ~/.mcp-polarion.env before anything imports pylero
  _app.py              FastMCP instance + _err() helper
  pylero_client.py     Serialization helpers (work items, test runs, etc.)
  server.py            Thin entrypoint — imports tool modules, defines main()
  tools/
    __init__.py        Package marker
    discovery.py       4 tools — connection, enums, custom fields, types
    search.py          4 tools — work items, test runs, plans, documents
    read.py           12 tools — get/inspect individual entities
    create.py          5 tools — create work items, runs, templates, docs, plans
    update.py          8 tools — modify entities, test steps, workflow actions
    manage.py          6 tools — links, assignees, attachments, comments, approvals, hyperlinks
    delete.py          3 tools — delete work items, documents, plans
```

pylero wraps Polarion's SOAP/WSDL API. The server eagerly initializes pylero at startup (~12s initial WSDL download, then cached). All tools share the same session and auth.

Note: The Polarion SOAP API is in maintenance mode since Polarion 2410. This server uses pylero for its full API coverage (deletes, test steps, attachments, approvals) which the REST v1 API does not support.

## License

MIT
