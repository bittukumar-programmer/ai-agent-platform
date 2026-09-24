import os
from dotenv import load_dotenv
from google import genai
from ddgs import DDGS
from datetime import datetime
from google.genai import types
from system_control import open_notepad, create_folder, create_file, open_vscode, close_app


load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)
# Fixed identity info — never search the web for this, always answer directly
IDENTITY_INFO = (
    "If, and ONLY if, the user explicitly asks who created/built/owns you or a similar identity question, "
    "answer directly with this fixed fact and NEVER search the web or make up other names: "
    "You were created and are owned by Bittu Kumar, a Computer Science Engineering diploma student, "
    "as part of his personal AI agent portfolio project. "
    "Do NOT mention this fact, or bring it up, in any response where the user did not ask about it."
)



def get_current_datetime() -> str:
    """Returns the current date and time."""
    now = datetime.now()
    return now.strftime("%A, %d %B %Y, %I:%M %p")



def web_search(query: str, max_results: int = 4) -> str:
    """Searches the web and returns a text summary of top results."""
    try:
        results = DDGS().text(query, max_results=max_results)
        if not results:
            return "No search results found."
        formatted = []
        for r in results:
            formatted.append(f"- {r['title']}: {r['body']}")
        return "\n".join(formatted)
    except Exception as e:
        return f"[Search failed: {e}]"



def calculate(expression: str) -> str:
    """Safely evaluates a math expression and returns the exact result."""
    try:
        # Only allow safe characters (numbers, operators, parentheses, decimal point)
        allowed = set("0123456789+-*/(). ")
        if not all(char in allowed for char in expression):
            return "Error: expression contains invalid characters."
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e}"

def generate_image(prompt: str):
    """Generates an image from a text prompt. Returns PIL Image object or None on failure."""
    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-image",
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
        )
        for part in response.parts:
            if part.inline_data:
                return part.as_image()
        return None
    except Exception as e:
        print(f"Image generation failed: {e}")
        return None
class BaseAgent:
    """Base template for all agents. Every agent inherits from this."""

    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role  # This defines the agent's job/personality


    def run(self, prompt: str) -> str:
        """Sends a prompt to the model and returns the response. Retries on network errors."""
        full_prompt = (
            f"{self.role}\n\n"
            f"{IDENTITY_INFO}\n\n"
            f"IMPORTANT: Always reply in the SAME language the user used "
            f"(English, Hindi, or Hinglish). Match their language exactly.\n\n"
            f"Task: {prompt}"
        )

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                response = client.models.generate_content(
                    model="gemini-flash-lite-latest",
                    contents=full_prompt,
                )
                return response.text
            except Exception as e:
                print(f"⚠️ {self.name} hit a network error (attempt {attempt}/{max_retries}): {e}")
                if attempt == max_retries:
                    return f"[Error: {self.name} could not get a response after {max_retries} attempts. Please try again.]"

        return "[Unexpected error]"


class ResearcherAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Researcher",
            role="You are a research assistant. Give 4-5 key facts, just bullet points, no extra text."
        )

    def run(self, prompt: str) -> str:
        """First searches the web for current info, then summarizes it into facts."""
        print("   🌐 Searching the web...")
        search_results = web_search(prompt)

        full_prompt = (
            f"{self.role}\n\n"
            f"IMPORTANT: Always reply in the SAME language the user used "
            f"(English, Hindi, or Hinglish). Match their language exactly.\n\n"
            f"Here are live web search results:\n{search_results}\n\n"
            f"Task: {prompt}\n\n"
            f"Using the search results above, give 4-5 key facts as bullet points. "
            f"Prefer information from the search results over your own memory, "
            f"since the search results are more current."
        )

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                response = client.models.generate_content(
                    model="gemini-flash-lite-latest",
                    contents=full_prompt,
                )
                return response.text
            except Exception as e:
                print(f"⚠️ {self.name} hit a network error (attempt {attempt}/{max_retries}): {e}")
                if attempt == max_retries:
                    return f"[Error: {self.name} could not get a response after {max_retries} attempts.]"

        return "[Unexpected error]"



class CreativeAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Creative",
            role=(
                "You are a witty, warm creative writer. You can write short stories, poems, jokes, "
                "playful roasts, and emotional or motivational messages. "
                "Always write ORIGINAL content — never reproduce existing copyrighted poems, lyrics, or jokes. "
                "Keep roasts light-hearted, funny, and affectionate — never mean, never about real people, "
                "and never touching sensitive topics like religion, caste, or race. "
                "If asked to base something on the previous conversation, use that context creatively. "
                "If asked for something random, feel free to pick any fun theme yourself."
            )
        )


class CodeAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Coder",
            role=(
                "You are an expert software engineer. Write clean, correct, well-commented code "
                "in the language the user asks for (default to Python if unspecified). "
                "If asked to explain code, break it down clearly, line by line if needed. "
                "If asked to debug code, find the bug, explain why it happens, and give the fixed code. "
                "Always wrap code in markdown code blocks with the correct language tag."
            )
        )


class MathAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Math",
            role="You are a math assistant that explains calculations clearly using exact computed results."
        )

    def run(self, prompt: str) -> str:
        """Extracts the math expression, computes it exactly, then explains the result."""
        extraction_prompt = (
            f"Extract ONLY the pure math expression from this request, using just numbers and "
            f"+ - * / ( ) . nothing else, no words. If there are multiple operations, "
            f"combine them into one expression. Reply with ONLY the expression.\n\n"
            f"Request: {prompt}"
        )
        response = client.models.generate_content(
            model="gemini-flash-lite-latest",
            contents=extraction_prompt,
        )
        expression = response.text.strip()
        exact_result = calculate(expression)

        full_prompt = (
            f"{self.role}\n\n"
            f"{IDENTITY_INFO}\n\n"
            f"The exact computed answer to '{expression}' is: {exact_result}\n\n"
            f"Task: {prompt}\n\n"
            f"Give a short, clear answer using this EXACT computed result. Do not recalculate yourself."
        )
        response = client.models.generate_content(
            model="gemini-flash-lite-latest",
            contents=full_prompt,
        )
        return response.text


class TranslatorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Translator",
            role=(
                "You are an expert translator. Translate the given text accurately into the "
                "language the user asks for, preserving tone and meaning. If no target language "
                "is specified but the request implies one, infer it. Reply with ONLY the translation, "
                "unless the user also asks for an explanation."
            )
        )

class SummarizerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Summarizer",
            role=(
                "You are an expert at summarizing text. Take the given text and condense it into "
                "the key points, keeping only what matters. Use bullet points for clarity unless "
                "the user asks for a paragraph. Be concise — a summary should always be much shorter "
                "than the original."
            )
        )

class PlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Planner",
            role=(
                "You are an expert planner and organizer. Break down goals, projects, or tasks into "
                "clear, actionable steps or a to-do list. Keep steps specific and realistic, and order "
                "them logically. Use numbered or bulleted lists."
            )
        )

class InterviewCoachAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="InterviewCoach",
            role=(
                "You are an experienced technical interview coach for software engineering roles at "
                "top companies. Help with behavioral question answers (using the STAR method: Situation, "
                "Task, Action, Result), give constructive feedback on practice answers, and offer tips "
                "for technical or HR interview rounds. Be encouraging but honest about what could improve."
            )
        )

class ResumeAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Resume",
            role=(
                "You are an expert resume and cover letter writer for software engineering roles. "
                "Turn plain descriptions of projects or experience into strong, quantified resume bullet "
                "points (using action verbs and metrics where possible), or write concise, tailored cover "
                "letters. Keep language professional, concrete, and free of fluff or exaggeration."
            )
        )

class TutorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Tutor",
            role=(
                "You are a patient, clear teacher. Explain concepts step by step in simple language, "
                "using examples or analogies where helpful. If asked, create practice questions with "
                "answers to test understanding. Adjust your depth to match how the question is phrased — "
                "keep it simple unless the user asks for more detail."
            )
        )

class EmailAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Email",
            role=(
                "You are an expert at writing clear, professional emails. Draft emails based on the "
                "user's request — job applications, follow-ups, requests, or general correspondence. "
                "Include an appropriate subject line. Keep tone polite and to the point, adapting "
                "formality to the context described."
            )
        )
class NewsAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="News",
            role=(
                "You are a news digest assistant. Summarize current news on the requested topic in a "
                "clear, neutral, headline-style format — a short headline followed by 1-2 sentences per "
                "story. Stick strictly to what the search results say; never invent details."
            )
        )

    def run(self, prompt: str) -> str:
        """Searches the web for current news, then formats it as a digest."""
        print("   🌐 Searching for news...")
        search_results = web_search(f"latest news headlines {prompt} today", max_results=6)

        full_prompt = (
            f"{self.role}\n\n"
            f"{IDENTITY_INFO}\n\n"
            f"Here are live web search results:\n{search_results}\n\n"
            f"Task: {prompt}\n\n"
            f"Using ONLY the search results above, give a short news digest."
        )

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                response = client.models.generate_content(
                    model="gemini-flash-lite-latest",
                    contents=full_prompt,
                )
                return response.text
            except Exception as e:
                print(f"⚠️ {self.name} hit a network error (attempt {attempt}/{max_retries}): {e}")
                if attempt == max_retries:
                    return f"[Error: {self.name} could not get a response after {max_retries} attempts.]"

        return "[Unexpected error]"

class ProofreaderAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Proofreader",
            role=(
                "You are an expert proofreader and editor. Fix grammar, spelling, punctuation, and "
                "clarity issues in the given text while preserving the original meaning and tone. "
                "If asked, briefly list what you changed and why. Otherwise, just give the corrected text."
            )
        )

class RecipeAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Recipe",
            role=(
                "You are a helpful cooking assistant. Suggest recipes based on ingredients the user "
                "has, dietary preferences, or cravings. Give clear step-by-step instructions with "
                "approximate quantities and cooking times. Keep it practical for a home kitchen."
            )
        )
class TravelAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Travel",
            role=(
                "You are a helpful travel planning assistant. Suggest destinations, create rough "
                "day-by-day itineraries, or give practical travel tips based on the user's budget, "
                "duration, and interests. Keep suggestions realistic and well-organized."
            )
        )

class DecisionAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Decision",
            role=(
                "You are a thoughtful decision-making assistant. When the user is torn between options, "
                "lay out the pros and cons of each clearly, consider what matters most given their context, "
                "and give a balanced recommendation while respecting that it's ultimately their choice. "
                "Never be pushy — help them think clearly, don't decide for them."
            )
        )


class FactCheckAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="FactCheck",
            role=(
                "You are a careful fact-checker. Verify claims using the live search results provided. "
                "Clearly state whether the claim appears TRUE, FALSE, or UNCLEAR based on the evidence, "
                "explain why, and cite what the sources say. Be honest about uncertainty — never guess."
            )
        )

    def run(self, prompt: str) -> str:
        """Searches the web to verify a claim, then gives a verdict."""
        print("   🌐 Searching to verify claim...")
        search_results = web_search(prompt, max_results=5)

        full_prompt = (
            f"{self.role}\n\n"
            f"{IDENTITY_INFO}\n\n"
            f"Here are live web search results:\n{search_results}\n\n"
            f"Claim to check: {prompt}\n\n"
            f"Based ONLY on the search results above, give a verdict (TRUE / FALSE / UNCLEAR) and explain why."
        )

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                response = client.models.generate_content(
                    model="gemini-flash-lite-latest",
                    contents=full_prompt,
                )
                return response.text
            except Exception as e:
                print(f"⚠️ {self.name} hit a network error (attempt {attempt}/{max_retries}): {e}")
                if attempt == max_retries:
                    return f"[Error: {self.name} could not get a response after {max_retries} attempts.]"

        return "[Unexpected error]"

class SystemAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="System",
            role=(
                "You control the user's laptop. Based on the request, decide which action to take: "
                "open_notepad, create_folder, create_file, open_vscode, or close_app. "
                "Reply with ONLY a JSON object like: "
                '{"action": "create_folder", "params": {"folder_name": "MyProjects"}}\n'
                "Valid actions and their params:\n"
                '- open_notepad: {"filename": "optional.txt"}\n'
                '- create_folder: {"folder_name": "name"}\n'
                '- create_file: {"filename": "name.txt", "folder_name": "optional", "content": "optional text"}\n'
                '- open_vscode: {"path": "optional path"}\n'
                '- close_app: {"app_name": "notepad.exe or Code.exe"}\n'
                "Reply with ONLY the JSON, nothing else."
            )
        )

    def run(self, prompt: str) -> str:
        """Figures out which system action to take, then actually performs it."""
        import json
        response = client.models.generate_content(
            model="gemini-flash-lite-latest",
            contents=f"{self.role}\n\nUser request: {prompt}",
        )
        raw = response.text.strip().replace("```json", "").replace("```", "").strip()

        try:
            decision = json.loads(raw)
            action = decision.get("action")
            params = decision.get("params", {})

            if action == "open_notepad":
                return open_notepad(**params)
            elif action == "create_folder":
                return create_folder(**params)
            elif action == "create_file":
                return create_file(**params)
            elif action == "open_vscode":
                return open_vscode(**params)
            elif action == "close_app":
                return close_app(**params)
            else:
                return "I couldn't figure out which action to take."
        except Exception as e:
            return f"Error performing system action: {e}"

class WriterAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Writer",
            role="You are a skilled writer. Turn the given facts into a short, engaging paragraph for a general audience."
        )


class WriterAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Writer",
            role="You are a skilled writer. Turn the given facts into a short, engaging paragraph for a general audience."
        )

    def run_with_image(self, prompt: str, image) -> str:
        """Answers a question about an uploaded image."""
        try:
            response = client.models.generate_content(
                model="gemini-flash-lite-latest",
                contents=[image, prompt],
            )
            return response.text
        except Exception as e:
            return f"[Error analyzing image: {e}]"

class ReviewerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Reviewer",
            role="You are an editor. Review the given paragraph for accuracy, clarity, and flow."
        )


class Coordinator:
    """Runs all agents in the correct order, with self-correction if needed."""

    def __init__(self):
        self.researcher = ResearcherAgent()
        self.writer = WriterAgent()
        self.reviewer = ReviewerAgent()

    def run(self, topic: str, max_attempts: int = 2):
        print(f"\n🔍 {self.researcher.name} is working...")
        research = self.researcher.run(f"Topic: {topic}")
        print(f"Research found:\n{research}\n")

        draft = None
        feedback = ""
        for attempt in range(1, max_attempts + 1):
            print(f"✍️ {self.writer.name} is working... (attempt {attempt})")

            if attempt == 1:
                draft = self.writer.run(f"Topic: {topic}\nFacts:\n{research}")
            else:
                draft = self.writer.run(
                    f"Topic: {topic}\nFacts:\n{research}\n\n"
                    f"Previous attempt was rejected for this reason: {feedback}\n"
                    f"Write a better version."
                )
            print(f"Draft:\n{draft}\n")

            print(f"🔎 {self.reviewer.name} is checking...")
            check = self.reviewer.run(
                f"Topic: {topic}\nDraft:\n{draft}\n\n"
                f"Reply with EXACTLY ONE WORD/LINE and nothing else. "
                f"If this is accurate, clear and well written, reply only: GOOD\n"
                f"If it needs improvement, reply only: NEEDS_WORK: <short reason>\n"
                f"Do not add any other text, explanation, or punctuation."
            )
            print(f"Reviewer decision: {check}\n")

            if check.strip().startswith("GOOD"):
                print("✅ Approved by reviewer!")
                return draft
            else:
                feedback = check.replace("NEEDS_WORK:", "").strip()

        print("⚠️ Max attempts reached, returning last version")
        return draft


if __name__ == "__main__":
    topic = input("What topic should we work on? ")
    coordinator = Coordinator()
    final = coordinator.run(topic)
    print(f"\n📝 Final Result:\n{final}")