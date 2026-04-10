from voice.voice_input import listen_command
from intelligence.context_state import get_conversation_mode, set_conversation_mode

WAKE_WORD = "jarvis"

def listen_wake_word():
    command = listen_command()

    if not command:
        return None

    command = command.lower()

    # ✅ If already in conversation → skip wake word
    if get_conversation_mode():
        return command

    # ✅ Detect wake word
    if WAKE_WORD in command:
        set_conversation_mode(True)

        # remove wake word from command
        command = command.replace(WAKE_WORD, "").strip()

        return command

    return None