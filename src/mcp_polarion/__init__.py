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

import os
from pathlib import Path

from dotenv import load_dotenv

ENV_FILE = Path.home() / ".mcp-polarion.env"

load_dotenv(ENV_FILE, override=False)

# An expired or wrong token must FAIL, not hang. On an authentication fault
# pylero falls back to prompting for a new one with getpass() (base_polarion.py,
# "Invalid Token.\nEnter Token:"), retrying three times -- but an MCP server
# owns stdin as its protocol channel and there is no terminal to answer from,
# so the process blocks indefinitely with nothing on stdout or stderr. This
# guard turns that into an immediate PyleroLibException instead.
#
# setdefault, and after load_dotenv: a real env var wins, then the file, then
# this. Set it to the empty string to restore pylero's prompt -- pylero reads
# the raw value, so any NON-EMPTY string (including "false") disables manual
# auth, and only an empty one re-enables it.
os.environ.setdefault("POLARION_DISABLE_MANUAL_AUTH", "true")
