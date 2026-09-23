import speech_recognition as sr
import pyttsx3
from manager import ManagerAgent

# Setup speech recognition (listening) and text-to-speech (speaking)
recognizer = sr.Recognizer()
 


def listen() -> str:
    """Listens through the microphone and converts speech to text."""
    with sr.Microphone() as source:
        print("\n🎤 Listening... (speak now)")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source)

    print("🧠 Transcribing...")
    try:
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("⚠️ Couldn't understand that, try again.")
        return ""
    except sr.RequestError as e:
        print(f"⚠️ Speech recognition error: {e}")
        return ""


def speak(text: str):
    """Converts text to speech and plays it aloud. Creates a fresh engine each time to avoid Windows TTS freezing on repeated use."""
    engine = pyttsx3.init()
    engine.setProperty("rate", 175)
    engine.say(text)
    engine.runAndWait()
    engine.stop()


if __name__ == "__main__":
    manager = ManagerAgent()
    print("🎙️ Voice Assistant ready! Say 'exit' or 'stop' to quit.\n")
    speak("Voice assistant ready. How can I help you?")

    while True:
        user_input = listen()

        if not user_input:
            continue

        if user_input.lower() in ["exit", "stop", "quit"]:
            speak("Goodbye!")
            break

        result, image = manager.execute(user_input)
        print(f"\n📝 Response: {result}\n")
        speak(result)