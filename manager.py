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
    This is the 'brain' that plans before any work is done.
    """

    def __init__(self):
        self.researcher = ResearcherAgent()
        self.writer = WriterAgent()
        self.reviewer = ReviewerAgent()

    def plan(self, task: str) -> list:
        """
        Asks the LLM to decide which steps are needed for this task.
        Returns a list like ["research", "write", "review"] or a subset of it.
        """
        prompt = (
            "You are a planning manager for a team of AI agents. "
            "Available agents: 'research' (gathers facts), 'write' (turns facts into a paragraph), "
            "'review' (checks and polishes the final text).\n\n"
            f"Task: {task}\n\n"
            "Decide which agents are needed and in what order. "
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
        # Clean up if the model wraps the JSON in markdown code blocks
        raw = raw.replace("```json", "").replace("```", "").strip()
        try:
            steps = json.loads(raw)
        except json.JSONDecodeError:
            # Fallback: if parsing fails, just run the full pipeline
            steps = ["research", "write", "review"]
        return steps

    def execute(self, task: str):
        steps = self.plan(task)
        print(f"\n🧠 Manager decided the steps: {steps}\n")

        research = ""
        draft = ""

        for step in steps:
            if step == "research":
                print("🔍 Researcher is working...")
                research = self.researcher.run(f"Topic: {task}")
                print(f"Research:\n{research}\n")

            elif step == "write":
                print("✍️ Writer is working...")
                context = f"Topic: {task}"
                if research:
                    context += f"\nFacts:\n{research}"
                draft = self.writer.run(context)
                print(f"Draft:\n{draft}\n")

            elif step == "review":
                print("🔎 Reviewer is working...")
                draft = self.reviewer.run(
                    f"Topic: {task}\nDraft:\n{draft}\n\n"
                    f"Improve this for accuracy, clarity, and flow. "
                    f"Reply with ONLY the final improved paragraph. "
                    f"Do NOT include any feedback, headings, explanations, or commentary."
                )
                print(f"Reviewed:\n{draft}\n")
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