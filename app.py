import streamlit as st
from agents import Coordinator

# Page setup
st.set_page_config(page_title="AI Agent Platform", page_icon="🤖")
st.title("🤖 Multi-Agent AI Platform")
st.write("Researcher → Writer → Reviewer (with self-correction) work together on your topic")

# Get topic from user
topic = st.text_input("What topic should we work on?")

if st.button("Start"):
    if topic:
        coordinator = Coordinator()

        with st.spinner("Researcher is working..."):
            research = coordinator.researcher.run(f"Topic: {topic}")
        st.subheader("🔍 Research")
        st.write(research)

        draft = None
        feedback = ""
        max_attempts = 2

        for attempt in range(1, max_attempts + 1):
            with st.spinner(f"Writer is working... (attempt {attempt})"):
                if attempt == 1:
                    draft = coordinator.writer.run(f"Topic: {topic}\nFacts:\n{research}")
                else:
                    draft = coordinator.writer.run(
                        f"Topic: {topic}\nFacts:\n{research}\n\n"
                        f"Previous attempt was rejected for this reason: {feedback}\n"
                        f"Write a better version."
                    )

            with st.spinner(f"Reviewer is checking... (attempt {attempt})"):
                check = coordinator.reviewer.run(
                    f"Topic: {topic}\nDraft:\n{draft}\n\n"
                    f"Reply with EXACTLY ONE WORD/LINE and nothing else. "
                    f"If this is accurate, clear and well written, reply only: GOOD\n"
                    f"If it needs improvement, reply only: NEEDS_WORK: <short reason>\n"
                    f"Do not add any other text, explanation, or punctuation."
                )

            if check.strip().startswith("GOOD"):
                st.success(f"✅ Approved on attempt {attempt}")
                break
            else:
                feedback = check.replace("NEEDS_WORK:", "").strip()
                st.info(f"🔁 Attempt {attempt} needs work: {feedback}")

        st.subheader("📝 Final Result")
        st.write(draft)
    else:
        st.warning("Please enter a topic first")