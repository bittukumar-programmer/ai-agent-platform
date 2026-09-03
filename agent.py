import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# एक टूल (function) जो असली कैलकुलेशन करता है
def calculator(expression: str) -> str:
    """गणित का सवाल हल करता है, जैसे '15 * 23' या '100 / 4'"""
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e}"

# चैट सेशन बनाना, calculator टूल के साथ
chat = client.chats.create(
    model="gemini-3.6-flash",
    config=types.GenerateContentConfig(
        tools=[calculator],
        system_instruction="You are a helpful assistant. Use the calculator tool for any math."
    )
)

print("AI Agent तैयार है! बात करना शुरू करें (बंद करने के लिए 'exit' टाइप करें)\n")

# लगातार सवाल लेने वाला loop
while True:
    user_input = input("आप: ")
    if user_input.lower() == "exit":
        print("अलविदा!")
        break
    
    response = chat.send_message(user_input)
    print("Agent:", response.text)
    print()