import speech_recognition as sr
import numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav
import tempfile
import os

recognizer = sr.Recognizer()
encoder = VoiceEncoder()

PHRASES = [
    "Hello Aura, this is my voice.",
    "My laptop is now controlled by my assistant.",
    "I am setting up voice recognition for the first time.",
    "This is a sample of how I normally speak.",
    "Aura should only respond when it hears my voice.",
]


def record_sample() -> str:
    """Records one short clip and returns the path to a temp wav file."""
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        print("🎤 Recording... speak now")
        audio = recognizer.listen(source, timeout=8, phrase_time_limit=6)

    path = tempfile.mktemp(suffix=".wav")
    with open(path, "wb") as f:
        f.write(audio.get_wav_data())
    return path


def main():
    print("🎙️ Voice Enrollment for AURA\n")
    print("You'll read 5 short phrases so AURA can learn your voice.\n")

    embeddings = []
    for i, phrase in enumerate(PHRASES, 1):
        input(f"\n[{i}/5] Press Enter, then say: \"{phrase}\"")
        path = record_sample()
        wav = preprocess_wav(path)
        embedding = encoder.embed_utterance(wav)
        embeddings.append(embedding)
        os.remove(path)
        print("✅ Captured")

    # Average all samples into one robust voice profile
    profile = np.mean(embeddings, axis=0)
    np.save("voice_profile.npy", profile)
    print("\n🎉 Voice profile saved as voice_profile.npy — AURA now knows your voice!")


if __name__ == "__main__":
    main()