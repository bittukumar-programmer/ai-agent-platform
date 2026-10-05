import asyncio
import os
import pyaudio
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-3.8-live"
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_RATE = 16000
RECEIVE_RATE = 24000
CHUNK = 1024

pya = pyaudio.PyAudio()

CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
        )
    ),
    system_instruction=(
        "You are AURA, a personal AI assistant, speaking to your user named Bittu. "
        "Always address him as 'Sir'. Be natural, warm, and conversational, like Jarvis "
        "from Iron Man. Keep responses concise unless asked for detail."
    ),
)


class LiveAura:
    def __init__(self):
        self.audio_in_queue = asyncio.Queue()
        self.out_queue = asyncio.Queue(maxsize=20)
        self.session = None

    async def listen_mic(self):
        mic_info = pya.get_default_input_device_info()
        stream = await asyncio.to_thread(
            pya.open, format=FORMAT, channels=CHANNELS, rate=SEND_RATE,
            input=True, input_device_index=mic_info["index"], frames_per_buffer=CHUNK,
        )
        while True:
            data = await asyncio.to_thread(stream.read, CHUNK, exception_on_overflow=False)
            await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})

    async def send_audio(self):
        while True:
            msg = await self.out_queue.get()
            await self.session.send_realtime_input(audio=msg)

    async def receive_audio(self):
        while True:
            turn = self.session.receive()
            async for response in turn:
                if data := response.data:
                    self.audio_in_queue.put_nowait(data)
                if text := response.text:
                    print(f"AURA: {text}")

    async def play_audio(self):
        stream = await asyncio.to_thread(
            pya.open, format=FORMAT, channels=CHANNELS, rate=RECEIVE_RATE, output=True
        )
        while True:
            data = await self.audio_in_queue.get()
            await asyncio.to_thread(stream.write, data)

    async def run(self):
        async with client.aio.live.connect(model=MODEL, config=CONFIG) as session:
            self.session = session
            print("🎙️ AURA (Live) is listening — speak naturally, you can even interrupt it.")
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.listen_mic())
                tg.create_task(self.send_audio())
                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())


if __name__ == "__main__":
    asyncio.run(LiveAura().run())