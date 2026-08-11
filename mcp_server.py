"""MCP server - phoi 2 tool cua agent ra ngoai theo chuan Model Context Protocol.

Bat ky MCP client nao (Claude Desktop, Cursor, hoac main_04_mcp.py trong repo nay)
deu goi duoc 2 tool nay ma KHONG can biet gi ve code ben trong.

Chay tay de kiem tra:  venv\\Scripts\\python.exe mcp_server.py
Cam vao Claude Desktop: xem README.md muc "Use the tools from Claude Desktop".
"""

import contextlib
import sys

from mcp.server.fastmcp import FastMCP

# Giao thuc MCP tren stdio dung stdout de truyen JSON-RPC -> moi dong print lac vao
# stdout se lam hong ket noi. Vi vay nuot toan bo log luc import sang stderr.
with contextlib.redirect_stdout(sys.stderr):
    from main_02_02 import search_travel_info as _search_tool
    from main_02_02 import weather_forecast as _weather_tool

mcp = FastMCP("cornwall-travel")


@mcp.tool()
def search_travel_info(query: str) -> str:
    """Search travel information about destinations in England.

    Use it to find towns, beaches, resorts and activities in Cornwall.
    """
    return _search_tool.invoke({"query": query})


@mcp.tool()
def weather_forecast(town: str, country: str = "") -> dict:
    """Get the CURRENT weather of a town or city anywhere in the world.

    Pass `country` (e.g. "United Kingdom") when you know it, because many towns
    share a name. Returns condition, temperature, wind and rain.
    """
    return _weather_tool.invoke({"town": town, "country": country})


if __name__ == "__main__":
    mcp.run(transport="stdio")
