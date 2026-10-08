import json
import threading
import webview
from voice_manager import wait_for_wake_word, play_yes_sir, prepare_yes_sir_clip
from manager import ManagerAgent
import asyncio
import pyaudio
from google import genai
from google.genai import types
import os
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
manager = ManagerAgent()

window = None  # set once the webview window is created

# Maps our 20+ agent names to the 4 visual "squad" cards in the HUD
AGENT_BUCKETS = {
    "write": "agent-strategist", "plan": "agent-strategist", "decision": "agent-strategist",
    "interview": "agent-strategist", "tutor": "agent-strategist",
    "math": "agent-analytics", "code": "agent-analytics", "office": "agent-analytics", "summarize": "agent-analytics",
    "research": "agent-research", "news": "agent-research", "factcheck": "agent-research",
    "translate": "agent-research", "recipe": "agent-research", "travel": "agent-research",
    "system": "agent-operations", "email": "agent-operations", "resume": "agent-operations",
    "proofread": "agent-operations", "creative": "agent-operations", "image": "agent-operations",
    "datetime": "agent-operations",
}


def ui_set_state(state: str):
    if window:
        window.evaluate_js(f"setOrbState('{state}')")


def ui_log(source: str, msg: str):
    if window:
        safe_msg = json.dumps(msg)
        window.evaluate_js(f"addLog('{source}', {safe_msg})")


def ui_set_agent(agent_name: str, state: str):
    bucket = AGENT_BUCKETS.get(agent_name, "agent-strategist")
    if window:
        window.evaluate_js(f"setAgentActive('{bucket}', '{state}')")


run_agent_task_tool = {
    "function_declarations": [{
        "name": "run_agent_task",
        "description": (
            "Use this for ANY request that requires actually doing something or looking something up — "
            "controlling the laptop, opening apps, creating files, Office documents, sending WhatsApp "
            "messages, web search, news, fact-checking, code, math, translation, summarizing, planning, "
            "or any specialized task. Do NOT use for simple greetings or casual conversation."
        ),
        "parameters": {
            "type": "object",
            "properties": {"request": {"type": "string", "description": "The user's request"}},
            "required": ["request"],
        },
    }]
}

CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore"))
    ),
    tools=[run_agent_task_tool],
    input_audio_transcription={},
    output_audio_transcription={},
    system_instruction=(
        "You are AURA, a personal AI assistant speaking to your user, Bittu. Always address him as 'Sir'. "
        "Be natural, warm, and conversational, like Jarvis from Iron Man. Keep responses concise. "
        "For simple conversation, answer directly. For anything requiring real action or lookup, call "
        "the run_agent_task tool."
    ),
)


class LiveAura:
    def __init__(self):
        self.audio_in_queue = asyncio.Queue()
        self.out_queue = asyncio.Queue(maxsize=20)
        self.session = None
        self.aura_speaking = False  # tracks whether AURA is currently talking

    async def listen_mic(self):
        mic_info = pya.get_default_input_device_info()
        stream = await asyncio.to_thread(
            pya.open, format=FORMAT, channels=CHANNELS, rate=SEND_RATE,
            input=True, input_device_index=mic_info["index"], frames_per_buffer=CHUNK,
        )
        ui_set_state("listening")
        while True:
            data = await asyncio.to_thread(stream.read, CHUNK, exception_on_overflow=False)
            await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})

    async def send_audio(self):
        while True:
            msg = await self.out_queue.get()
            if not self.aura_speaking:  # don't send mic audio while AURA is talking, to avoid echo
                await self.session.send_realtime_input(audio=msg)

    async def handle_tool_call(self, tool_call):
        for fc in tool_call.function_calls:
            if fc.name == "run_agent_task":
                request = fc.args.get("request", "")
                ui_set_state("thinking")
                steps = await asyncio.to_thread(manager.plan, request)
                primary = steps[0] if steps else "write"
                ui_set_agent(primary, "thinking")
                ui_log("SYSTEM", f"Routing to {primary} agent: {request}")
                result, image = await asyncio.to_thread(manager.execute, request, steps)
                ui_set_agent(primary, "active")
                await self.session.send_tool_response(
                    function_responses=[types.FunctionResponse(id=fc.id, name=fc.name, response={"result": result})]
                )

    async def receive_audio(self):
        while True:
            turn = self.session.receive()
            async for response in turn:
                if data := response.data:
                    self.aura_speaking = True
                    ui_set_state("speaking")
                    self.audio_in_queue.put_nowait(data)
                if response.tool_call:
                    await self.handle_tool_call(response.tool_call)
                if response.server_content:
                    if it := response.server_content.input_transcription:
                        if it.text:
                            ui_log("USER", it.text)
                    if ot := response.server_content.output_transcription:
                        if ot.text:
                            ui_log("AURA", ot.text)
                    if response.server_content.turn_complete:
                        self.aura_speaking = False
                        ui_set_state("listening")

    async def play_audio(self):
        stream = await asyncio.to_thread(pya.open, format=FORMAT, channels=CHANNELS, rate=RECEIVE_RATE, output=True)
        while True:
            data = await self.audio_in_queue.get()
            await asyncio.to_thread(stream.write, data)

    async def run(self):
        async with client.aio.live.connect(model=MODEL, config=CONFIG) as session:
            self.session = session
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.listen_mic())
                tg.create_task(self.send_audio())
                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())


def backend_loop():
    prepare_yes_sir_clip()
    ui_log("SYSTEM", "AURA Core Orchestrator Online.")
    while True:
        ui_set_state("idle")
        wait_for_wake_word()
        ui_log("SYSTEM", "Wake word detected, verifying speaker...")
        play_yes_sir()

        proactive_msg = manager.proactive_check()
        if proactive_msg:
            ui_log("AURA", proactive_msg)
            # Speak it before starting the live session
            import asyncio as _a
            from voice_manager import speak as offline_speak
            _a.get_event_loop_policy()  # ensure a loop exists
            try:
                offline_speak(proactive_msg)
            except Exception:
                pass
        else:
            ui_log("AURA", "Yes Sir?")

        asyncio.run(LiveAura().run())


def start_app(win):
    global window
    window = win
    threading.Thread(target=backend_loop, daemon=True).start()


if __name__ == "__main__":
    w = webview.create_window("AURA", "dashboard/index.html", width=1400, height=850, background_color="#02050a")
    webview.start(start_app, w)