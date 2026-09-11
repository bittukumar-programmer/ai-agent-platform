
# 🤖 Agent Deck — Multi-Agent AI Platform


🔗 **Live Demo:** [ai-agent-platform-fjdy2ipwfkqvxcuictc75j.streamlit.app](https://ai-agent-platform-fjdy2ipwfkqvxcuictc75j.streamlit.app)

A multi-agent AI system where a **Manager Agent** dynamically plans which specialized agents (Researcher, Writer, Reviewer) are needed for a given task — instead of running a fixed pipeline every time.

## Features

- **Dynamic planning** — the Manager decides in real time whether a task needs research, writing, review, or just a direct reply.
- **Self-correction loop** — the Writer and Reviewer go back and forth until the output is approved, instead of settling for a first draft.
- **Conversation memory** — remembers recent turns, so follow-up requests like "make it shorter" work naturally.
- **Multi-language support** — replies in English, Hindi, or Hinglish, matching whatever language the user typed in.
- **Error handling** — automatically retries on network/API failures instead of crashing.
- **Web interface** — a chat-style UI built with Streamlit, showing which agents worked on each response.

## Tech Stack

- Python
- Google Gemini API (`google-genai`)
- Streamlit (web interface)

## How It Works

1. User sends a request.
2. The **Manager Agent** analyzes it and decides which steps are needed (e.g. `["research", "write", "review"]`).
3. Each required agent runs in order, passing its output to the next.
4. If the Reviewer isn't satisfied, the Writer retries with feedback (self-correction).
5. The final response is returned, and the exchange is saved to memory for future context.

## Running Locally

```bash
# Clone the repo
git clone https://github.com/bittukumar-programmer/ai-agent-platform.git
cd ai-agent-platform

# Set up a virtual environment
python -m venv venv
venv\Scripts\activate      # Windows

# Install dependencies
pip install google-genai python-dotenv streamlit

# Add your Gemini API key
echo GEMINI_API_KEY=your_key_here > .env

# Run in terminal
python manager.py

# Or run the web interface
streamlit run app.py
```

## Project Status

This is an ongoing project, actively being developed with new agent capabilities and features added regularly.