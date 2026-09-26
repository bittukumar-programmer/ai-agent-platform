import speech_recognition as sr
import pyttsx3
from manager import ManagerAgent
import os
import wave
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
tts_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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
    """Converts text to natural-sounding speech using Gemini TTS and plays it aloud."""
    try:
        response = tts_client.models.generate_content(
            model="gemini-3.8-flash-tts",
            contents=[{"role": "user", "parts": [{"text": text}]}],
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
                    )
                ),
            ),
        )
        audio_data = response.candidates[0].content.parts[0].inline_data.data

        # Save as a WAV file and play it
        wav_path = "temp_response.wav"
        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(audio_data)

        from playsound3 import playsound
        playsound(wav_path)
    except Exception as e:
        print(f"⚠️ TTS error, falling back to offline voice: {e}")
        # Fallback to old offline method if Gemini TTS fails (e.g. no internet)
        import pyttsx3
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