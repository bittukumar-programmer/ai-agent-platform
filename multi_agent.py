import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

def researcher_agent(topic: str) -> str:
    """ये एजेंट किसी टॉपिक के बारे में मुख्य जानकारी इकट्ठा करता है"""
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=f"Give me 4-5 key facts about: {topic}. Just bullet points, no extra text.",
    )
    return response.text

def writer_agent(topic: str, research: str) -> str:
    """ये एजेंट रिसर्च को एक अच्छे पैराग्राफ में बदलता है"""
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=f"Using these facts:\n{research}\n\nWrite a short, engaging paragraph about {topic} for a general audience.",
    )
    return response.text

def reviewer_agent(topic: str, draft: str) -> str:
    """ये एजेंट Writer के आउटपुट को चेक करके सुधारा हुआ फाइनल वर्ज़न देता है"""
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=f"Review this paragraph about {topic}:\n\n{draft}\n\nCheck for accuracy, clarity, and flow. Then give ONLY the improved final version, no extra comments.",
    )
    return response.text

def coordinator(topic: str):
    """तीनों एजेंट्स को सही क्रम में चलाता है"""
    print(f"\n🔍 Researcher काम कर रहा है...")
    research = researcher_agent(topic)
    print(f"Research मिली:\n{research}\n")

    print(f"✍️ Writer काम कर रहा है...")
    draft = writer_agent(topic, research)
    print(f"Draft मिला:\n{draft}\n")

    print(f"🔎 Reviewer काम कर रहा है...")
    final_output = reviewer_agent(topic, draft)
    print(f"\n📝 Final Reviewed Result:\n{final_output}")

# चलाना
topic = input("किस टॉपिक पर काम करना है? ")
coordinator(topic)