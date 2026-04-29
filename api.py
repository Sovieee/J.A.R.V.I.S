import re
import sys
import threading
import time
import requests

from flask import Flask, jsonify, redirect, request
from flask_socketio import SocketIO

from commands.command_handler import handle_command
from commands.spotify_player import (
    complete_spotify_authorization,
    create_spotify_authorize_url,
    get_spotify_status,
    spotify_callback_page,
)
from intelligence.context_state import set_conversation_mode

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")


def safe_console_print(*parts):
    try:
        print(*parts)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        safe_parts = []

        for part in parts:
            text = str(part)
            safe_parts.append(text.encode(encoding, errors="replace").decode(encoding))

        print(*safe_parts)


@app.route("/command", methods=["POST"])
def run_command():
    data = request.json
    safe_console_print("[API DEBUG] Received:", data)

    command = data.get("command")

    if command:
        response = handle_command(command) or "Done"

        # 🔥 If it's an action dict → send directly
        if isinstance(response, dict):
            return jsonify(response)

        return jsonify({
            "status": "success",
            "response": response
        })

    return jsonify({"status": "error"})


@app.route("/spotify/login", methods=["GET"])
def spotify_login():
    try:
        auth_url = create_spotify_authorize_url()
        return redirect(auth_url)
    except Exception as exc:
        return spotify_callback_page(False, str(exc)), 400


@app.route("/spotify/callback", methods=["GET"])
def spotify_callback():
    error = request.args.get("error")
    code = request.args.get("code")
    state = request.args.get("state")

    if error:
        return spotify_callback_page(False, f"Spotify authorization failed: {error}."), 400

    if not code or not state:
        return spotify_callback_page(False, "Spotify did not return a valid authorization code."), 400

    try:
        complete_spotify_authorization(code, state)
        return spotify_callback_page(
            True,
            "Spotify is connected. Go back to JARVIS and ask me to play something.",
        )
    except Exception as exc:
        return spotify_callback_page(False, str(exc)), 400
    
@app.route("/update-context", methods=["POST"])
def update_context():
    data = request.json

    from intelligence.context_state import set_context
    print("🔥 LOCATION RECEIVED:", data)
    if "location" in data:
        set_context("location", data["location"])

    return jsonify({"status": "ok"})


@app.route("/spotify/status", methods=["GET"])
def spotify_status():
    return jsonify(get_spotify_status())


@socketio.on("start_listening")
def handle_listening():
    thread = threading.Thread(target=_listening_loop)
    thread.daemon = True
    thread.start()


def _listening_loop():
    from voice.wake_listener import listen_wake_word

    safe_console_print("Listening started...")

    last_active_time = time.time()
    last_command = None

    while True:
        command = listen_wake_word()

        if not command and (time.time() - last_active_time > 60):
            set_conversation_mode(False)

        if command and command != last_command:
            last_command = command
            last_active_time = time.time()

            safe_console_print("[WAKE] Heard:", command)

            socketio.emit("jarvis_user", {"command": command})

            response = handle_command(command) or "Done"

            safe_console_print("[STREAM] Sending response:", response)

            if response and response.strip():
                chunks = re.findall(r".{1,40}(?:\s|$)", response)
                for chunk in chunks:
                    socketio.emit("jarvis_chunk", {"chunk": chunk})
                    socketio.sleep(0.08)

            if not response:
                socketio.emit("jarvis_chunk", {"chunk": "Sorry, I didn't understand."})

            socketio.emit("jarvis_done")

        socketio.sleep(0.5)

def get_location():
    try:
        res = requests.get("http://ip-api.com/json/")
        data = res.json()

        return {
            "city": data.get("city"),
            "lat": data.get("lat"),
            "lon": data.get("lon"),
            "country": data.get("country")
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    socketio.run(app, debug=True)
