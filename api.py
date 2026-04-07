from flask import Flask, request, jsonify
from commands.command_handler import handle_command

app = Flask(__name__)

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

@app.route("/voice", methods=["GET"])
def voice_command():
    from voice.voice_input import listen_command

    command = listen_command()
    print("[VOICE] Heard:", command)

    if command:
        response = handle_command(command)
        return jsonify({
            "command": command,
            "response": response
        })

    return jsonify({
        "command": "",
        "response": "Could not understand"
    })


if __name__ == "__main__":
    app.run(port=5000)