import streamlit as st
from manager import ManagerAgent

st.set_page_config(page_title="Agent Deck", page_icon="◆", layout="centered")

# ---- Custom styling: a dark "mission control" console theme ----
st.markdown("""
<style>
    :root {
        --bg: #0d1117;
        --panel: #141a21;
        --line: #232b33;
        --text: #e6edf3;
        --dim: #7d8590;
        --research: #4fc3a1;
        --write: #e8a33d;
        --review: #6ea8fe;
    }

    .stApp { background: var(--bg); }
    html, body, [class*="css"] { color: var(--text); }

    /* Header block */
    .deck-header { padding: 1.2rem 0 0.4rem 0; border-bottom: 1px solid var(--line); margin-bottom: 1.2rem; }
    .deck-title { font-family: 'Courier New', monospace; font-size: 1.7rem; letter-spacing: -0.02em; margin: 0; }
    .deck-sub { color: var(--dim); font-size: 0.9rem; margin-top: 0.3rem; }

    /* Agent pipeline pills */
    .plan-strip { display: flex; gap: 0.4rem; margin: 0.5rem 0 0.8rem 0; font-family: 'Courier New', monospace; font-size: 0.78rem; }
    .plan-pill { padding: 0.15rem 0.55rem; border-radius: 3px; border: 1px solid var(--line); color: var(--dim); }
    .plan-pill.research { border-color: var(--research); color: var(--research); }
    .plan-pill.write { border-color: var(--write); color: var(--write); }
    .plan-pill.review { border-color: var(--review); color: var(--review); }

    /* Chat bubbles */
    [data-testid="stChatMessage"] { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; }

    /* Chat input */
    [data-testid="stChatInput"] textarea { font-family: 'Courier New', monospace; }
</style>
""", unsafe_allow_html=True)

# ---- Header ----
st.markdown("""
<div class="deck-header">
    <p class="deck-title">◆ Agent Deck</p>
    <p class="deck-sub">Manager plans the route · Research → Write → Review agents execute it</p>
</div>
""", unsafe_allow_html=True)

# ---- State ----
if "manager" not in st.session_state:
    st.session_state.manager = ManagerAgent()

if "messages" not in st.session_state:
    st.session_state.messages = []

AGENT_ICON = {"user": "🧑", "assistant": "🤖"}

# ---- Replay history ----
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=AGENT_ICON[msg["role"]]):
        if msg.get("plan"):
            pills = "".join(
                f'<span class="plan-pill {s}">{s}</span>' for s in msg["plan"]
            )
            st.markdown(f'<div class="plan-strip">{pills}</div>', unsafe_allow_html=True)
        st.write(msg["content"])

# ---- New input ----
user_input = st.chat_input("What do you need?")

if user_input:
    with st.chat_message("user", avatar=AGENT_ICON["user"]):
        st.write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant", avatar=AGENT_ICON["assistant"]):
        with st.spinner("Agents at work..."):
            steps = st.session_state.manager.plan(user_input)
            if steps:
                pills = "".join(f'<span class="plan-pill {s}">{s}</span>' for s in steps)
                st.markdown(f'<div class="plan-strip">{pills}</div>', unsafe_allow_html=True)
            result = st.session_state.manager.execute(user_input, steps=steps)
            st.write(result)

    st.session_state.messages.append({"role": "assistant", "content": result, "plan": steps})