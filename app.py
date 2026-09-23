"""Giao dien chat cho agent - hien REALTIME tung buoc agent suy luan va goi tool.

Chay:  venv\\Scripts\\streamlit.exe run app.py
"""

import ast
import json
import os
import time
import uuid
from collections import deque
from datetime import UTC, datetime
from pathlib import Path

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

import persistence
import tts

st.set_page_config(page_title="Cornwall Travel Agent", page_icon="🏖️", layout="wide")

PROJECT_DIR = Path(__file__).parent

# ---------------------------------------------------------------------------
# CSS thuan tuy trinh bay - khong dung toi logic nghiep vu. Mau/theme nen
# dat trong .streamlit/config.toml; phan nay chi phu font va cac lop san pham
# (topbar, empty state, recommendation/weather card, agent-activity line,
# trip list) ma config.toml khong lam duoc.
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Outfit:wght@400;500;600&display=swap');

    html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }
    h1, h2, h3 { font-family: 'Fraunces', serif; letter-spacing: -0.01em; }

    /* --- top bar: product name + subtle architecture/model metadata --- */
    .cta-topbar {
        display: flex; justify-content: space-between; align-items: baseline;
        padding: 4px 0 14px; border-bottom: 1px solid #2A251D; margin-bottom: 18px;
    }
    .cta-topbar h1 { font-size: 1.55rem; margin: 0; }
    .cta-meta { color: #A89E8E; font-size: 0.85rem; white-space: nowrap; }
    .cta-meta .cta-dot { color: #E8825B; margin: 0 4px; }

    /* --- empty / landing state --- */
    .cta-empty { text-align: center; padding: 56px 10px 8px; }
    .cta-empty .cta-empty-icon { font-size: 2.2rem; }
    .cta-empty h2 { font-size: 1.5rem; margin: 10px 0 4px; }
    .cta-empty p { color: #A89E8E; margin-bottom: 18px; }

    /* --- sidebar (Trips) --- */
    .cta-brand {
        font-family: 'Fraunces', serif; font-size: 1.15rem; font-weight: 600; margin-bottom: 10px;
    }
    .cta-sidebar-section {
        font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em;
        color: #A89E8E; margin: 14px 0 4px;
    }

    /* --- shared dev-fact rows (Settings panel) --- */
    .cta-fact { margin-bottom: 14px; }
    .cta-fact-label {
        font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em;
        color: #A89E8E; margin-bottom: 2px;
    }
    .cta-fact-value { font-size: 1.05rem; font-weight: 600; word-break: break-word; }

    .cta-tool {
        display: inline-block; background: rgba(232,130,91,0.14); color: #E8825B;
        border: 1px solid rgba(232,130,91,0.3); border-radius: 6px; padding: 2px 8px;
        font-family: monospace; font-size: 0.8rem; margin: 2px 0;
    }
    .cta-tool-desc { color: #A89E8E; font-size: 0.82rem; margin: 2px 0 12px 2px; }

    /* --- recommendation cards (destinations) --- */
    .cta-card {
        border: 1px solid #2A251D; border-radius: 14px; padding: 14px 16px; margin-bottom: 12px;
        background: linear-gradient(180deg, rgba(232,130,91,0.06), rgba(232,130,91,0) 65%);
    }
    .cta-card-rank {
        color: #A89E8E; font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase;
    }
    .cta-card-title {
        font-family: 'Fraunces', serif; font-size: 1.1rem; font-weight: 600; margin: 2px 0 8px;
    }
    .cta-card-row {
        display: flex; gap: 14px; flex-wrap: wrap; font-size: 0.88rem; margin-bottom: 8px;
    }
    .cta-card-match { color: #E8825B; font-weight: 600; }
    .cta-card-check { color: #A89E8E; font-size: 0.82rem; margin: 2px 0; }

    /* --- single weather card --- */
    .cta-weather-card {
        border: 1px solid #2A251D; border-radius: 14px; padding: 14px 16px; margin-bottom: 12px;
    }
    .cta-weather-temp { font-size: 1.5rem; font-weight: 600; font-family: 'Fraunces', serif; }
    .cta-weather-sub { color: #A89E8E; font-size: 0.85rem; }

    .cta-context-empty { color: #A89E8E; font-size: 0.88rem; padding: 8px 2px; }

    /* --- agent activity (collapsible "how I found this") --- */
    .cta-activity-line { font-size: 0.86rem; color: #C9C0B2; margin: 3px 0; }
    .cta-activity-line b { color: #E8825B; }

    .stButton>button { transition: transform .15s ease, border-color .15s ease, color .15s ease; }
    .stButton>button:hover { transform: translateY(-1px); border-color: #E8825B; color: #E8825B; }
    .stButton>button:active { transform: translateY(0); }

    [data-testid="stChatMessage"] { border-radius: 14px; }
    [data-testid="stStatus"] { border-radius: 10px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _fact(label: str, value: str) -> None:
    """Hang thay the st.metric - st.metric cat chu khi gia tri dai (vd ten model)."""
    st.markdown(
        f'<div class="cta-fact"><div class="cta-fact-label">{label}</div>'
        f'<div class="cta-fact-value">{value}</div></div>',
        unsafe_allow_html=True,
    )


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


def _new_thread(clear_recs: bool = True) -> None:
    st.session_state.messages = []
    st.session_state.thread_id = str(uuid.uuid4())
    st.query_params["thread"] = st.session_state.thread_id
    if clear_recs:
        st.session_state.pop("last_recs", None)
        st.session_state.pop("last_weather", None)


def _switch_to_thread(tid: str) -> None:
    """Mo lai mot thread cu - KHONG xoa messages, restore_messages() se doc lai."""
    st.session_state.pop("messages", None)
    st.session_state.thread_id = tid
    st.query_params["thread"] = tid
    st.session_state.pop("last_recs", None)
    st.session_state.pop("last_weather", None)


def _thread_bucket(ts_iso: str) -> str:
    """Today/Yesterday/Older cho sidebar - so sanh theo UTC date.

    ponytail: khong quy doi ve timezone cua nguoi dung, chi can dung tuong doi
    cho mot demo ca nhan, khong phai lich thuong mai nhieu nguoi dung.
    """
    try:
        ts = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return "Older"
    today = datetime.now(UTC).date()
    delta_days = (today - ts.date()).days
    if delta_days == 0:
        return "Today"
    if delta_days == 1:
        return "Yesterday"
    return "Older"


def _thread_title(reference_agent, tid: str) -> str:
    """Cau hoi dau tien cua thread lam nhan hien thi, cat ngan.

    reference_agent la BAT KY graph nao (ReAct hay multi-agent deu doc duoc
    channel "messages" chung) - khong phu thuoc kien truc dang chon o UI.
    """
    try:
        snapshot = reference_agent.get_state({"configurable": {"thread_id": tid}})
        for message in snapshot.values.get("messages", []):
            if isinstance(message, HumanMessage):
                text = message.content if isinstance(message.content, str) else str(message.content)
                return text[:40] + ("…" if len(text) > 40 else "")
    except Exception:
        pass
    return f"Trip {tid[:8]}"


@st.cache_data(ttl=15, show_spinner=False)
def _cached_recent_threads():
    """Cache ngan (15s) - tranh mot truy van SQL moi lan rerun script (moi phim Enter)."""
    return persistence.list_recent_threads()


with st.sidebar:
    st.markdown('<div class="cta-brand">🌴 Cornwall AI</div>', unsafe_allow_html=True)

    if st.button("+ New trip", use_container_width=True):
        _new_thread()
        st.rerun()

    recent_threads = _cached_recent_threads()
    buckets: dict[str, list[str]] = {"Today": [], "Yesterday": [], "Older": []}
    for tid, ts in recent_threads:
        if tid == st.session_state.thread_id:
            continue
        buckets[_thread_bucket(ts)].append(tid)

    reference_agent = agents[AGENT_MODES[0]]
    for bucket_name in ("Today", "Yesterday", "Older"):
        tids = buckets[bucket_name]
        if not tids:
            continue
        st.markdown(f'<div class="cta-sidebar-section">{bucket_name}</div>', unsafe_allow_html=True)
        for tid in tids:
            title = _thread_title(reference_agent, tid)
            if st.button(title, key=f"trip-{tid}", use_container_width=True):
                _switch_to_thread(tid)
                st.rerun()

    if store_backend != "postgres":
        st.caption(
            "Trip history needs a persistent store (Postgres) - this session runs in-memory."
        )

    with st.expander("⚙️ Settings"):
        agent_mode = st.radio(
            "Agent architecture",
            AGENT_MODES,
            help="ReAct: mot agent tu suy luan roi hanh dong, khong tach buoc. "
                 "Multi-agent: mot planner quyet dinh chien luoc (co can xep hang "
                 "nhieu town theo thoi tiet khong, bao nhieu, tieu chi gi) TRUOC, "
                 "roi giao cho executor - chinh la agent ReAct ben trai, dung "
                 "nguyen - thuc thi theo dung ke hoach do.",
        )
        _fact("LLM", lab.CHAT_MODEL)
        _fact("Weather source", "Open-Meteo (live)" if lab.WEATHER_MODE == "real" else "mock")
        _fact("Conversation store", store_backend)
        st.write("**Tools registered**")
        for t in lab.TOOLS:
            st.markdown(f'<span class="cta-tool">{t.name}</span>', unsafe_allow_html=True)
            st.markdown(f'<div class="cta-tool-desc">{t.description}</div>', unsafe_allow_html=True)
        graph_png = PROJECT_DIR / "docs" / "graph.png"
        if graph_png.exists():
            st.write("**Agent graph**")
            st.image(str(graph_png))

# Doi kien truc giua chung mot hoi thoai la truong hop la (2 graph khac shape
# dung chung 1 thread_id) - de an toan, coi nhu bam "New trip": mo thread moi
# thay vi co gang tron lich su cua 2 kien truc khac nhau.
if "agent_mode" not in st.session_state:
    st.session_state.agent_mode = agent_mode
elif st.session_state.agent_mode != agent_mode:
    st.session_state.agent_mode = agent_mode
    _new_thread()
    st.rerun()

agent = agents[agent_mode]


# ---------------------------------------------------------------------------
# Doc ket qua tool tra ve thanh du lieu THAT (khong bia) de ve card. ToolsExecutionNode
# ghi ToolMessage.content = str(result) (repr Python, khong phai JSON) nen dung
# ast.literal_eval - an toan, chi hieu literal, khong exec code.
# ---------------------------------------------------------------------------
_ACTIVITY_LABELS = {
    "search_travel_info": "Searching Cornwall travel knowledge",
    "weather_forecast": "Checking live weather",
    "rank_town_candidates": "Ranking candidate towns",
}


def _safe_parse_tool_result(raw: str):
    try:
        return ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return None


def _render_recommendation_cards(
    container, ranked: list[dict], relaxed: bool, relax_reason: str | None
) -> None:
    if not ranked:
        return
    if relaxed and relax_reason:
        container.caption(f"⚠️ {relax_reason}")
    for i, cand in enumerate(ranked, start=1):
        weather = cand.get("weather") or {}
        match_pct = round(cand.get("composite", 0) * 100)
        temp = weather.get("temperature")
        condition = weather.get("weather", "")
        temp_html = f"{temp}°C · {condition}" if temp is not None else "weather unavailable"
        checks = []
        if cand.get("relevance", 0) >= 0.5:
            checks.append("Strong semantic match")
        if cand.get("weather_fit", 0) >= 0.5:
            checks.append("Good weather fit")
        if not checks:
            checks.append("Best available option (criteria relaxed)")
        checks_html = "".join(f'<div class="cta-card-check">✓ {c}</div>' for c in checks)
        container.markdown(
            f'<div class="cta-card">'
            f'<div class="cta-card-rank">#{i:02d}</div>'
            f'<div class="cta-card-title">{cand.get("town", "?")}</div>'
            f'<div class="cta-card-row"><span>☀️ {temp_html}</span>'
            f'<span class="cta-card-match">⭐ {match_pct}% match</span></div>'
            f"{checks_html}"
            f"</div>",
            unsafe_allow_html=True,
        )


def _render_weather_card(container, weather: dict) -> None:
    if not weather or "error" in weather:
        return
    condition = weather.get("weather", "")
    town = weather.get("town", "")
    container.markdown(
        f'<div class="cta-weather-card">'
        f'<div class="cta-weather-temp">☀️ {weather.get("temperature")}°C</div>'
        f'<div class="cta-weather-sub">{condition} · {town}</div>'
        f'<div class="cta-weather-sub">Wind {weather.get("wind_speed_kmh")} km/h · '
        f'Precipitation {weather.get("precipitation_mm")} mm</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


chat_col, context_col = st.columns([2, 1])

with chat_col:
    mode_short = "ReAct" if agent_mode == AGENT_MODES[0] else "Multi-agent"
    st.markdown(
        f'<div class="cta-topbar"><h1>🌴 Cornwall Travel Agent</h1>'
        f'<div class="cta-meta">{mode_short}<span class="cta-dot">•</span>'
        f'{lab.CHAT_MODEL}</div></div>',
        unsafe_allow_html=True,
    )

    if "messages" not in st.session_state:
        st.session_state.messages = restore_messages()

    chip_prompt = None
    if not st.session_state.messages:
        st.markdown(
            '<div class="cta-empty"><div class="cta-empty-icon">🌴</div>'
            "<h2>Plan your next Cornwall adventure</h2>"
            "<p>Your AI travel agent for beaches, towns, weather and activities.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        chips = [
            "🌊 Find the best beach towns for good weather",
            "☀️ What's the weather like in St Ives?",
            "🏄 Suggest towns good for surfing",
            "🏖 Plan a weekend comparing two Cornwall towns",
        ]
        chip_cols = st.columns(2)
        for i, chip in enumerate(chips):
            with chip_cols[i % 2]:
                if st.button(chip, key=f"chip-{i}", use_container_width=True):
                    chip_prompt = chip.split(" ", 1)[1]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # -----------------------------------------------------------------------
    # GIONG NOI (Web Speech API cua trinh duyet - khong key, khong phi, khong
    # dependency moi). Chi Chrome/Edge co SpeechRecognition; Firefox/Safari thi
    # nut mic tu vo hieu hoa, phan con lai cua app khong doi.
    #
    # ponytail: khong co cach chinh thong de mot iframe tinh tra gia tri ve
    # Python ma khong full page reload (do can Streamlit.setComponentValue cua
    # mot component that su). Nen dung lai chinh ky thuat ?thread=... da co san
    # trong file nay: ghi ket qua nhan dien vao query param ?voice=..., Streamlit
    # tu doc lai khi trang nap lai. Nang cap khi can UX muot hon: xay mot custom
    # component that.
    # -----------------------------------------------------------------------
    st.iframe(
        """
        <style>
          body { margin: 0; background: transparent; }
          #mic-btn {
            padding: 7px 16px; border-radius: 20px; cursor: pointer;
            border: 1px solid rgba(232,130,91,0.4); background: rgba(232,130,91,0.12);
            color: #E8825B; font-family: Outfit, sans-serif; font-size: 14px; font-weight: 500;
            transition: background .15s ease, transform .15s ease;
          }
          #mic-btn:hover:not(:disabled) {
            background: rgba(232,130,91,0.22); transform: translateY(-1px);
          }
          #mic-btn:disabled { opacity: 0.5; cursor: not-allowed; }
          #mic-status {
            margin-left: 8px; color: #A89E8E; font-family: Outfit, sans-serif; font-size: 13px;
          }
        </style>
        <div style="margin-bottom:8px">
          <button id="mic-btn">
            🎤 Speak your question
          </button>
          <span id="mic-status"></span>
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
                  or voice_prompt or chip_prompt):
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
            turn_recs = None
            turn_weather = None

            with st.status("Agent activity", expanded=True) as status:
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
                            st.markdown(
                                f'<div class="cta-activity-line">🧭 <b>planner decision</b> · '
                                f'<code>{plan}</code></div>',
                                unsafe_allow_html=True,
                            )
                        for message in payload.get("messages", []):
                            if isinstance(message, AIMessage) and message.tool_calls:
                                for call in message.tool_calls:
                                    tool_calls += 1
                                    label = _ACTIVITY_LABELS.get(call["name"], call["name"])
                                    st.markdown(
                                        f'<div class="cta-activity-line">✓ <b>{label}</b></div>',
                                        unsafe_allow_html=True,
                                    )
                            elif isinstance(message, ToolMessage):
                                parsed = _safe_parse_tool_result(str(message.content))
                                is_dict = isinstance(parsed, dict)
                                if message.name == "rank_town_candidates" and is_dict:
                                    turn_recs = parsed
                                elif message.name == "weather_forecast" and is_dict:
                                    turn_weather = parsed
                                with st.expander(f"📄 result of `{message.name}`"):
                                    st.code(str(message.content)[:3000])
                            elif isinstance(message, AIMessage):
                                final_answer = lab.answer_text(message)
                status.update(label="Agent activity · done", state="complete", expanded=False)

            # Hiem khi model tra ve luot cuoi khong co chu nao (chi co khoi suy nghi).
            # Tren ban demo cong khai, mot o trong trong nhu app hong -> luon noi gi do.
            st.markdown(final_answer or "_No text came back from the model. Try rephrasing._")

            # The card that made the recommendation concrete (real tool output, not
            # invented): ranking wins over a bare weather lookup when both happened.
            if turn_recs and turn_recs.get("ranked"):
                _render_recommendation_cards(
                    st, turn_recs["ranked"], turn_recs.get("relaxed", False),
                    turn_recs.get("relax_reason"),
                )
                st.session_state.last_recs = turn_recs
                st.session_state.pop("last_weather", None)
            elif turn_weather and "error" not in turn_weather:
                _render_weather_card(st, turn_weather)
                st.session_state.last_weather = turn_weather

            trace_box.caption(
                f"{tool_calls} tool call(s) · {time.time() - started:.1f}s · model {lab.CHAT_MODEL}"
            )
            if final_answer:
                # Doc bang giong Gemini TTS that (tra phi qua GOOGLE_API_KEY) - chat
                # luong tot hon han giong may cua trinh duyet. Goi mang that bai
                # (het quota, mang hong...) thi tts.synthesize() tra None, lui ve
                # speechSynthesis mien phi cua trinh duyet de nguoi dung van nghe
                # duoc cau tra loi, chi la giong kem hon.
                audio_bytes = tts.synthesize(final_answer)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/wav", autoplay=True)
                else:
                    st.iframe(
                        f"<script>speechSynthesis.cancel();"
                        f"speechSynthesis.speak(new SpeechSynthesisUtterance("
                        f"{json.dumps(final_answer)}));</script>",
                        height=1,
                    )

        st.session_state.messages.append({"role": "assistant", "content": final_answer})
        # Rerun ngay: neu khong, luot dau tien se ve landing state (chip goi y) LAN
        # cau tra loi vua co trong CUNG mot lan flush, vi kiem tra "messages rong"
        # o tren chay TRUOC khi .append() nay xay ra trong cung run. Rerun cho
        # script chay lai tu dau voi messages da khong-rong -> landing tu an dung.
        st.rerun()

with context_col:
    st.markdown('<div class="cta-sidebar-section">Destinations</div>', unsafe_allow_html=True)
    last_recs = st.session_state.get("last_recs")
    last_weather = st.session_state.get("last_weather")
    if last_recs and last_recs.get("ranked"):
        _render_recommendation_cards(
            st, last_recs["ranked"], last_recs.get("relaxed", False), last_recs.get("relax_reason")
        )
    elif last_weather:
        _render_weather_card(st, last_weather)
    else:
        st.markdown(
            '<div class="cta-context-empty">Ask about a town to see live weather and '
            "match scores here.</div>",
            unsafe_allow_html=True,
        )
