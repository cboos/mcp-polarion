"""MCP server for Polarion ALM.

Credentials are loaded here, before anything else in the package runs.

``pylero`` reads ``POLARION_URL`` / ``POLARION_USERNAME`` / ``POLARION_TOKEN``
while it is being *imported*, and ``pylero_client`` reads ``POLARION_VERIFY_SSL``
the same way -- so by the time any tool module is imported it is already too
late to populate the environment. Importing any submodule of this package runs
this file first, which makes it the only placement that is early enough for
every entry point (``mcp-polarion``, ``python -m``, or a direct submodule
import in a test).

Values already present in the environment win: an explicit ``env`` block in
``.mcp.json``, or CI-injected credentials, override the file rather than the
other way round.
"""

from pathlib import Path

from dotenv import load_dotenv

ENV_FILE = Path.home() / ".mcp-polarion.env"

load_dotenv(ENV_FILE, override=False)
