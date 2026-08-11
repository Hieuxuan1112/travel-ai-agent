"""Agent lay tool QUA GIAO THUC MCP thay vi import truc tiep.

Khac biet kien truc so voi main_02_02.py / main_03_01.py:

    main_02_02.py :  agent  --import python-->  ham tool  (cung mot tien trinh)
    main_04_mcp.py:  agent  --JSON-RPC/stdio-->  mcp_server.py  --> ham tool
                     (hai TIEN TRINH roi nhau, chi noi chuyen qua giao thuc)

File nay khong biet tool duoc cai dat the nao, khong import Chroma hay Open-Meteo.
Doi lai co the thay server khac (viet bang ngon ngu khac, chay tren may khac) ma
khong sua mot dong nao o day.

Chay:  venv\\Scripts\\python.exe main_04_mcp.py "Suggest a Cornwall beach town with good weather"
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_DIR = Path(__file__).parent
load_dotenv(PROJECT_DIR / ".env")

SYSTEM_PROMPT = """You are a helpful assistant that can search travel information
and get the weather forecast. Only use the tools to find the information you need
(including town names). Never invent town names from your own knowledge."""

# Khai bao server MCP can ket noi. Muon them server khac chi viec them mot muc nua.
MCP_SERVERS = {
    "cornwall-travel": {
        "command": sys.executable,
        "args": [str(PROJECT_DIR / "mcp_server.py")],
        "cwd": str(PROJECT_DIR),
        "transport": "stdio",
    }
}


def answer_text(message) -> str:
    content = message.content
    if isinstance(content, list):
        return "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )
    return content


async def build_agent():
    client = MultiServerMCPClient(MCP_SERVERS)
    tools = await client.get_tools()  # <- tool duoc TAI VE tu server, khong import
    print(f"Loaded {len(tools)} tools over MCP: {[t.name for t in tools]}\n")
    model = ChatGoogleGenerativeAI(
        model=os.environ.get("CHAT_MODEL", "gemini-3.1-flash-lite"), temperature=0
    )
    return create_react_agent(model=model, tools=tools, prompt=SYSTEM_PROMPT)


async def main():
    agent = await build_agent()

    async def ask(question: str) -> str:
        result = await agent.ainvoke({"messages": [HumanMessage(content=question)]})
        return answer_text(result["messages"][-1])

    if len(sys.argv) > 1:
        print(f"You: {sys.argv[1]}")
        print(f"Assistant: {await ask(sys.argv[1])}")
        return

    print("UK Travel Assistant over MCP (type 'exit' to quit)")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        if user_input:
            print(f"Assistant: {await ask(user_input)}\n")


if __name__ == "__main__":
    asyncio.run(main())
