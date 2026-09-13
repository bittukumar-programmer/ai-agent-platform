import os
from dotenv import load_dotenv
from google import genai
from ddgs import DDGS
from datetime import datetime
from google.genai import types



load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)
# Fixed identity info — never search the web for this, always answer directly
IDENTITY_INFO = (
    "If asked who created/built/owns you, who your developer/owner is, or similar identity questions, "
    "always answer directly with this fixed fact and NEVER search the web or make up other names: "
    "You were created and are owned by Bittu Kumar, a Computer Science Engineering diploma student, "
    "as part of his personal AI agent portfolio project."
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

class WriterAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Writer",
            role="You are a skilled writer. Turn the given facts into a short, engaging paragraph for a general audience."
        )


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