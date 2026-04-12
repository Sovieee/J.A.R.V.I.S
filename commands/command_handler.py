from intelligence.nlp import clean_command, detect_intent
from commands.open_apps import (
    open_chrome, open_notepad, open_spotify,
    open_calculator, open_vscode, open_whatsapp,
    open_file_explorer, open_netflix, open_prime_video,
    open_word, open_excel, open_powerpoint, open_settings
)
from commands.web_search import search_google
from intelligence.memory import set_preference, get_preference
from intelligence.learning import log_activity, get_frequent_actions
from voice.voice_output import speak
from intelligence.learning import get_time_based_suggestion
from intelligence.memory import save_fact, get_fact
from intelligence.ai_brain import ask_ai
from intelligence.context_memory import add_to_history
import time
from intelligence.context_state import (
    set_pending_intent,
    get_pending_intent,
    clear_pending_intent,
    set_conversation_mode
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
    words = command.lower().split()
    if any(word in words for word in ["yes", "yeah", "yep", "sure", "ok", "okay"]):
        if last_suggestion:
            print(f"[DEBUG] Executing suggested command: {last_suggestion}")
            cmd = last_suggestion
            last_suggestion = None
            return handle_command(cmd)

    words = command.lower().split()
    if any(word in words for word in ["no", "nope", "nah", "don't", "dont"]):
        suggestion_rejected = True
        last_suggestion = None
        message = "Okay, ignoring suggestion."
        speak(message)
        return message

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
                message = "No browser preference set"
                speak(message)
                return message

       # Direct commands
        if "chrome" in command:
            return open_chrome()

        if "notepad" in command:
            return open_notepad()

        if "spotify" in command:
            return open_spotify()

        if "calculator" in command or "calc" in command:
            return open_calculator()

        if "vs code" in command or "vscode" in command or "code" in command:
            return open_vscode()

        if "whatsapp" in command:
            return open_whatsapp()

        if "netflix" in command:
            return open_netflix()

        if "prime" in command or "amazon" in command:
            return open_prime_video()

        if "word" in command:
            return open_word()

        if "excel" in command:
            return open_excel()

        if "powerpoint" in command or "ppt" in command:
            return open_powerpoint()

        if "settings" in command:
            return open_settings()

        if "file explorer" in command or "explorer" in command or "files" in command:
            # Check if user named a specific folder
            if "downloads" in command:
                return open_file_explorer(r"C:\Users\%USERNAME%\Downloads")
            elif "documents" in command:
                return open_file_explorer(r"C:\Users\%USERNAME%\Documents")
            elif "desktop" in command:
                return open_file_explorer(r"C:\Users\%USERNAME%\Desktop")
            elif "pictures" in command:
                return open_file_explorer(r"C:\Users\%USERNAME%\Pictures")
            elif "music" in command:
                return open_file_explorer(r"C:\Users\%USERNAME%\Music")
            elif "videos" in command:
                return open_file_explorer(r"C:\Users\%USERNAME%\Videos")
            else:
                return open_file_explorer()

    # 🔹 SEARCH
    elif intent == "search":
        words = command.split()

        if len(words) > 1:
            query = " ".join(words[1:])
            search_google(query)
            return f"Searching for {query}"

        else:
            set_pending_intent("search")
            message = "What do you want me to search?"
            speak(message)
            return message

    # 🔹 EXIT
    elif intent == "exit":
        set_conversation_mode(False)  # 🔥 turn off conversation mode
        speak("Goodbye!")
        return "Goodbye!"

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

    # 🔹 ADD USER TO MEMORY (IMPORTANT: lowercase roles)
    add_to_history("user", command)

    # 🔹 AI RESPONSE
    ai_response = ask_ai(command)

    # 🔹 ADD AI RESPONSE TO MEMORY
    if ai_response:
        add_to_history("assistant", ai_response)

    # 🔹 SPEAK + RETURN (Fallback)
    if ai_response and "AI brain is not connected" not in ai_response:
        set_conversation_mode(True)  # 🔥 KEEP LISTENING
        time.sleep(0.1)
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
    final_msg = "Sorry, I don't understand that command."
    speak(final_msg)
    return final_msg