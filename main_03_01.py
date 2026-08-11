"""
Muc 11.9 cua sach: ban RUT GON cua chinh agent o main_02_02.py.

Toan bo phan lap rap do thi (AgentState, ToolsExecutionNode, llm_node,
add_node/add_conditional_edges/compile) duoc thay bang MOT loi goi
create_react_agent(). Ket qua chay giong het, code ngan hon rat nhieu.

Chay:  venv\\Scripts\\python.exe main_03_01.py
"""

import sys

from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

# Dung lai 2 tool + model da dinh nghia o ban day du (khong copy code lai).
from main_02_02 import SYSTEM_PROMPT, TOOLS, answer_text, llm_model

travel_info_agent = create_react_agent(
    model=llm_model,
    tools=TOOLS,
    prompt=SYSTEM_PROMPT,
)


def ask(question: str) -> str:
    result = travel_info_agent.invoke({"messages": [HumanMessage(content=question)]})
    return answer_text(result["messages"][-1])


def chat_loop():
    print("UK Travel Assistant - prebuilt ReAct agent (type 'exit' to quit)")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue
        print(f"Assistant: {ask(user_input)}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(f"You: {sys.argv[1]}")
        print(f"Assistant: {ask(sys.argv[1])}")
    else:
        chat_loop()
