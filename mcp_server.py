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
    from main_02_02 import convert_currency as _currency_tool
    from main_02_02 import rank_town_candidates as _rank_tool
    from main_02_02 import search_travel_info as _search_tool
    from main_02_02 import translate_text as _translate_tool
    from main_02_02 import weather_forecast as _weather_tool
    from main_02_02 import web_search as _web_search_tool

mcp = FastMCP("cornwall-travel")


@mcp.tool()
def search_travel_info(query: str) -> str:
    """Search travel information about destinations anywhere in the world.

    Use it to find towns, cities, regions, beaches, resorts and activities.
    """
    return _search_tool.invoke({"query": query})


@mcp.tool()
def weather_forecast(town: str, country: str = "") -> dict:
    """Get the CURRENT weather of a town or city anywhere in the world.

    Pass `country` (e.g. "United Kingdom") when you know it, because many towns
    share a name. Returns condition, temperature, wind and rain.
    """
    return _weather_tool.invoke({"town": town, "country": country})


@mcp.tool()
def rank_town_candidates(
    towns: list[str],
    country: str = "",
    min_temp_c: float = 15.0,
    max_temp_c: float = 25.0,
    min_weather_fit: float = 0.5,
    top_n: int = 2,
) -> dict:
    """Rank candidate towns by relevance and weather fit using a weighted score.

    Pass town names only - this tool fetches each town's weather itself.
    """
    return _rank_tool.invoke({
        "towns": towns,
        "country": country,
        "min_temp_c": min_temp_c,
        "max_temp_c": max_temp_c,
        "min_weather_fit": min_weather_fit,
        "top_n": top_n,
    })


@mcp.tool()
def web_search(query: str) -> str:
    """Search the general web for information not covered by the other tools."""
    return _web_search_tool.invoke({"query": query})


@mcp.tool()
def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convert an amount between currencies using the current exchange rate."""
    return _currency_tool.invoke({
        "amount": amount, "from_currency": from_currency, "to_currency": to_currency,
    })


@mcp.tool()
def translate_text(text: str, target_lang: str) -> dict:
    """Translate text into another language (ISO 639-1 code or language name)."""
    return _translate_tool.invoke({"text": text, "target_lang": target_lang})


if __name__ == "__main__":
    mcp.run(transport="stdio")
