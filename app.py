import streamlit as st
from manager import ManagerAgent
from agents import get_current_datetime

st.set_page_config(page_title="Agent Deck", page_icon="◆", layout="centered")

st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
    :root {
        --bg: #07080c;
        --panel: #12141c;
        --panel2: #171a24;
        --text: #eef0f6;
        --dim: #8a8fa3;
        --accent: #7c8cff;
        --research: #2dd4bf;
        --write: #f5a623;
        --review: #5b8def;
    }

    #MainMenu, footer, header { visibility: hidden; height: 0; }
    .block-container { padding-top: 2rem !important; max-width: 760px; }

    .stApp {
        background:
            radial-gradient(circle at 15% -10%, rgba(124,140,255,0.15), transparent 40%),
            var(--bg);
    }
    html, body, [class*="css"], .stMarkdown p, .stMarkdown li {
        color: var(--text) !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* ---- Agent roster strip ---- */
    .roster { display: flex; gap: 0.5rem; margin-bottom: 1.6rem; flex-wrap: wrap; }
    .roster-chip {
        font-family: 'JetBrains Mono', monospace !important; font-size: 0.72rem;
        padding: 0.3rem 0.7rem; border-radius: 6px; border: 1px solid;
        display: flex; align-items: center; gap: 0.4rem;
    }
    .roster-chip .dot { width: 6px; height: 6px; border-radius: 50%; }
    .roster-chip.manager { border-color: rgba(124,140,255,0.35); color: var(--accent); }
    .roster-chip.manager .dot { background: var(--accent); }
    .roster-chip.research { border-color: rgba(45,212,191,0.35); color: var(--research); }
    .roster-chip.research .dot { background: var(--research); }
    .roster-chip.write { border-color: rgba(245,166,35,0.35); color: var(--write); }
    .roster-chip.write .dot { background: var(--write); }
    .roster-chip.review { border-color: rgba(91,141,239,0.35); color: var(--review); }
    .roster-chip.review .dot { background: var(--review); }

    /* ---- Hero ---- */
    .hero { margin-bottom: 0.3rem; }
    .hero-title {
        font-family: 'Space Grotesk', sans-serif !important; font-size: 2.4rem !important; font-weight: 700 !important;
        letter-spacing: -0.02em; line-height: 1.15; margin: 0 !important; max-width: 520px;
        color: var(--text) !important;
    }
    .hero-sub { color: var(--dim) !important; font-size: 1rem; margin-top: 0.7rem; max-width: 480px; line-height: 1.55; }
    .section-label { color: var(--dim); font-size: 0.85rem; margin: 1.8rem 0 0.7rem 0; }

    /* ---- Quick task cards ---- */
    div[data-testid="stButton"] button {
        background: linear-gradient(160deg, var(--panel2), var(--panel));
        border: 1px solid rgba(255,255,255,0.07) !important;
        border-left: 3px solid var(--card-accent, var(--accent)) !important;
        border-radius: 10px !important;
        text-align: left; padding: 1rem 1.1rem !important;
        width: 100%; height: 100%;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    div[data-testid="stButton"] button p {
        white-space: pre-line !important; color: var(--dim) !important; font-size: 0.85rem !important; margin: 0 !important; line-height: 1.5;
    }
    div[data-testid="stButton"] button p::first-line {
        font-family: 'Space Grotesk', sans-serif !important; font-size: 1.02rem !important; font-weight: 600 !important; color: var(--text) !important;
    }
    div[data-testid="stButton"] button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 26px rgba(0,0,0,0.35);
    }
    div[data-testid="column"]:nth-of-type(1) div[data-testid="stButton"]:nth-of-type(1) button { --card-accent: var(--research); }
    div[data-testid="column"]:nth-of-type(2) div[data-testid="stButton"]:nth-of-type(1) button { --card-accent: var(--review); }
    div[data-testid="column"]:nth-of-type(1) div[data-testid="stButton"]:nth-of-type(2) button { --card-accent: var(--write); }
    div[data-testid="column"]:nth-of-type(2) div[data-testid="stButton"]:nth-of-type(2) button { --card-accent: var(--accent); }

    /* ---- Chat ---- */
    [data-testid="stChatMessage"] { border-radius: 12px; border: 1px solid rgba(255,255,255,0.06); }
    [data-testid="stChatMessage"]:nth-of-type(even) { background: var(--panel); }
    [data-testid="stChatInput"] textarea { font-family: 'Inter', sans-serif !important; }

    /* ---- Plan pills ---- */
    .plan-strip { display: flex; gap: 0.4rem; margin: 0 0 0.7rem 0; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; }
    .plan-pill { padding: 0.15rem 0.55rem; border-radius: 20px; border: 1px solid rgba(255,255,255,0.1); color: var(--dim); }
    .plan-pill.research { border-color: var(--research); color: var(--research); }
    .plan-pill.write { border-color: var(--write); color: var(--write); }
    .plan-pill.review { border-color: var(--review); color: var(--review); }
    .plan-pill.datetime { border-color: var(--accent); color: var(--accent); }
</style>
""", unsafe_allow_html=True)

# ---- State ----
if "manager" not in st.session_state:
    st.session_state.manager = ManagerAgent()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_input" not in st.session_state:
    st.session_state.pending_input = None

AGENT_ICON = {"user": "🧑", "assistant": "🤖"}


def render_plan_pills(steps):
    pills = "".join(f'<span class="plan-pill {s}">{s}</span>' for s in steps)
    st.markdown(f'<div class="plan-strip">{pills}</div>', unsafe_allow_html=True)


# ---- Hero + quick tasks (only before the first message) ----
if not st.session_state.messages:
    st.markdown("""
    <div class="roster">
        <span class="roster-chip manager"><span class="dot"></span>Manager · plans</span>
        <span class="roster-chip research"><span class="dot"></span>Research · gathers</span>
        <span class="roster-chip write"><span class="dot"></span>Write · drafts</span>
        <span class="roster-chip review"><span class="dot"></span>Review · polishes</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="hero">
        <p class="hero-title">What should the team work on?</p>
        <p class="hero-sub">{get_current_datetime()} — tell the Manager what you need, and it decides which agents above actually need to run.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<p class="section-label">Try one of these</p>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✎  Quick answer\nExplain gravity in one line", use_container_width=True):
            st.session_state.pending_input = "Explain gravity in one line"
        if st.button("📰  Full article\nWrite a short article about black holes", use_container_width=True):
            st.session_state.pending_input = "Write a short article about black holes"
    with col2:
        if st.button("🌐  Live web lookup\nWhat's the latest on ISRO's missions?", use_container_width=True):
            st.session_state.pending_input = "What's the latest on ISRO's missions?"
        if st.button("🕐  Right now\nWhat's the date and time today?", use_container_width=True):
            st.session_state.pending_input = "What's the date and time today?"

# ---- Replay history ----
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=AGENT_ICON[msg["role"]]):
        if msg.get("plan"):
            render_plan_pills(msg["plan"])
        st.write(msg["content"])

# ---- New input ----
typed_input = st.chat_input("What do you need?")
user_input = st.session_state.pending_input or typed_input
st.session_state.pending_input = None

if user_input:
    with st.chat_message("user", avatar=AGENT_ICON["user"]):
        st.write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant", avatar=AGENT_ICON["assistant"]):
        with st.spinner("Agents at work..."):
            steps = st.session_state.manager.plan(user_input)
            if steps:
                render_plan_pills(steps)
            result = st.session_state.manager.execute(user_input, steps=steps)
            st.write(result)

    st.session_state.messages.append({"role": "assistant", "content": result, "plan": steps})