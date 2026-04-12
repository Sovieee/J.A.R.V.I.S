from flask import Flask, request, jsonify
from commands.command_handler import handle_command
from flask_socketio import SocketIO
import time
import random
import threading
import re
from intelligence.context_state import set_conversation_mode
from voice.voice_output import speak

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")


# -------------------------------
# 🔹 NORMAL COMMAND (TEXT API)
# -------------------------------
@app.route("/command", methods=["POST"])
def run_command():
    data = request.json
    print("[API DEBUG] Received:", data)

    command = data.get("command")

    if command:
        response = handle_command(command) or "Done"

        return jsonify({
            "status": "success",
            "response": response if response else "Done"
        })

    return jsonify({"status": "error"})


# -------------------------------
# 🔹 VOICE + STREAMING (REAL-TIME)
# -------------------------------
@socketio.on("start_listening")
def handle_listening():
    thread = threading.Thread(target=_listening_loop)
    thread.daemon = True
    thread.start()

def _listening_loop():
    from voice.wake_listener import listen_wake_word

    print("🎤 Listening started...")

    last_active_time = time.time()
    last_command = None

    while True:
        command = listen_wake_word()

        if not command and (time.time() - last_active_time > 60):
            set_conversation_mode(False)

        if command and command != last_command:
            last_command = command
            last_active_time = time.time()

            print("[WAKE] Heard:", command)

            socketio.emit("jarvis_user", {"command": command})

            response = handle_command(command) or "Done"

            print("[STREAM] Sending response:", response)

            if response and response.strip():
                chunks = re.findall(r'.{1,40}(?:\s|$)', response)
                for chunk in chunks:
                    socketio.emit("jarvis_chunk", {"chunk": chunk})
                    socketio.sleep(0.08)

            if not response:
                socketio.emit("jarvis_chunk", {"chunk": "Sorry, I didn't understand."})

            socketio.emit("jarvis_done")

        socketio.sleep(0.5)

# -------------------------------
# 🔹 RUN SERVER
# -------------------------------
if __name__ == "__main__":
    socketio.run(app, debug=True)