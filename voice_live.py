import asyncio
import os
import pyaudio
from google import genai
from google.genai import types
from dotenv import load_dotenv
from manager import ManagerAgent
from voice_manager import wait_for_wake_word, play_yes_sir, prepare_yes_sir_clip

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-3.8-live"
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_RATE = 16000
RECEIVE_RATE = 24000
CHUNK = 1024

pya = pyaudio.PyAudio()
manager = ManagerAgent()

# This tool lets the Live model hand off real tasks (system control, research, office files,
# WhatsApp, etc.) to our existing 20+ agent pipeline, instead of trying to answer them itself.
run_agent_task_tool = {
    "function_declarations": [
        {
            "name": "run_agent_task",
            "description": (
                "Use this for ANY request that requires actually doing something or looking something "
                "up — controlling the laptop, opening apps, creating files/folders, creating Word/Excel/"
                "PowerPoint files, sending WhatsApp messages, searching the web, checking news, fact-checking, "
                "writing code, doing exact math, translating, summarizing, planning, or any specialized task. "
                "Do NOT use this for simple greetings or casual conversation — handle those yourself directly."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "request": {"type": "string", "description": "The user's request, as they said it"}
                },
                "required": ["request"],
            },
        }
    ]
}

CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
        )
    ),
    tools=[run_agent_task_tool],
    system_instruction=(
        "You are AURA, a personal AI assistant speaking to your user, Bittu. Always address him as "
        "'Sir'. Be natural, warm, and conversational, like Jarvis from Iron Man. Keep responses concise. "
        "For simple conversation, greetings, or questions you can answer yourself, just answer directly. "
        "For anything requiring real action or lookup, call the run_agent_task tool."
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

    async def handle_tool_call(self, tool_call):
        for fc in tool_call.function_calls:
            if fc.name == "run_agent_task":
                request = fc.args.get("request", "")
                print(f"🧠 Routing to agent pipeline: {request}")
                result, image = await asyncio.to_thread(manager.execute, request)
                await self.session.send_tool_response(
                    function_responses=[
                        types.FunctionResponse(id=fc.id, name=fc.name, response={"result": result})
                    ]
                )

    async def receive_audio(self):
        while True:
            turn = self.session.receive()
            async for response in turn:
                if data := response.data:
                    self.audio_in_queue.put_nowait(data)
                if response.tool_call:
                    await self.handle_tool_call(response.tool_call)

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
    prepare_yes_sir_clip()
    while True:
        wait_for_wake_word()
        play_yes_sir()
        asyncio.run(LiveAura().run())