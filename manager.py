import os
import json
from memory_store import load_memory, save_memory
from dotenv import load_dotenv
from agents import ResearcherAgent, WriterAgent, ReviewerAgent, CreativeAgent, CodeAgent, MathAgent
from google import genai
from agents import ResearcherAgent, WriterAgent, ReviewerAgent, CreativeAgent, CodeAgent, MathAgent, TranslatorAgent, SummarizerAgent, PlannerAgent, InterviewCoachAgent, ResumeAgent
from agents import ResearcherAgent, WriterAgent, ReviewerAgent, CreativeAgent, CodeAgent, MathAgent, TranslatorAgent
from agents import ResearcherAgent, WriterAgent, ReviewerAgent, CreativeAgent, CodeAgent, MathAgent, TranslatorAgent, SummarizerAgent
from agents import ResearcherAgent, WriterAgent, ReviewerAgent, CreativeAgent, CodeAgent, MathAgent, TranslatorAgent, SummarizerAgent, PlannerAgent
from agents import ResearcherAgent, WriterAgent, ReviewerAgent, CreativeAgent, CodeAgent, MathAgent, TranslatorAgent, SummarizerAgent, PlannerAgent, InterviewCoachAgent
from agents import ResearcherAgent, WriterAgent, ReviewerAgent, CreativeAgent, CodeAgent, MathAgent, TranslatorAgent, SummarizerAgent, PlannerAgent, InterviewCoachAgent, ResumeAgent, TutorAgent
from agents import ResearcherAgent, WriterAgent, ReviewerAgent, CreativeAgent, CodeAgent, MathAgent, TranslatorAgent, SummarizerAgent, PlannerAgent, InterviewCoachAgent, ResumeAgent, TutorAgent, EmailAgent
from agents import ResearcherAgent, WriterAgent, ReviewerAgent, CreativeAgent, CodeAgent, MathAgent, TranslatorAgent, SummarizerAgent, PlannerAgent, InterviewCoachAgent, ResumeAgent, TutorAgent, EmailAgent, NewsAgent
from agents import ResearcherAgent, WriterAgent, ReviewerAgent, CreativeAgent, CodeAgent, MathAgent, TranslatorAgent, SummarizerAgent, PlannerAgent, InterviewCoachAgent, ResumeAgent, TutorAgent, EmailAgent, NewsAgent, ProofreaderAgent
from agents import ResearcherAgent, WriterAgent, ReviewerAgent, CreativeAgent, CodeAgent, MathAgent, TranslatorAgent, SummarizerAgent, PlannerAgent, InterviewCoachAgent, ResumeAgent, TutorAgent, EmailAgent, NewsAgent, ProofreaderAgent, RecipeAgent
from agents import ResearcherAgent, WriterAgent, ReviewerAgent, CreativeAgent, CodeAgent, MathAgent, TranslatorAgent, SummarizerAgent, PlannerAgent, InterviewCoachAgent, ResumeAgent, TutorAgent, EmailAgent, NewsAgent, ProofreaderAgent, RecipeAgent, TravelAgent
from agents import ResearcherAgent, WriterAgent, ReviewerAgent, CreativeAgent, CodeAgent, MathAgent, TranslatorAgent, SummarizerAgent, PlannerAgent, InterviewCoachAgent, ResumeAgent, TutorAgent, EmailAgent, NewsAgent, ProofreaderAgent, RecipeAgent, TravelAgent, DecisionAgent
from agents import ResearcherAgent, WriterAgent, ReviewerAgent, CreativeAgent, CodeAgent, MathAgent, TranslatorAgent, SummarizerAgent, PlannerAgent, InterviewCoachAgent, ResumeAgent, TutorAgent, EmailAgent, NewsAgent, ProofreaderAgent, RecipeAgent, TravelAgent, DecisionAgent, FactCheckAgent
from agents import ResearcherAgent, WriterAgent, ReviewerAgent, CreativeAgent, CodeAgent
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)
from agents import get_current_datetime, generate_image


class ManagerAgent:
    """
    Decides which agents are needed for a given task, and in what order.
    Also remembers recent conversation history so it can understand
    follow-up requests like "make it shorter" or "add more about that".
    """

    def __init__(self):
        self.researcher = ResearcherAgent()
        self.creative = CreativeAgent()
        self.writer = WriterAgent()
        self.reviewer = ReviewerAgent()
        self.history = load_memory()  # load past conversation history from local file
        self.coder = CodeAgent()
        self.math = MathAgent()
        self.translator = TranslatorAgent()
        self.summarizer = SummarizerAgent()
        self.planner = PlannerAgent()
        self.interview_coach = InterviewCoachAgent()
        self.resume = ResumeAgent()
        self.tutor = TutorAgent()
        self.email = EmailAgent()
        self.news = NewsAgent()
        self.proofreader = ProofreaderAgent()
        self.recipe = RecipeAgent()
        self.travel = TravelAgent()
        self.decision = DecisionAgent()
        self.factcheck = FactCheckAgent()

    def _history_text(self) -> str:
        """Turns the recent history into a short text block for context."""
        if not self.history:
            return "No previous conversation."
        lines = []
        for i, turn in enumerate(self.history[-3:], 1):  # only last 3 turns
            lines.append(f"Turn {i} - User asked: {turn['task']}")
            lines.append(f"Turn {i} - Result: {turn['result'][:300]}")  # trim long results
        return "\n".join(lines)

    def plan(self, task: str, has_image: bool = False) -> list:
        """Asks the LLM to decide which steps are needed for this task."""
        prompt = (
            "You are a planning manager for a team of AI agents. "
            "You are a planning manager for a team of AI agents. "
            + ("An image has been attached by the user — if their request is about the image, use ['write'] so the Writer can analyze it.\n\n" if has_image else "")
            + "If the task is asking about your identity, creator, owner, or developer, "
            "If the task is asking about your identity, creator, owner, or developer, "
            "NEVER use 'research' (do not search the web for this) — just use ['write'].\n\n"
            "Available agents: 'research' (gathers facts, use for general knowledge questions), "
            "'creative' (writes original stories, poems, jokes, playful roasts, or emotional/motivational "
            "messages — use for entertainment or creative requests, NOT factual ones), "

            "'creative' (writes original stories, poems, jokes, playful roasts, or emotional/motivational "
            "messages — use for entertainment or creative requests, NOT factual ones), "
            "'code' (writes, explains, or debugs code, or explains programming/CS concepts like loops, "
            "functions, data structures, algorithms — use this for ANY programming or computer-science-related "
            "request instead of 'research'), "
            "'math' (does EXACT calculations — use for any arithmetic or math computation request), "
            "'image' (generates a picture from a text description — use ONLY when the user explicitly "
            "asks to create/draw/generate an image or picture), "
            "'translate' (translates text into another language — use when the user explicitly asks "
            "to translate something), "

            "'summarize' (condenses long text into key points — use when the user gives you text "
            "and asks to summarize, shorten, or condense it), "
            "'plan' (breaks a goal or task into a step-by-step to-do list — use when the user asks "
            "how to approach, organize, or plan something), "
             "'interview' (helps practice interview answers, gives feedback using STAR method, or shares "
            "interview tips — use for job interview preparation requests), "
            "'resume' (writes or improves resume bullet points or cover letters — use for resume/CV "
            "or job application writing requests), "
            "'tutor' (explains concepts step by step like a teacher, or creates practice questions — "
            "use when the user wants to learn or understand a topic, not just get quick facts), "
            "'email' (drafts professional emails with a subject line — use when the user asks to "
            "write or draft an email), "
            "'news' (gets a live news digest on a topic — use when the user specifically asks for "
            "news, headlines, or 'what's happening' on a topic), "
            "'proofread' (fixes grammar, spelling, and clarity in given text — use when the user gives "
            "text and asks to check, correct, fix, or proofread it), "
            "'recipe' (suggests recipes and cooking instructions — use for food/cooking-related "
            "requests), "
            "'travel' (suggests destinations, itineraries, or travel tips — use for trip/vacation "
            "planning requests), "
             
            "'datetime' (gets the current real date and time, use ONLY when the user asks about today's date, current time, or day of the week), "
            "'write' (turns facts into a paragraph), "
            "'review' (checks and polishes the final text).\n\n"
            f"Recent conversation:\n{self._history_text()}\n\n"
            f"New task: {task}\n\n"

            "IMPORTANT RULE: 'travel', 'recipe', 'interview', 'tutor', 'email', 'resume', 'creative', "
            "'code', 'math', 'translate', 'summarize', 'plan', 'news', and 'proofread' agents already "
            "produce a complete, well-formatted final answer on their own — do NOT chain 'write' or "
            "'review' after them, just use them alone (e.g. ['travel']). Only use 'write' and 'review' "
            "together with 'research' for general knowledge questions.\n\n"
            "Decide which agents are needed and in what order for this NEW task. "
            "'decision' (helps weigh pros/cons of a difficult choice — use when the user is torn "
            "between options and wants help deciding), "

            "'factcheck' (verifies if a claim/statement is true or false using live search — use when "
            "the user asks to verify, check, or fact-check something), "
    
            "Decide which agents are needed and in what order for this NEW task. "
            "If the new task refers to something from the recent conversation "
            "(like 'make it shorter' or 'add more'), take that into account. "
            "Reply with ONLY a JSON list of steps, nothing else. Examples:\n"
            '["research", "write", "review"]\n'
            '["write"]\n'
            '["research", "write"]\n'
            '["datetime", "write"]\n'
            '["creative"]\n'
            '["code"]\n'
            '["math"]\n'
            '["image"]\n'
            '["translate"]\n'
            '["summarize"]\n'
            '["plan"]\n'
            '["interview"]\n'
            '["resume"]\n'
            '["tutor"]\n'
            '["email"]\n'
            '["news"]\n'
            '["proofread"]\n'
            '["recipe"]\n'
            '["travel"]\n'
            '["decision"]\n'
            '["factcheck"]\n'
            
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

    def execute(self, task: str, steps: list = None, image=None):
        if steps is None:
            steps = self.plan(task)
        print(f"\n🧠 Manager decided the steps: {steps}\n")

        # Include recent history in the task context so agents understand follow-ups
        context_task = f"Recent conversation:\n{self._history_text()}\n\nNew request: {task}"

        research = ""
        draft = ""
        generated_image = None

        for step in steps:
            if step == "research":
                print("🔍 Researcher is working...")
                research = self.researcher.run(f"Topic: {context_task}")
                print(f"Research:\n{research}\n")

            elif step == "datetime":
                from agents import get_current_datetime
                print("🕐 Getting current date/time...")
                research = f"Current date and time: {get_current_datetime()}"
                print(f"{research}\n")

            elif step == "write":
                print("✍️ Writer is working...")
                writer_input = f"Topic: {context_task}"
                if research:
                    writer_input += f"\nFacts:\n{research}"
                if image is not None:
                    draft = self.writer.run_with_image(writer_input, image)
                else:
                    draft = self.writer.run(writer_input)


            elif step == "code":

                print("💻 Code agent is working...")
                draft = self.coder.run(context_task)
                print(f"Draft:\n{draft}\n")

            elif step == "math":
                print("🔢 Math agent is working...")
                draft = self.math.run(context_task)
                print(f"Draft:\n{draft}\n")

            elif step == "translate":
                print("🌐 Translator is working...")
                draft = self.translator.run(context_task)
                print(f"Draft:\n{draft}\n")

            elif step == "summarize":
                print("📋 Summarizer is working...")
                draft = self.summarizer.run(context_task)
                print(f"Draft:\n{draft}\n")

            elif step == "plan":
                print("📅 Planner is working...")
                draft = self.planner.run(context_task)
                print(f"Draft:\n{draft}\n")

            elif step == "interview":
                print("🎤 Interview Coach is working...")
                draft = self.interview_coach.run(context_task)
                print(f"Draft:\n{draft}\n")

            elif step == "resume":
                print("📄 Resume agent is working...")
                draft = self.resume.run(context_task)
                print(f"Draft:\n{draft}\n")

            elif step == "tutor":
                print("📚 Tutor is working...")
                draft = self.tutor.run(context_task)
                print(f"Draft:\n{draft}\n")

            elif step == "email":
                print("📧 Email agent is working...")
                draft = self.email.run(context_task)
                print(f"Draft:\n{draft}\n")


            elif step == "news":
                print("📰 News agent is working...")
                draft = self.news.run(task)
                print(f"Draft:\n{draft}\n")

            elif step == "proofread":
                print("✔️ Proofreader is working...")
                draft = self.proofreader.run(context_task)
                print(f"Draft:\n{draft}\n")

            elif step == "recipe":
                print("🍳 Recipe agent is working...")
                draft = self.recipe.run(context_task)
                print(f"Draft:\n{draft}\n")

            elif step == "travel":
                print("✈️ Travel agent is working...")
                draft = self.travel.run(context_task)
                print(f"Draft:\n{draft}\n")

            elif step == "factcheck":
                print("✅ Fact-checker is working...")
                draft = self.factcheck.run(task)
                print(f"Draft:\n{draft}\n")

            elif step == "decision":
                print("🤔 Decision helper is working...")
                draft = self.decision.run(context_task)
                print(f"Draft:\n{draft}\n")

            elif step == "image":
                print("🎨 Generating image...")
                generated_image = generate_image(task)
                draft = "Here's the image you asked for!" if generated_image else "Sorry, I couldn't generate the image."

            elif step == "review":
                print("🔎 Reviewer is working...")
                draft = self.reviewer.run(
                    f"Topic: {context_task}\nDraft:\n{draft}\n\n"
                    f"Improve this for accuracy, clarity, and flow. "
                    f"Reply with ONLY the final improved paragraph. "
                    f"Do NOT include any feedback, headings, explanations, or commentary."
                )
                print(f"Reviewed:\n{draft}\n")

                        # Fallback: if no steps were needed (e.g. simple greeting), just respond directly
        if not draft:
            draft = self.writer.run(
                f"{context_task}\n\nThis is a simple conversational message (like a greeting). "
                f"Reply naturally and briefly, like a helpful assistant would."
            )

        # Save this turn to history for future context
        self.history.append({"task": task, "result": draft})
        save_memory(self.history)

        return draft, generated_image


if __name__ == "__main__":
    manager = ManagerAgent()
    print("AI Agent Manager ready! Type your request (or 'exit' to quit)\n")

    while True:
        task = input("What do you need? ")
        if task.lower() == "exit":
            print("Goodbye!")
            break

        result, image = manager.execute(task)
        print(f"\n📝 Final Result:\n{result}\n")
        if image:
            image.save("generated_image.png")
            print("🖼️ Image saved as generated_image.png\n")
        print("-" * 50)