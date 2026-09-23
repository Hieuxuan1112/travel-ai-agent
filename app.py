"""Giao dien chat cho agent - hien REALTIME tung buoc agent suy luan va goi tool.

Chay:  venv\\Scripts\\streamlit.exe run app.py
"""

import json
import os
import time
import uuid
from collections import deque
from pathlib import Path

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

st.set_page_config(page_title="Cornwall Travel Agent", page_icon="🏖️", layout="centered")

PROJECT_DIR = Path(__file__).parent

# ---------------------------------------------------------------------------
# CONG TAC NGAT + NGAN SACH, cho ban CONG KHAI.
#
# api.py da co rate limit theo IP, nhung ban chay cong khai lai la app.py -
# tuc la cho so ho that su nam o day. Streamlit khong dua IP client ra mot cach
# on dinh giua cac phien ban, nen thay vi gia vo chan theo IP, ta chan hai lop
# thanh that:
#   - ngan sach TOAN CUC theo gio: bao ve dung thu can bao ve (hoa don API key)
#   - han muc theo PHIEN: giu cong bang giua nhung nguoi dang mo app cung luc
# Nguoi co the mo tab moi de lach han muc phien, nhung KHONG lach duoc ngan
# sach toan cuc - do la lop chan thuc su.
# ---------------------------------------------------------------------------
AI_ENABLED = os.environ.get("AI_ENABLED", "1").strip().lower() not in {"0", "false", "no"}
GLOBAL_BUDGET_PER_HOUR = int(os.environ.get("GLOBAL_BUDGET_PER_HOUR", "200"))
SESSION_LIMIT_PER_HOUR = int(os.environ.get("SESSION_LIMIT_PER_HOUR", "20"))
_WINDOW_SECONDS = 3600


@st.cache_resource
def _global_hits() -> deque:
    """Mot deque dung chung ca tien trinh (cache_resource = mot ban cho moi server)."""
    return deque()


def _within_window(hits: deque, now: float) -> deque:
    while hits and now - hits[0] > _WINDOW_SECONDS:
        hits.popleft()
    return hits


def check_budget() -> str | None:
    """Tra ve thong bao tu choi, hoac None neu duoc phep hoi."""
    if not AI_ENABLED:
        return ("Tinh nang AI dang duoc tam tat. Repo la public, ban co the "
                "clone ve chay bang API key cua minh.")
    now = time.time()
    if len(_within_window(_global_hits(), now)) >= GLOBAL_BUDGET_PER_HOUR:
        return (f"Demo da dung het ngan sach {GLOBAL_BUDGET_PER_HOUR} cau/gio. "
                "Thu lai sau, hoac clone repo ve chay bang key cua minh.")
    session = _within_window(st.session_state.setdefault("hits", deque()), now)
    if len(session) >= SESSION_LIMIT_PER_HOUR:
        return f"Ban da hoi {SESSION_LIMIT_PER_HOUR} cau trong mot gio. Thu lai sau."
    return None


def record_question() -> None:
    now = time.time()
    _global_hits().append(now)
    st.session_state.setdefault("hits", deque()).append(now)


@st.cache_resource(show_spinner="Building the travel knowledge base (first run only) ...")
def load_agent():
    """Import mot lan roi cache: tranh dung lai vector store moi khi Streamlit rerun."""
    import main_02_02 as lab

    lab.get_travel_info_vectorstore()  # dung/nap kho ngay, khong de cho toi cau hoi dau tien
    return lab


lab = load_agent()


AGENT_MODES = ["ReAct (single agent)", "Multi-agent (planner + executor)"]


@st.cache_resource(show_spinner="Connecting to the conversation store ...")
def load_stateful_agents():
    """Hai agent, DUNG CHUNG mot checkpointer/connection pool.

    Multi-agent tai them main_05_multi_agent - file do tu import main_02_02
    va boc lai chinh graph ReAct lam executor (subgraph), nen khong ton them
    vector store hay ket noi rieng nao ca, chi them mot compiled graph nua.
    """
    import main_05_multi_agent as multi_agent
    import persistence

    checkpointer = persistence.get_checkpointer()
    agents = {
        AGENT_MODES[0]: lab.build_agent(checkpointer),
        AGENT_MODES[1]: multi_agent.build_supervised_agent(checkpointer),
    }
    return agents, persistence.backend_name()


agents, store_backend = load_stateful_agents()

# thread_id nam tren URL chu khong chi trong session_state: F5 la Streamlit tao
# phien moi va xoa sach session_state, nhung query param thi con -> mo lai dung
# hoi thoai cu. Dan URL cho nguoi khac cung mo duoc dung thread do.
def _valid_thread(raw: str | None) -> str | None:
    """Chi nhan UUID dung dinh dang.

    thread_id di THANG tu URL vao khoa doc/ghi cua checkpointer. Khong kiem tra
    thi ai cung dat duoc khoa tuy y (?thread=admin, ?thread=1) - vua tao rac
    trong database, vua bien khong gian khoa tu 122 bit ngau nhien thanh thu
    doan duoc. Ep dung UUID giu cho khoa luon o muc khong the do tim.
    """
    if not raw:
        return None
    try:
        return str(uuid.UUID(raw))
    except ValueError:
        return None


if "thread_id" not in st.session_state:
    st.session_state.thread_id = _valid_thread(st.query_params.get("thread")) or str(uuid.uuid4())
if st.query_params.get("thread") != st.session_state.thread_id:
    st.query_params["thread"] = st.session_state.thread_id

thread_config = {"configurable": {"thread_id": st.session_state.thread_id}}


def restore_messages():
    """Dung lai danh sach de hien thi tu state da luu.

    Checkpointer giu ca AIMessage rong (luot chi goi tool) va ToolMessage - hai
    loai do la duong di ben trong, khong phai loi thoai -> bo qua khi ve lai man hinh.
    """
    snapshot = agent.get_state(thread_config)
    shown = []
    for message in snapshot.values.get("messages", []):
        if isinstance(message, HumanMessage):
            shown.append({"role": "user", "content": message.content})
        elif isinstance(message, AIMessage) and not message.tool_calls:
            text = lab.answer_text(message)
            if text:
                shown.append({"role": "assistant", "content": text})
    return shown


with st.sidebar:
    st.subheader("Agent configuration")
    agent_mode = st.radio(
        "Agent architecture",
        AGENT_MODES,
        help="ReAct: mot agent tu suy luan roi hanh dong, khong tach buoc. "
             "Multi-agent: mot planner quyet dinh chien luoc (co can xep hang "
             "nhieu town theo thoi tiet khong, bao nhieu, tieu chi gi) TRUOC, "
             "roi giao cho executor - chinh la agent ReAct ben trai, dung "
             "nguyen - thuc thi theo dung ke hoach do.",
    )
    st.metric("LLM", lab.CHAT_MODEL)
    st.metric("Weather source", "Open-Meteo (live)" if lab.WEATHER_MODE == "real" else "mock")
    st.metric("Conversation store", store_backend)
    st.write("**Tools registered**")
    for t in lab.TOOLS:
        st.markdown(f"- `{t.name}`")
        st.caption(t.description)
    graph_png = PROJECT_DIR / "docs" / "graph.png"
    if graph_png.exists():
        st.write("**Agent graph**")
        st.image(str(graph_png))
    # Khong xoa gi duoi database: chi mo mot thread moi. Hoi thoai cu van truy
    # lai duoc neu con giu URL - dung tinh chat cua checkpointer.
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.query_params["thread"] = st.session_state.thread_id
        st.rerun()

# Doi kien truc giua chung mot hoi thoai la truong hop la (2 graph khac shape
# dung chung 1 thread_id) - de an toan, coi nhu bam "Clear conversation": mo
# thread moi thay vi co gang tron lich su cua 2 kien truc khac nhau.
if "agent_mode" not in st.session_state:
    st.session_state.agent_mode = agent_mode
elif st.session_state.agent_mode != agent_mode:
    st.session_state.agent_mode = agent_mode
    st.session_state.messages = []
    st.session_state.thread_id = str(uuid.uuid4())
    st.query_params["thread"] = st.session_state.thread_id
    st.rerun()

agent = agents[agent_mode]

st.title("🏖️ Cornwall Travel Agent")
st.caption(
    "LangGraph agent (choose ReAct or Multi-agent in the sidebar) · "
    "tools: semantic search over Wikivoyage, live weather, weighted town ranking"
)

if "messages" not in st.session_state:
    st.session_state.messages = restore_messages()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------------------------------
# GIONG NOI (Web Speech API cua trinh duyet - khong key, khong phi, khong
# dependency moi). Chi Chrome/Edge co SpeechRecognition; Firefox/Safari thi
# nut mic tu vo hieu hoa, phan con lai cua app khong doi.
#
# ponytail: khong co cach chinh thong de mot iframe tinh tra gia tri ve Python
# ma khong full page reload (do can Streamlit.setComponentValue cua mot
# component that su). Nen dung lai chinh ky thuat ?thread=... da co san trong
# file nay: ghi ket qua nhan dien vao query param ?voice=..., Streamlit tu doc
# lai khi trang nap lai. Nang cap khi can UX muot hon: xay mot custom component
# that.
# ---------------------------------------------------------------------------
st.iframe(
    """
    <div style="margin-bottom:8px">
      <button id="mic-btn" style="padding:6px 14px;border-radius:6px;cursor:pointer">
        🎤 Speak your question
      </button>
      <span id="mic-status" style="margin-left:8px;color:#888;font-size:13px"></span>
    </div>
    <script>
    const btn = document.getElementById("mic-btn");
    const status = document.getElementById("mic-status");
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      status.textContent = "Not supported in this browser - try Chrome or Edge.";
      btn.disabled = true;
    } else {
      const recognition = new SR();
      recognition.lang = "en-US";
      recognition.interimResults = false;
      btn.onclick = () => { status.textContent = "Listening ..."; recognition.start(); };
      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        const url = new URL(window.parent.location.href);
        url.searchParams.set("voice", transcript);
        window.parent.location.href = url.toString();
      };
      recognition.onerror = (event) => { status.textContent = "Error: " + event.error; };
    }
    </script>
    """,
    height=45,
)

voice_prompt = st.query_params.get("voice")
if voice_prompt:
    del st.query_params["voice"]  # xu ly mot lan, khong lap lai o lan rerun sau

if prompt := (st.chat_input("e.g. Suggest two Cornwall beach towns with nice weather")
              or voice_prompt):
    refusal = check_budget()
    if refusal:
        st.warning(refusal)
        st.stop()
    record_question()
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        trace_box = st.container()
        started = time.time()
        tool_calls = 0
        final_answer = ""

        with st.status("Agent is reasoning ...", expanded=True) as status:
            # Chi gui CAU MOI: checkpointer tu nap lai lich su cua thread_id nay,
            # khong con phai tu ghep history nhu truoc.
            # stream_mode="updates": moi lan mot node chay xong thi tra ve ket qua node do
            for update in agent.stream(
                {"messages": [HumanMessage(content=prompt)]},
                thread_config,
                stream_mode="updates",
            ):
                for _node_name, payload in update.items():
                    if _node_name == "planner" and payload.get("plan"):
                        plan = payload["plan"]
                        st.markdown(f"🧭 **planner decision** · `{plan}`")
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
        if final_answer:
            # TTS cung bang Web Speech API, cung ly do voi mic o tren: khong
            # key, khong phi. height=1 vi khong co gi de hien, chi chay script.
            st.iframe(
                f"<script>speechSynthesis.cancel();"
                f"speechSynthesis.speak(new SpeechSynthesisUtterance({json.dumps(final_answer)}));"
                f"</script>",
                height=1,
            )

    st.session_state.messages.append({"role": "assistant", "content": final_answer})
