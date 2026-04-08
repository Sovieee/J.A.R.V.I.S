from flask import Flask, request, jsonify
from commands.command_handler import handle_command
from flask_socketio import SocketIO
import time
from intelligence.context_state import set_conversation_mode


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

@app.route("/command", methods=["POST"])
def run_command():
    data = request.json
    print("[API DEBUG] Received:", data)   # 🔥 IMPORTANT

    command = data.get("command")

    if command:
        response = handle_command(command)

        return jsonify({
        "status": "success",
        "response": response if response else "Done"})
    
    return jsonify({"status": "error"})

@socketio.on("start_listening")
def handle_listening():
    from voice.wake_listener import listen_wake_word

    print("🎤 Listening started...")

    last_active_time = time.time()

    while True:
        command = listen_wake_word()

# Only reset if NO command AND timeout reached
        if not command and (time.time() - last_active_time > 60):
            set_conversation_mode(False)

        if command:
            last_active_time = time.time()

            print("[WAKE] Heard:", command)

            response = handle_command(command)

            socketio.emit("jarvis_response", {
                "command": command,
                "response": response
        })


if __name__ == "__main__":
    socketio.run(app, debug=True)