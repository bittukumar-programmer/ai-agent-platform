import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)


class BaseAgent:
    """हर एजेंट का बुनियादी ढांचा, बाकी एजेंट्स इसी से बनेंगे"""
    
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role  # ये एजेंट का काम क्या है, ये बताता है (system instruction जैसा)
    
    def run(self, prompt: str) -> str:
        """ये फंक्शन एजेंट को असली सवाल भेजता है और जवाब लाता है"""
        full_prompt = f"{self.role}\n\nTask: {prompt}"
        response = client.models.generate_content(
            model="gemini-flash-lite-latest",
            contents=full_prompt,
        )
        return response.text


class ResearcherAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Researcher",
            role="You are a research assistant. Give 4-5 key facts, just bullet points, no extra text."
        )


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
            role="You are an editor. Review the given paragraph for accuracy, clarity, and flow. Give ONLY the improved final version, no extra comments."
        )


class Coordinator:
    """ये सभी एजेंट्स को सही क्रम में चलाता है"""
    
    def __init__(self):
        self.researcher = ResearcherAgent()
        self.writer = WriterAgent()
        self.reviewer = ReviewerAgent()
    
    def run(self, topic: str):
        print(f"\n🔍 {self.researcher.name} काम कर रहा है...")
        research = self.researcher.run(f"Topic: {topic}")
        print(f"Research मिली:\n{research}\n")

        print(f"✍️ {self.writer.name} काम कर रहा है...")
        draft = self.writer.run(f"Topic: {topic}\nFacts:\n{research}")
        print(f"Draft मिला:\n{draft}\n")

        print(f"🔎 {self.reviewer.name} काम कर रहा है...")
        final_output = self.reviewer.run(f"Topic: {topic}\nDraft:\n{draft}")
        print(f"\n📝 Final Result:\n{final_output}")
        
        return final_output


if __name__ == "__main__":
    topic = input("किस टॉपिक पर काम करना है? ")
    coordinator = Coordinator()
    coordinator.run(topic)