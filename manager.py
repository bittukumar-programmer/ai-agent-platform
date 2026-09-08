import os
import json
from dotenv import load_dotenv
from google import genai
from agents import ResearcherAgent, WriterAgent, ReviewerAgent

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)


class ManagerAgent:
    """
    Decides which agents are needed for a given task, and in what order.
    Also remembers recent conversation history so it can understand
    follow-up requests like "make it shorter" or "add more about that".
    """

    def __init__(self):
        self.researcher = ResearcherAgent()
        self.writer = WriterAgent()
        self.reviewer = ReviewerAgent()
        self.history = []  # stores {"task": ..., "result": ...} for past turns

    def _history_text(self) -> str:
        """Turns the recent history into a short text block for context."""
        if not self.history:
            return "No previous conversation."
        lines = []
        for i, turn in enumerate(self.history[-3:], 1):  # only last 3 turns
            lines.append(f"Turn {i} - User asked: {turn['task']}")
            lines.append(f"Turn {i} - Result: {turn['result'][:300]}")  # trim long results
        return "\n".join(lines)

    def plan(self, task: str) -> list:
        """Asks the LLM to decide which steps are needed for this task."""
        prompt = (
            "You are a planning manager for a team of AI agents. "
            "Available agents: 'research' (gathers facts), 'write' (turns facts into a paragraph), "
            "'review' (checks and polishes the final text).\n\n"
            f"Recent conversation:\n{self._history_text()}\n\n"
            f"New task: {task}\n\n"
            "Decide which agents are needed and in what order for this NEW task. "
            "If the new task refers to something from the recent conversation "
            "(like 'make it shorter' or 'add more'), take that into account. "
            "Reply with ONLY a JSON list of steps, nothing else. Examples:\n"
            '["research", "write", "review"]\n'
            '["write"]\n'
            '["research", "write"]\n'
        )
        response = client.models.generate_content(
            model="gemini-flash-lite-latest",
            contents=prompt,
        )
        raw = response.text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        try:
            steps = json.loads(raw)
        except json.JSONDecodeError:
            steps = ["research", "write", "review"]
        return steps

    def execute(self, task: str):
        steps = self.plan(task)
        print(f"\n🧠 Manager decided the steps: {steps}\n")

        # Include recent history in the task context so agents understand follow-ups
        context_task = f"Recent conversation:\n{self._history_text()}\n\nNew request: {task}"

        research = ""
        draft = ""

        for step in steps:
            if step == "research":
                print("🔍 Researcher is working...")
                research = self.researcher.run(f"Topic: {context_task}")
                print(f"Research:\n{research}\n")

            elif step == "write":
                print("✍️ Writer is working...")
                writer_input = f"Topic: {context_task}"
                if research:
                    writer_input += f"\nFacts:\n{research}"
                draft = self.writer.run(writer_input)
                print(f"Draft:\n{draft}\n")

            elif step == "review":
                print("🔎 Reviewer is working...")
                draft = self.reviewer.run(
                    f"Topic: {context_task}\nDraft:\n{draft}\n\n"
                    f"Improve this for accuracy, clarity, and flow. "
                    f"Reply with ONLY the final improved paragraph. "
                    f"Do NOT include any feedback, headings, explanations, or commentary."
                )
                print(f"Reviewed:\n{draft}\n")

        # Save this turn to history for future context
        self.history.append({"task": task, "result": draft})

        return draft


if __name__ == "__main__":
    manager = ManagerAgent()
    print("AI Agent Manager ready! Type your request (or 'exit' to quit)\n")

    while True:
        task = input("What do you need? ")
        if task.lower() == "exit":
            print("Goodbye!")
            break

        result = manager.execute(task)
        print(f"\n📝 Final Result:\n{result}\n")
        print("-" * 50)