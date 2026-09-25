import tkinter as tk
import threading
from manager import ManagerAgent
from voice_manager import listen, speak

COLORS = {
    "idle": "#3a3f4b",
    "listening": "#2dd4bf",
    "thinking": "#f5a623",
    "speaking": "#5b8def",
}

BG = "#050608"


class VoiceAssistantUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Voice Assistant")
        self.root.configure(bg=BG)
        self.root.attributes("-fullscreen", True)
        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False))

        self.canvas = tk.Canvas(root, bg=BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.cx, self.cy = 700, 400
        self.base_radius = 110
        self.glow_rings = []
        self.core = None
        self.status_text = None
        self.agent_text = None

        self._pulse = 0
        self._pulse_dir = 1
        self.state = "idle"

        self.manager = ManagerAgent()

        self.root.after(100, self.setup_visuals)
        threading.Thread(target=self.voice_loop, daemon=True).start()

    def setup_visuals(self):
        self.canvas.update()
        self.cx = self.canvas.winfo_width() // 2
        self.cy = self.canvas.winfo_height() // 2 - 40

        self.glow_rings = []
        for i, size in enumerate([200, 160, 130]):
            ring = self.canvas.create_oval(
                self.cx - size, self.cy - size, self.cx + size, self.cy + size,
                outline=self._shade(COLORS["idle"], 0.3 + i * 0.15), width=2
            )
            self.glow_rings.append(ring)

        self.core = self.canvas.create_oval(
            self.cx - self.base_radius, self.cy - self.base_radius,
            self.cx + self.base_radius, self.cy + self.base_radius,
            fill=COLORS["idle"], outline=""
        )

        self.status_text = self.canvas.create_text(
            self.cx, self.cy + 220, text="Idle", fill="#e6edf3",
            font=("Segoe UI", 20, "bold")
        )
        self.agent_text = self.canvas.create_text(
            self.cx, self.cy + 255, text="Say something to begin", fill="#7d8590",
            font=("Segoe UI", 13)
        )

        self.animate()

    def _shade(self, hex_color, factor):
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    def set_state(self, state: str, agent_name: str = ""):
        self.state = state
        color = COLORS.get(state, COLORS["idle"])
        self.canvas.itemconfig(self.core, fill=color)
        for i, ring in enumerate(self.glow_rings):
            self.canvas.itemconfig(ring, outline=self._shade(color, 0.3 + i * 0.15))
        self.canvas.itemconfig(self.status_text, text=state.capitalize())
        self.canvas.itemconfig(self.agent_text, text=agent_name)

    def animate(self):
        self._pulse += 0.6 * self._pulse_dir
        if self._pulse >= 12:
            self._pulse_dir = -1
        elif self._pulse <= 0:
            self._pulse_dir = 1

        r = self.base_radius + self._pulse
        self.canvas.coords(self.core, self.cx - r, self.cy - r, self.cx + r, self.cy + r)

        for i, ring in enumerate(self.glow_rings):
            size = [200, 160, 130][i] + self._pulse * (0.6 - i * 0.15)
            self.canvas.coords(ring, self.cx - size, self.cy - size, self.cx + size, self.cy + size)

        self.root.after(30, self.animate)

    def voice_loop(self):
        while True:
            self.set_state("listening", "Listening...")
            user_input = listen()

            if not user_input:
                continue
            if user_input.lower() in ["exit", "stop", "quit"]:
                self.set_state("idle", "Goodbye!")
                speak("Goodbye!")
                break

            self.set_state("thinking", "Manager is planning...")
            steps = self.manager.plan(user_input)
            agent_name = steps[0].capitalize() if steps else "Assistant"
            self.set_state("thinking", f"{agent_name} is working...")

            result, image = self.manager.execute(user_input, steps=steps)

            self.set_state("speaking", agent_name)
            speak(result)
            self.set_state("idle", "Say something to continue")

        self.set_state("idle")


if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceAssistantUI(root)
    root.mainloop()