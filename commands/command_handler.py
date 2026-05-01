import re
import time

from commands.open_apps import (
    open_calculator,
    open_chrome,
    open_excel,
    open_file_explorer,
    open_netflix,
    open_notepad,
    open_powerpoint,
    open_prime_video,
    open_settings,
    open_spotify,
    open_vscode,
    open_whatsapp,
    open_word,
)
from commands.smart_actions import (
    calculate_expression,
    extract_location,
    extract_reminder_details,
    get_time_response,
    get_weather_response,
    handle_media_command,
    normalize_follow_up_text,
    schedule_reminder,
    get_current_location,
)
from commands.spotify_player import handle_spotify_playback_command, play_spotify_request
from commands.web_search import search_google
from intelligence.ai_brain import ask_ai
from intelligence.context_memory import add_to_history
from intelligence.context_state import (
    clear_pending_intent,
    get_pending_intent,
    set_conversation_mode,
    set_pending_intent,
)
from intelligence.learning import get_time_based_suggestion, log_activity
from intelligence.memory import get_fact, get_preference, save_fact, set_preference
from intelligence.nlp import clean_command, detect_intent
from voice.voice_output import speak


last_suggestion = None
suggestion_rejected = False

LOCATION_REQUEST_PATTERN = re.compile(
    r"^(?:where am i(?: right now)?|my location|current location|what(?: is|'s) my location)$"
)


def respond(message):
    speak(message)
    return message


def get_pending_name(pending_intent):
    if isinstance(pending_intent, dict):
        return pending_intent.get("intent")

    return pending_intent


def complete_reminder(details):
    message = details.get("message")
    delay_seconds = details.get("delay_seconds")
    due_text = details.get("due_text")

    if message and delay_seconds is not None:
        schedule_reminder(message, delay_seconds)
        clear_pending_intent()

        if due_text:
            return respond(f"Okay. I will remind you to {message} {due_text}.")

        return respond(f"Okay. I will remind you to {message}.")

    if message and delay_seconds is None:
        set_pending_intent({
            "intent": "reminder",
            "message": message,
        })
        return respond(f"Sure. When should I remind you to {message}?")

    if delay_seconds is not None and not message:
        set_pending_intent({
            "intent": "reminder",
            "delay_seconds": delay_seconds,
            "due_text": due_text,
        })
        return respond("Sure. What should I remind you about?")

    set_pending_intent({"intent": "reminder"})
    return respond("What should I remind you about, and when?")


def handle_pending_intent(command):
    pending_intent = get_pending_intent()
    pending_name = get_pending_name(pending_intent)

    if not pending_name:
        return None

    if pending_name == "search":
        clear_pending_intent()
        return search_google(command)

    if pending_name == "weather":
        location = extract_location(command) or normalize_follow_up_text(command)
        if not location:
            return respond("Which city should I check the weather for?")

        clear_pending_intent()
        weather_response = get_weather_response(location)

        if weather_response:
            return respond(weather_response)

        search_google(f"weather in {location}")
        return f"Searching weather for {location}"

    if pending_name == "time":
        location = extract_location(command) or normalize_follow_up_text(command)
        if not location:
            return respond("Which city or timezone should I use?")

        clear_pending_intent()
        time_response = get_time_response(command, location=location)

        if time_response:
            return respond(time_response)

        search_google(f"current time in {location}")
        return f"Searching current time in {location}"

    if pending_name == "reminder":
        details = extract_reminder_details(
            command,
            pending_intent if isinstance(pending_intent, dict) else None,
        )
        return complete_reminder(details)

    return None


def handle_command(command):
    global last_suggestion, suggestion_rejected

    command = clean_command(command)

    if not command:
        return respond("I did not catch that. Try saying it once more.")

    if "my name is" in command:
        name = command.split("my name is")[-1].strip()
        save_fact("name", name)
        return respond(f"Nice to meet you, {name}")

    if "call me" in command and not command.startswith("what"):
        nickname = command.split("call me")[-1].strip()
        save_fact("nickname", nickname)
        return respond(f"Got it. I will call you {nickname}")

    if "i like" in command:
        thing = command.split("i like")[-1].strip()
        save_fact("likes", thing)
        return respond(f"Got it, you like {thing}")

    if "i prefer" in command:
        pref = command.split("i prefer")[-1].strip()
        save_fact("preference", pref)
        return respond(f"Got it, you prefer {pref}")

    if "what do you call me" in command or "what is my name" in command:
        nickname = get_fact("nickname")
        name = get_fact("name")

        if nickname:
            return respond(f"I call you {nickname}")

        if name:
            return respond(f"Your name is {name}")

        return respond("I do not know yet. What should I call you?")

    if "what do i like" in command:
        like = get_fact("likes")
        if like:
            return respond(f"You like {like}")

        return respond("I do not know your preferences yet.")
    
    if LOCATION_REQUEST_PATTERN.fullmatch(command):
        location = get_current_location()

        if location:
            speak(f"You are in {location['city']}, {location['country']}")
            return location  # IMPORTANT: returning JSON for frontend

        return "I couldn't determine your location."

    pending_response = handle_pending_intent(command)
    if pending_response is not None:
        return pending_response

    intent = detect_intent(command)

    log_activity({
        "intent": intent,
        "command": command,
    })

    print(f"[DEBUG] Command: {command}")
    print(f"[DEBUG] Intent: {intent}")

    words = command.split()

    if intent == "affirm" or any(word in words for word in ["yes", "yeah", "yep", "sure", "ok", "okay"]):
        if last_suggestion:
            suggestion = last_suggestion
            last_suggestion = None
            return handle_command(suggestion)

    if intent == "decline" or any(word in words for word in ["no", "nope", "nah", "dont", "don't", "cancel"]):
        suggestion_rejected = True
        last_suggestion = None
        return respond("Okay, ignoring suggestion.")

    if "set browser to" in command:
        browser = command.split("set browser to")[-1].strip()
        set_preference("browser", browser)
        return respond(f"Got it. I will use {browser}")

    # =======================
    # CAMERA CONTROLS (FIXED ORDER)
    # =======================

    cmd = command.lower()

    # CLOSE CAMERA
    if ("close" in cmd or "stop" in cmd) and "camera" in cmd:
        return {"action": "close_camera"}

    # STOP RECORDING
    if "stop recording" in cmd:
        return {"action": "stop_recording"}

    # RECORD VIDEO
    if "record" in cmd:
        return {"action": "record_video"}

    # TAKE PHOTO
    if ("take" in cmd or "click" in cmd) and ("photo" in cmd or "picture" in cmd):
        return {"action": "capture_photo"}

    # OPEN CAMERA
    if "camera" in cmd:
        return {"action": "open_camera"}

    if intent == "open_app":
        if "browser" in command:
            browser = get_preference("browser")

            if browser == "chrome":
                return open_chrome()
            if browser == "notepad":
                return open_notepad()

            return respond("No browser preference is set.")

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

    if intent == "search":
        query = re.sub(r"^(search|google|look up|find)\s+", "", command).strip()

        if query:
            search_google(query)
            return f"Searching for {query}"

        set_pending_intent("search")
        return respond("What do you want me to search?")

    if intent == "weather":
        location = extract_location(command)

        if location:
            weather_response = get_weather_response(location)
            if weather_response:
                return respond(weather_response)

            search_google(f"weather in {location}")
            return f"Searching weather for {location}"

        set_pending_intent({"intent": "weather"})
        return respond("Which city should I check the weather for?")

    if intent == "time":
        needs_location = bool(re.search(r"\b(?:time|date|day)\s+in\s*$", command))
        if needs_location:
            set_pending_intent({"intent": "time"})
            return respond("Which city or timezone should I use?")

        location = extract_location(command)
        time_response = get_time_response(command, location=location)

        if time_response:
            return respond(time_response)

        if location:
            search_google(f"current time in {location}")
            return f"Searching current time in {location}"

        return respond("I could not work out the time request.")

    if intent == "arithmetic":
        try:
            result = calculate_expression(command)
            return respond(f"The answer is {result}.")
        except Exception:
            return respond("I could not solve that calculation yet.")

    if intent == "reminder":
        reminder_details = extract_reminder_details(command)
        return complete_reminder(reminder_details)

    if intent == "play_music":
        return respond(play_spotify_request(command))

    if intent == "media_control":
        if "spotify" in command:
            spotify_response = handle_spotify_playback_command(command)
            if spotify_response:
                return respond(spotify_response)

        media_response = handle_media_command(command)
        return respond(media_response)

    if intent == "exit":
        clear_pending_intent()
        set_conversation_mode(False)
        return respond("Goodbye!")
    # =======================
    # FINAL AI FALLBACK (FIX)
    # =======================

    add_to_history("user", command)
    ai_response = ask_ai(command)

    if ai_response:
        add_to_history("assistant", ai_response)
        set_conversation_mode(True)
        time.sleep(0.1)
        speak(ai_response)
        return ai_response
    
    # =======================
    # SUGGESTION (OPTIONAL)
    # =======================

    suggestion = get_time_based_suggestion()

    if suggestion and suggestion != command:
        if suggestion == last_suggestion and suggestion_rejected:
            return respond("Sorry, I do not understand that command.")

        last_suggestion = suggestion
        suggestion_rejected = False

        return respond(f"You usually do '{suggestion}'. Want me to do it?")

    return respond("Sorry, I do not understand that command.")
