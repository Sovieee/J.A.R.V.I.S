from intelligence.nlp import clean_command, detect_intent
from commands.open_apps import open_chrome, open_notepad
from commands.web_search import search_google
from intelligence.memory import set_preference, get_preference
from intelligence.learning import log_activity, get_frequent_actions
from voice.voice_output import speak
from intelligence.learning import get_time_based_suggestion
from intelligence.memory import save_fact, get_fact
from intelligence.ai_brain import ask_ai
from intelligence.context_memory import add_to_history

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

            # 🔹 MEMORY LEARNING (store facts)

    if "my name is" in command:
        name = command.split("my name is")[-1].strip()
        save_fact("name", name)
        message = f"Nice to meet you, {name}"
        speak(message)
        return message

    if "i like" in command:
        thing = command.split("i like")[-1].strip()
        save_fact("likes", thing)
        message = f"Got it, you like {thing}"
        speak(message)
        return message


    # 🔹 MEMORY RECALL

    if "what is my name" in command:
        name = get_fact("name")
        if name:
            message = f"Your name is {name}"
        else:
            message = "I don't know your name yet"

        speak(message)
        return message

    if "what do i like" in command:
        like = get_fact("likes")
        if like:
            message = f"You like {like}"
        else:
            message = "I don't know your preferences yet"

        speak(message)
        return message

    add_to_history("User", command)

        # 🔹 FALLBACK → AI FIRST
    ai_response = ask_ai(command)
    
    if ai_response and "AI brain is not connected" not in ai_response:
        add_to_history("Jarvis", ai_response)
        speak(ai_response)
        return ai_response


    # 🔹 THEN TIME-AWARE SUGGESTION (only if AI fails)
    suggestion = get_time_based_suggestion()

    if suggestion and suggestion != command:
        if suggestion == last_suggestion and suggestion_rejected:
            return "Sorry, I don't understand that command."

        last_suggestion = suggestion
        suggestion_rejected = False

        message = f"You usually do '{suggestion}' around this time. Want me to do it?"
        speak(message)
        return message


    # 🔹 FINAL FALLBACK
    return "Sorry, I don't understand that command."