import re


APP_KEYWORDS = (
    "chrome",
    "browser",
    "notepad",
    "spotify",
    "calculator",
    "calc",
    "vscode",
    "code",
    "whatsapp",
    "netflix",
    "prime",
    "word",
    "excel",
    "powerpoint",
    "ppt",
    "settings",
    "explorer",
    "downloads",
    "file explorer",
)

OPEN_APP_VERBS = ("open", "launch", "start", "run")
SEARCH_KEYWORDS = ("search", "google", "look up", "find")
WEATHER_KEYWORDS = ("weather", "forecast", "temperature", "rain", "humid")
TIME_KEYWORDS = ("time", "date", "day", "clock")
REMINDER_KEYWORDS = ("remind", "reminder", "timer", "alarm", "countdown")
MEDIA_KEYWORDS = (
    "pause",
    "resume",
    "stop music",
    "stop playback",
    "next song",
    "next track",
    "previous song",
    "previous track",
    "skip",
    "mute",
    "unmute",
    "volume up",
    "volume down",
    "increase volume",
    "decrease volume",
    "louder",
    "softer",
)
PLAY_MUSIC_KEYWORDS = (
    "play",
    "put on",
)
MATH_KEYWORDS = (
    "calculate",
    "compute",
    "solve",
    "plus",
    "minus",
    "times",
    "multiplied",
    "divide",
    "divided",
    "mod",
    "percent",
    "square root",
)
FOLLOW_UP_PREFIXES = ("in ", "for ", "at ", "about ", "after ", "tomorrow ", "today ")


def clean_command(command):
    command = command.lower()

    fillers = [
        "please",
        "can you",
        "could you",
        "hey",
        "jarvis",
        "tell me",
        "give me",
    ]

    for word in fillers:
        command = command.replace(word, " ")

    command = re.sub(r"\s+", " ", command)
    return command.strip()


def _contains_phrase(command, phrases):
    return any(phrase in command for phrase in phrases)


def _looks_like_math(command):
    if _contains_phrase(command, MATH_KEYWORDS):
        return True

    if re.search(r"\d", command) and re.search(r"[\+\-\*/%]", command):
        return True

    return bool(re.search(r"what is\s+\d", command))


def _is_play_music_request(command):
    if _contains_phrase(command, MEDIA_KEYWORDS):
        return False

    if command.startswith("play "):
        return True

    if command.startswith("put on "):
        return True

    if " play " in command and any(
        hint in command
        for hint in (
            "song",
            "music",
            "track",
            "album",
            "artist",
            "playlist",
            "spotify",
        )
    ):
        return True

    return _contains_phrase(command, PLAY_MUSIC_KEYWORDS) and "spotify" in command


def detect_intent(command):
    if _contains_phrase(command, SEARCH_KEYWORDS):
        return "search"

    if _contains_phrase(command, WEATHER_KEYWORDS):
        return "weather"

    if _contains_phrase(command, REMINDER_KEYWORDS):
        return "reminder"

    if _contains_phrase(command, MEDIA_KEYWORDS):
        return "media_control"

    if _is_play_music_request(command):
        return "play_music"

    if _contains_phrase(command, TIME_KEYWORDS):
        return "time"

    if _looks_like_math(command):
        return "arithmetic"

    if _contains_phrase(command, OPEN_APP_VERBS) and _contains_phrase(command, APP_KEYWORDS):
        return "open_app"

    if command in {"yes", "yeah", "yep", "sure", "ok", "okay", "do it"}:
        return "affirm"

    if command in {"no", "nope", "nah", "don't", "dont", "cancel"}:
        return "decline"

    if "exit" in command or "quit" in command or "goodbye" in command:
        return "exit"

    if command.startswith(FOLLOW_UP_PREFIXES) or len(command.split()) <= 4:
        return "follow_up"

    return "unknown"
