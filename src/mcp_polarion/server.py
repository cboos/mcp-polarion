"""Polarion ALM MCP Server — 42 tools via pylero (SOAP/WSDL SDK).

Covers work items, test runs, documents, plans, links, attachments,
comments, approvals, test steps, and workflow actions.

Tool implementations live in the tools/ subpackage; importing them
registers the @mcp.tool() decorated functions on the shared FastMCP
instance from _app.py.
"""

from mcp_polarion._app import mcp  # noqa: F401 — re-exported for FastMCP

import mcp_polarion.tools.discovery  # noqa: F401
import mcp_polarion.tools.search     # noqa: F401
import mcp_polarion.tools.read       # noqa: F401
import mcp_polarion.tools.create     # noqa: F401
import mcp_polarion.tools.update     # noqa: F401
import mcp_polarion.tools.manage     # noqa: F401
import mcp_polarion.tools.delete     # noqa: F401


def main():
    mcp.run()
