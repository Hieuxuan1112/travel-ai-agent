"""Giao dien chat cho agent - hien REALTIME tung buoc agent suy luan va goi tool.

Chay:  venv\\Scripts\\streamlit.exe run app.py
"""

import time
from pathlib import Path

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

st.set_page_config(page_title="Cornwall Travel Agent", page_icon="🏖️", layout="centered")

PROJECT_DIR = Path(__file__).parent
HISTORY_TURNS = 4  # so luot hoi-dap cu duoc gui kem de agent hieu ngu canh


@st.cache_resource(show_spinner="Building the travel knowledge base (first run only) ...")
def load_agent():
    """Import mot lan roi cache: tranh dung lai vector store moi khi Streamlit rerun."""
    import main_02_02 as lab

    lab.get_travel_info_vectorstore()  # dung/nap kho ngay, khong de cho toi cau hoi dau tien
    return lab


lab = load_agent()

with st.sidebar:
    st.subheader("Agent configuration")
    st.metric("LLM", lab.CHAT_MODEL)
    st.metric("Weather source", "Open-Meteo (live)" if lab.WEATHER_MODE == "real" else "mock")
    st.write("**Tools registered**")
    for t in lab.TOOLS:
        st.markdown(f"- `{t.name}`")
        st.caption(t.description)
    graph_png = PROJECT_DIR / "docs" / "graph.png"
    if graph_png.exists():
        st.write("**Agent graph**")
        st.image(str(graph_png))
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()

st.title("🏖️ Cornwall Travel Agent")
st.caption(
    "LangGraph ReAct agent · tool 1: semantic search over Wikivoyage · "
    "tool 2: live weather for any city"
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("e.g. Suggest two Cornwall beach towns with nice weather"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Ghep lai vai luot gan nhat de agent hieu cau hoi noi tiep ("con thi tran kia thi sao?")
    history = []
    for msg in st.session_state.messages[-(HISTORY_TURNS * 2 + 1):]:
        cls = HumanMessage if msg["role"] == "user" else AIMessage
        history.append(cls(content=msg["content"]))

    with st.chat_message("assistant"):
        trace_box = st.container()
        started = time.time()
        tool_calls = 0
        final_answer = ""

        with st.status("Agent is reasoning ...", expanded=True) as status:
            # stream_mode="updates": moi lan mot node chay xong thi tra ve ket qua node do
            for update in lab.travel_info_agent.stream(
                {"messages": history}, stream_mode="updates"
            ):
                for _node_name, payload in update.items():
                    for message in payload.get("messages", []):
                        if isinstance(message, AIMessage) and message.tool_calls:
                            for call in message.tool_calls:
                                tool_calls += 1
                                args = ", ".join(f"{k}={v!r}" for k, v in call["args"].items())
                                st.markdown(f"🔧 **{call['name']}**({args})")
                        elif isinstance(message, ToolMessage):
                            with st.expander(f"📄 result of `{message.name}`"):
                                st.code(str(message.content)[:3000])
                        elif isinstance(message, AIMessage):
                            final_answer = lab.answer_text(message)
            status.update(label="Done", state="complete", expanded=False)

        # Hiem khi model tra ve luot cuoi khong co chu nao (chi co khoi suy nghi).
        # Tren ban demo cong khai, mot o trong trong nhu app hong -> luon noi gi do.
        st.markdown(final_answer or "_No text came back from the model. Try rephrasing._")
        trace_box.caption(
            f"{tool_calls} tool call(s) · {time.time() - started:.1f}s · model {lab.CHAT_MODEL}"
        )

    st.session_state.messages.append({"role": "assistant", "content": final_answer})
