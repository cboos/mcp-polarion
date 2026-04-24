"""Shared FastMCP instance and error helper."""

from __future__ import annotations

import json

from fastmcp import FastMCP

mcp = FastMCP("Polarion ALM")


def _err(e: Exception) -> str:
    return json.dumps({"status": "error", "detail": str(e)})
