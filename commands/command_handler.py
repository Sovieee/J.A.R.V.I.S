from intelligence.nlp import clean_command, detect_intent
from commands.open_apps import open_chrome, open_notepad
from commands.web_search import search_google
from intelligence.memory import set_preference, get_preference
from intelligence.learning import log_activity, get_frequent_actions
from voice.voice_output import speak
from intelligence.learning import get_time_based_suggestion
from intelligence.context_state import (
    set_pending_intent,
    get_pending_intent,
    clear_pending_intent
)

# 🔹 Store last suggestion
last_suggestion = None
suggestion_rejected = False

def handle_command(command):
    
    global last_suggestion, suggestion_rejected

     #  Clean first
    command = clean_command(command)

    #  Then check pending intent
    pending = get_pending_intent()

    if pending == "search":
        clear_pending_intent()
        return search_google(command)
    
    intent = detect_intent(command)

    # 🔹 Log activity
    log_activity({
    "intent": intent,
    "command": command
})

    # 🔍 Debug logs
    print(f"[DEBUG] Cleaned Command: {command}")
    print(f"[DEBUG] Detected Intent: {intent}")

    # 🔹 Handle YES / NO for suggestions
    if any(word in command for word in ["yes", "yeah", "yep", "sure", "ok", "okay", "do it"]):
        if last_suggestion:
            print(f"[DEBUG] Executing suggested command: {last_suggestion}")
            cmd = last_suggestion
            last_suggestion = None
            return handle_command(cmd)

    if any(word in command for word in ["no", "nope", "nah", "don't", "dont"]):
        suggestion_rejected = True
        last_suggestion = None
        return speak("Okay, ignoring suggestion.")

    # 🔹 SET PREFERENCE
    if "set browser to" in command:
        browser = command.split("set browser to")[-1].strip()
        set_preference("browser", browser)
        message = f"Got it. I will use {browser} as your browser"
        speak(message)
        return message

    # 🔹 OPEN APP
    if intent == "open_app":

        # Use memory
        if "browser" in command:
            browser = get_preference("browser")
            print(f"[DEBUG] Preferred Browser: {browser}")

            if browser == "chrome":
                return open_chrome()
            elif browser == "notepad":
                return open_notepad()
            else:
                return speak("No browser preference set")

        # Direct commands
        if "chrome" in command:
            return open_chrome()

        if "notepad" in command:
            return open_notepad()

    # 🔹 SEARCH
    elif intent == "search":
        words = command.split()

        if len(words) > 1:
            query = " ".join(words[1:])
            return search_google(query)

        else:
            set_pending_intent("search")
            message = "What do you want me to search?"
            speak(message)
            return message

    # 🔹 EXIT
    elif intent == "exit":
        speak("Goodbye!")
        exit()

    # 🔹 TIME-AWARE SUGGESTION

    suggestion = get_time_based_suggestion()

    if suggestion and suggestion != command:
    
    #  Don't repeat rejected suggestion
        if suggestion == last_suggestion and suggestion_rejected:
            return "Sorry, I don't understand that command."

        last_suggestion = suggestion
        suggestion_rejected = False

        message = f"You usually do '{suggestion}' around this time. Want me to do it?"
        speak(message)
        return message

    # 🔹 FALLBACK
    return "Sorry, I don't understand that command."