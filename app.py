import streamlit as st
from agents import Coordinator

# पेज का title और basic setup
st.set_page_config(page_title="AI Agent Platform", page_icon="🤖")
st.title("🤖 Multi-Agent AI Platform")
st.write("Researcher → Writer → Reviewer, तीनों एजेंट्स मिलकर आपके सवाल पर काम करेंगे")

# यूज़र से टॉपिक लेना
topic = st.text_input("किस टॉपिक पर काम करना है?")

# बटन दबाने पर काम शुरू हो
if st.button("शुरू करें"):
    if topic:
        coordinator = Coordinator()
        
        with st.spinner("Researcher काम कर रहा है..."):
            research = coordinator.researcher.run(f"Topic: {topic}")
        st.subheader("🔍 Research")
        st.write(research)
        
        with st.spinner("Writer काम कर रहा है..."):
            draft = coordinator.writer.run(f"Topic: {topic}\nFacts:\n{research}")
        st.subheader("✍️ Draft")
        st.write(draft)
        
        with st.spinner("Reviewer काम कर रहा है..."):
            final_output = coordinator.reviewer.run(f"Topic: {topic}\nDraft:\n{draft}")
        st.subheader("📝 Final Result")
        st.write(final_output)
    else:
        st.warning("पहले कोई टॉपिक लिखें")