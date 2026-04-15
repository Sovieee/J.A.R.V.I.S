from intelligence.nlp import clean_command, detect_intent
from commands.open_apps import (
    open_chrome, open_notepad, open_spotify,
    open_calculator, open_vscode, open_whatsapp,
    open_file_explorer, open_netflix, open_prime_video,
    open_word, open_excel, open_powerpoint, open_settings
)
from commands.web_search import search_google
from intelligence.memory import set_preference, get_preference, save_fact, get_fact
from intelligence.learning import log_activity, get_time_based_suggestion
from voice.voice_output import speak
from intelligence.ai_brain import ask_ai
from intelligence.context_memory import add_to_history
from intelligence.context_state import (
    set_pending_intent,
    get_pending_intent,
    clear_pending_intent,
    set_conversation_mode
)
import time

# 🔹 Store last suggestion
last_suggestion = None
suggestion_rejected = False


def handle_command(command):
    global last_suggestion, suggestion_rejected

    # 🔹 Clean command
    command = clean_command(command)

    # =========================
    # 🧠 MEMORY LEARNING
    # =========================

    if "my name is" in command:
        name = command.split("my name is")[-1].strip()
        save_fact("name", name)
        msg = f"Nice to meet you, {name}"
        speak(msg)
        return msg

    if "call me" in command and not command.startswith("what"):
        nickname = command.split("call me")[-1].strip()
        save_fact("nickname", nickname)
        msg = f"Got it. I will call you {nickname}"
        speak(msg)
        return msg

    if "i like" in command:
        thing = command.split("i like")[-1].strip()
        save_fact("likes", thing)
        msg = f"Got it, you like {thing}"
        speak(msg)
        return msg

    if "i prefer" in command:
        pref = command.split("i prefer")[-1].strip()
        save_fact("preference", pref)
        msg = f"Got it, you prefer {pref}"
        speak(msg)
        return msg

    # =========================
    # 🧠 MEMORY RECALL
    # =========================

    if "what do you call me" in command or "what is my name" in command:
        nickname = get_fact("nickname")
        name = get_fact("name")

        if nickname:
            msg = f"I call you {nickname}"
        elif name:
            msg = f"Your name is {name}"
        else:
            msg = "I don't know yet. What should I call you?"

        speak(msg)
        return msg

    if "what do i like" in command:
        like = get_fact("likes")
        msg = f"You like {like}" if like else "I don't know your preferences yet"
        speak(msg)
        return msg

    # =========================
    # 🔄 PENDING INTENT
    # =========================

    pending = get_pending_intent()
    if pending == "search":
        clear_pending_intent()
        return search_google(command)

    # =========================
    # 🎯 INTENT DETECTION
    # =========================

    intent = detect_intent(command)

    log_activity({
        "intent": intent,
        "command": command
    })

    print(f"[DEBUG] Command: {command}")
    print(f"[DEBUG] Intent: {intent}")

    # =========================
    # 👍 YES / NO HANDLING
    # =========================

    words = command.lower().split()

    if any(w in words for w in ["yes", "yeah", "yep", "sure", "ok"]):
        if last_suggestion:
            cmd = last_suggestion
            last_suggestion = None
            return handle_command(cmd)

    if any(w in words for w in ["no", "nope", "nah", "dont", "don't"]):
        suggestion_rejected = True
        last_suggestion = None
        msg = "Okay, ignoring suggestion."
        speak(msg)
        return msg

    # =========================
    # ⚙️ PREFERENCES
    # =========================

    if "set browser to" in command:
        browser = command.split("set browser to")[-1].strip()
        set_preference("browser", browser)
        msg = f"Got it. I will use {browser}"
        speak(msg)
        return msg

    # =========================
    # 🖥️ OPEN APPS
    # =========================

    if intent == "open_app":

        if "browser" in command:
            browser = get_preference("browser")

            if browser == "chrome":
                return open_chrome()
            elif browser == "notepad":
                return open_notepad()

            msg = "No browser preference set"
            speak(msg)
            return msg

        if "chrome" in command:
            return open_chrome()
        if "notepad" in command:
            return open_notepad()
        if "spotify" in command:
            return open_spotify()
        if "calculator" in command or "calc" in command:
            return open_calculator()
        if "vscode" in command or "code" in command:
            return open_vscode()
        if "whatsapp" in command:
            return open_whatsapp()
        if "netflix" in command:
            return open_netflix()
        if "prime" in command:
            return open_prime_video()
        if "word" in command:
            return open_word()
        if "excel" in command:
            return open_excel()
        if "powerpoint" in command or "ppt" in command:
            return open_powerpoint()
        if "settings" in command:
            return open_settings()

        return open_file_explorer()

    # =========================
    # 🔍 SEARCH
    # =========================

    if intent == "search":
        words = command.split()

        if len(words) > 1:
            query = " ".join(words[1:])
            search_google(query)
            return f"Searching for {query}"

        set_pending_intent("search")
        msg = "What do you want me to search?"
        speak(msg)
        return msg

    # =========================
    # ❌ EXIT
    # =========================

    if intent == "exit":
        set_conversation_mode(False)
        speak("Goodbye!")
        return "Goodbye!"

    # =========================
    # 🤖 AI FALLBACK
    # =========================

    add_to_history("user", command)

    ai_response = ask_ai(command)

    if ai_response:
        add_to_history("assistant", ai_response)

    if ai_response and "offline" not in ai_response.lower():
        set_conversation_mode(True)
        time.sleep(0.1)
        speak(ai_response)
        return ai_response

    # =========================
    # ⏰ SUGGESTIONS
    # =========================

    suggestion = get_time_based_suggestion()

    if suggestion and suggestion != command:
        if suggestion == last_suggestion and suggestion_rejected:
            return "Sorry, I don't understand that command."

        last_suggestion = suggestion
        suggestion_rejected = False

        msg = f"You usually do '{suggestion}'. Want me to do it?"
        speak(msg)
        return msg

    # =========================
    # ❓ FINAL FALLBACK
    # =========================

    msg = "Sorry, I don't understand that command."
    speak(msg)
    return msg