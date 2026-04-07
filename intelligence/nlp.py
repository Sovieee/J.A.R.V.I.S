def clean_command(command):
    command = command.lower()

    # words to ignore
    fillers = [
        "please", "can you", "could you",
        "hey", "jarvis", "tell me", "give me"
    ]

    for word in fillers:
        command = command.replace(word, "")

    return command.strip()

def detect_intent(command):
    if "open" in command:
        return "open_app"
    elif "search" in command or "google" in command:
        return "search"
    elif "exit" in command:
        return "exit"
    else:
        return "unknown"