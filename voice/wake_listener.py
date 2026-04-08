from voice.voice_input import listen_command
from intelligence.context_state import get_conversation_mode, set_conversation_mode

def listen_wake_word():
    command = listen_command()

    if not command:
        return None

    command = command.lower()

    # 🔹 If already in conversation mode → skip wake word
    if get_conversation_mode():
        return command

    # 🔹 Activate on wake word
    if "hey jarvis" in command:
        set_conversation_mode(True)
        return command.replace("hey jarvis", "").strip()

    return None