import os
import re
import time
import wave
import asyncio
import edge_tts
import speech_recognition as sr
from google import genai
from google.genai import types
from dotenv import load_dotenv
from manager import ManagerAgent

import numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav
import tempfile

voice_encoder = VoiceEncoder()
MY_VOICE_PROFILE = np.load("voice_profile.npy")
VOICE_MATCH_THRESHOLD = 0.65

from playsound3 import playsound

load_dotenv()
tts_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
recognizer = sr.Recognizer()

WAKE_WORD = "aura"
AWAKE_MINUTES = 90  # how long AURA stays actively listening after being woken

# Friendly names for the "working on it" message
AGENT_FRIENDLY_NAMES = {
    "research": "Research agent", "write": "Writer", "review": "Reviewer",
    "creative": "Creative agent", "code": "Coding agent", "math": "Math agent",
    "image": "Image generator", "translate": "Translator", "summarize": "Summarizer",
    "plan": "Planner", "interview": "Interview coach", "resume": "Resume agent",
    "tutor": "Tutor", "email": "Email agent", "news": "News agent",
    "proofread": "Proofreader", "recipe": "Recipe agent", "travel": "Travel agent",
    "decision": "Decision helper", "factcheck": "Fact-checker", "system": "System control agent",
    "office": "Office agent", "datetime": "Clock",
}

# Agents slow enough to deserve a "working on it" message instead of silence
SLOW_AGENTS = {"research", "news", "factcheck", "image", "office", "system"}


VOICE = "en-IN-NeerjaNeural"  # Natural Indian-English voice that also handles Hindi/Hinglish well


async def _generate_speech(text: str, path: str):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(path)


def clean_for_speech(text: str) -> str:
    """Removes markdown symbols and other characters that shouldn't be spoken aloud."""
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)   # **bold** → bold
    text = re.sub(r"\*(.*?)\*", r"\1", text)        # *italic* → italic
    text = re.sub(r"#+\s*", "", text)               # remove markdown headings (#, ##, ###)
    text = re.sub(r"`(.*?)`", r"\1", text)           # `code` → code
    text = re.sub(r"[_~]", "", text)                 # remove underscores, tildes
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)  # remove bullet point markers
    text = re.sub(r"\n+", ". ", text)                # newlines → pause-like period
    return text.strip()




def speak(text: str):
    """Converts text to natural speech using free, unlimited Edge TTS and plays it."""
    try:
        clean_text = clean_for_speech(text)
        wav_path = "temp_response.mp3"
        asyncio.run(_generate_speech(clean_text, wav_path))
        playsound(wav_path)
    except Exception as e:
        print(f"⚠️ TTS error, falling back to offline voice: {e}")
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", 175)
        engine.say(text)
        engine.runAndWait()
        engine.stop()


def prepare_yes_sir_clip():
    """Pre-generates the 'Yes Sir?' acknowledgment once at startup for instant playback later."""
    global YES_SIR_PATH
    try:
        YES_SIR_PATH = "yes_sir.mp3"
        asyncio.run(_generate_speech("Yes Sir?", YES_SIR_PATH))
    except Exception:
        YES_SIR_PATH = None

        
def play_yes_sir():
    if YES_SIR_PATH:
        playsound(YES_SIR_PATH)
    else:
        speak("Yes Sir?")



def is_my_voice(audio) -> bool:
    """Checks if the given audio matches the enrolled voice profile."""
    try:
        path = tempfile.mktemp(suffix=".wav")
        with open(path, "wb") as f:
            f.write(audio.get_wav_data())

        wav = preprocess_wav(path)
        embedding = voice_encoder.embed_utterance(wav)
        os.remove(path)

        similarity = np.dot(embedding, MY_VOICE_PROFILE) / (
            np.linalg.norm(embedding) * np.linalg.norm(MY_VOICE_PROFILE)
        )
        print(f"   (voice match score: {similarity:.2f})")
        return similarity >= VOICE_MATCH_THRESHOLD
    except Exception as e:
        print(f"⚠️ Voice check failed: {e}")
        return True


def listen_once(timeout=6, phrase_time_limit=8) -> str:
    """Listens for one utterance, checks it's your voice, and returns the text, or '' otherwise."""
    try:
        with sr.Microphone() as source:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

        if not is_my_voice(audio):
            print("🚫 Voice doesn't match — ignoring.")
            return ""

        return recognizer.recognize_google(audio).strip()
    except (sr.UnknownValueError, sr.WaitTimeoutError, sr.RequestError):
        return ""


WAKE_WORD_VARIANTS = ["aura", "ora", "arrow", "aurora", "ura", "howrah", "aara", "aira", "ara", "era"]

def wait_for_wake_word():
    """Quietly listens until the wake word is heard. Keeps the mic open the whole time for instant response."""
    print(f"\n💤 Sleeping... (say '{WAKE_WORD}' to wake me up)")
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        recognizer.pause_threshold = 0.5  # shorter pause = faster detection after you finish speaking

        while True:
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
            except sr.WaitTimeoutError:
                continue

            try:
                text = recognizer.recognize_google(audio).lower()
                print(f"   (heard: {text})")
                if any(variant in text for variant in WAKE_WORD_VARIANTS):
                    if is_my_voice(audio):
                        print("✅ Wake word detected, and it's your voice!")
                        return
                    else:
                        print("🚫 Wake word heard, but voice doesn't match — ignoring.")
            except (sr.UnknownValueError, sr.RequestError):
                continue


def is_directed_at_assistant(text: str) -> bool:
    """Quick check: is this utterance actually meant for AURA, or just ambient conversation nearby?"""
    prompt = (
        "You are deciding whether a spoken sentence, overheard by an AI assistant named AURA while "
        "actively listening, is a command/question DIRECTED AT the assistant, or just ambient background "
        "conversation (e.g. the user talking to a friend, thinking aloud unrelated to the assistant, or "
        "background noise/unclear speech) that should be ignored.\n\n"
        f"Sentence: \"{text}\"\n\n"
        "Reply with EXACTLY ONE WORD: RESPOND or IGNORE."
    )
    try:
        result = tts_client.models.generate_content(
            model="gemini-flash-lite-latest", contents=prompt
        )
        return "RESPOND" in result.text.strip().upper()
    except Exception:
        return True  # if the check fails, default to responding rather than staying silent forever


def active_session(manager: ManagerAgent):
    """Stays actively listening after being woken, without needing the wake word again, until AWAKE_MINUTES pass."""
    session_end = time.time() + AWAKE_MINUTES * 60

    while time.time() < session_end:
        print("\n👂 Listening (active session)...")
        text = listen_once(timeout=8, phrase_time_limit=10)

        if not text:
            continue

        print(f"Heard: {text}")

        if text.lower() in ["sleep", "stop listening", "go to sleep"]:
            speak("Going back to sleep, Sir.")
            return

        if not is_directed_at_assistant(text):
            print("   (ignored — not directed at AURA)")
            continue

        session_end = time.time() + AWAKE_MINUTES * 60  # reset timer on real interaction

        steps = manager.plan(text)
        primary_agent = steps[0] if steps else "write"

        if primary_agent in SLOW_AGENTS:
            friendly = AGENT_FRIENDLY_NAMES.get(primary_agent, "the right agent")
            speak(f"Sir, I'm on it — putting the {friendly} to work. I'll let you know as soon as I have it.")

        result, image = manager.execute(text, steps=steps)
        print(f"\n📝 Response: {result}\n")
        speak(result)

    print("⏰ Active session timed out, going back to sleep.")


if __name__ == "__main__":
    manager = ManagerAgent()
    print("🎙️ AURA is running in the background.")
    prepare_yes_sir_clip()

    while True:
        wait_for_wake_word()
        play_yes_sir()
        active_session(manager)