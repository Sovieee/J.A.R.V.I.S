import ast
import json
import operator
import os
import re
import threading
from datetime import datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from voice.voice_output import speak


TIMEZONE_ALIASES = {
    "india": "Asia/Kolkata",
    "kolkata": "Asia/Kolkata",
    "calcutta": "Asia/Kolkata",
    "delhi": "Asia/Kolkata",
    "new delhi": "Asia/Kolkata",
    "mumbai": "Asia/Kolkata",
    "bombay": "Asia/Kolkata",
    "pune": "Asia/Kolkata",
    "bangalore": "Asia/Kolkata",
    "bengaluru": "Asia/Kolkata",
    "hyderabad": "Asia/Kolkata",
    "chennai": "Asia/Kolkata",
    "new york": "America/New_York",
    "los angeles": "America/Los_Angeles",
    "san francisco": "America/Los_Angeles",
    "chicago": "America/Chicago",
    "london": "Europe/London",
    "paris": "Europe/Paris",
    "berlin": "Europe/Berlin",
    "dubai": "Asia/Dubai",
    "singapore": "Asia/Singapore",
    "tokyo": "Asia/Tokyo",
    "sydney": "Australia/Sydney",
}

LOCATION_NOISE = (
    "right now",
    "currently",
    "today",
    "now",
    "outside",
)

MATH_REPLACEMENTS = (
    ("to the power of", "**"),
    ("power of", "**"),
    ("multiplied by", "*"),
    ("divide by", "/"),
    ("divided by", "/"),
    ("added to", "+"),
    ("subtracted by", "-"),
    ("minus", "-"),
    ("plus", "+"),
    ("times", "*"),
    ("into", "*"),
    ("over", "/"),
    ("modulo", "%"),
    ("mod", "%"),
)

ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

ACTIVE_REMINDERS = []


def normalize_follow_up_text(text):
    cleaned = text.strip().strip(" .?!,")
    cleaned = re.sub(r"^(in|for|at|about)\s+", "", cleaned)

    for phrase in LOCATION_NOISE:
        cleaned = re.sub(rf"\b{re.escape(phrase)}\b", "", cleaned)

    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip(" .?!,")


def extract_location(command):
    patterns = [
        r"(?:what\s+is\s+the\s+)?(?:weather|forecast|temperature|rain|humidity)\s+(?:in|for|at)\s+(.+)$",
        r"(?:what\s+)?(?:time|date|day)\s+is(?:\s+it)?\s+(?:in|for|at)\s+(.+)$",
        r"(?:weather|forecast|temperature|rain|humidity)\s+(?:in|for|at)\s+(.+)$",
        r"(?:time|date|day)\s+(?:in|for|at)\s+(.+)$",
        r"^(?:in|for|at)\s+(.+)$",
    ]

    for pattern in patterns:
        match = re.search(pattern, command)
        if match:
            location = normalize_follow_up_text(match.group(1))
            return location or None

    return None


def resolve_timezone(location):
    if not location:
        return None, None

    normalized = location.lower().strip()
    zone_name = TIMEZONE_ALIASES.get(normalized)

    if not zone_name:
        zone_name = location.strip().replace(" ", "_")

    try:
        return ZoneInfo(zone_name), location.title()
    except ZoneInfoNotFoundError:
        return None, None


def get_time_response(command, location=None):
    requested_location = location or extract_location(command)
    wants_date = any(word in command for word in ["date", "day", "today"])
    wants_time = "time" in command or not wants_date

    if requested_location:
        timezone, label = resolve_timezone(requested_location)
        if not timezone:
            return None

        now = datetime.now(timezone)
        formatted_time = now.strftime("%I:%M %p").lstrip("0")
        formatted_date = now.strftime("%A, %d %B %Y")

        if wants_date and not wants_time:
            return f"The date in {label} is {formatted_date}."

        return f"The time in {label} is {formatted_time} on {formatted_date}."

    now = datetime.now().astimezone()
    formatted_time = now.strftime("%I:%M %p").lstrip("0")
    formatted_date = now.strftime("%A, %d %B %Y")

    if wants_date and not wants_time:
        return f"Today is {formatted_date}."

    return f"It is {formatted_time}. Today is {formatted_date}."


def get_weather_response(location):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key or not location:
        return None

    safe_location = quote(location)
    geo_url = (
        "https://api.openweathermap.org/geo/1.0/direct"
        f"?q={safe_location}&limit=1&appid={api_key}"
    )

    try:
        with urlopen(geo_url, timeout=6) as response:
            geo_data = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None

    if not geo_data:
        return None

    match = geo_data[0]
    city_name = match.get("name", location.title())
    country = match.get("country", "")
    lat = match.get("lat")
    lon = match.get("lon")

    if lat is None or lon is None:
        return None

    weather_url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&units=metric&appid={api_key}"
    )

    try:
        with urlopen(weather_url, timeout=6) as response:
            weather_data = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None

    weather_list = weather_data.get("weather") or [{}]
    main_data = weather_data.get("main") or {}

    description = weather_list[0].get("description", "clear")
    temp = round(main_data.get("temp", 0))
    feels_like = round(main_data.get("feels_like", temp))
    humidity = main_data.get("humidity")

    place = f"{city_name}, {country}".strip(", ")
    humidity_text = f" Humidity is {humidity}%." if humidity is not None else ""

    return (
        f"Currently {description} in {place}. "
        f"The temperature is {temp} degrees Celsius and feels like {feels_like}.{humidity_text}"
    )

def get_current_location():
    try:
        with urlopen("http://ip-api.com/json/", timeout=5) as response:
            data = json.load(response)

        return {
            "city": data.get("city"),
            "lat": data.get("lat"),
            "lon": data.get("lon"),
            "country": data.get("country"),
        }

    except Exception:
        return None


def _safe_eval(node):
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)

    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_OPERATORS:
        return ALLOWED_OPERATORS[type(node.op)](_safe_eval(node.operand))

    if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_OPERATORS:
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        return ALLOWED_OPERATORS[type(node.op)](left, right)

    raise ValueError("Unsupported expression")


def _normalize_math_expression(command):
    expression = command.lower()
    expression = re.sub(r"what is|calculate|compute|solve|jarvis|equals|equal to", " ", expression)

    percent_match = re.search(
        r"(\d+(?:\.\d+)?)\s*percent of\s*(\d+(?:\.\d+)?)",
        expression,
    )
    if percent_match:
        first = percent_match.group(1)
        second = percent_match.group(2)
        return f"({first}/100)*({second})"

    sqrt_match = re.search(r"square root of\s*(\d+(?:\.\d+)?)", expression)
    if sqrt_match:
        value = sqrt_match.group(1)
        return f"({value})**0.5"

    for source, target in MATH_REPLACEMENTS:
        expression = expression.replace(source, target)

    expression = re.sub(r"(?<=\d)\s*x\s*(?=\d)", " * ", expression)
    expression = re.sub(r"[^0-9\.\+\-\*\/%\(\)\s]", " ", expression)
    expression = re.sub(r"\s+", " ", expression).strip()

    return expression


def calculate_expression(command):
    expression = _normalize_math_expression(command)
    if not expression or not re.search(r"\d", expression):
        raise ValueError("No math expression found")

    parsed = ast.parse(expression, mode="eval")
    result = _safe_eval(parsed)

    if isinstance(result, float) and result.is_integer():
        result = int(result)
    elif isinstance(result, float):
        result = round(result, 4)

    return result


def _parse_duration(command):
    match = re.search(
        r"(?:in|after|for)\s+(\d+)\s*(second|seconds|sec|secs|minute|minutes|min|mins|hour|hours|hr|hrs)\b",
        command,
    )
    if not match:
        return None, None

    amount = int(match.group(1))
    unit = match.group(2)

    if unit.startswith("hour") or unit.startswith("hr"):
        return amount * 3600, f"in {amount} hour{'s' if amount != 1 else ''}"
    if unit.startswith("min"):
        return amount * 60, f"in {amount} minute{'s' if amount != 1 else ''}"

    return amount, f"in {amount} second{'s' if amount != 1 else ''}"


def _parse_absolute_time(command):
    match = re.search(r"\bat\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", command)
    if not match:
        return None, None

    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    meridiem = match.group(3)

    if meridiem:
        meridiem = meridiem.lower()
        if hour == 12:
            hour = 0
        if meridiem == "pm":
            hour += 12

    if hour > 23 or minute > 59:
        return None, None

    now = datetime.now()
    due_at = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if "tomorrow" in command or due_at <= now:
        due_at += timedelta(days=1)

    delay_seconds = int((due_at - now).total_seconds())
    due_text = due_at.strftime("at %I:%M %p").replace(" 0", " ")
    return delay_seconds, due_text


def extract_reminder_details(command, existing=None):
    details = dict(existing or {})

    delay_seconds, due_text = _parse_duration(command)
    if delay_seconds is None:
        delay_seconds, due_text = _parse_absolute_time(command)

    if delay_seconds is not None:
        details["delay_seconds"] = delay_seconds
        details["due_text"] = due_text

    patterns = [
        r"remind me to (.+?)(?:\s+(?:in|after|at)\b|$)",
        r"remind me about (.+?)(?:\s+(?:in|after|at)\b|$)",
        r"set (?:a )?reminder to (.+?)(?:\s+(?:in|after|at)\b|$)",
        r"set (?:a )?timer to (.+?)(?:\s+(?:in|after|at)\b|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, command)
        if match:
            message = match.group(1).strip(" .?!,")
            if message:
                details["message"] = message
            break

    if not details.get("message"):
        plain_message = command
        plain_message = re.sub(
            r"(?:in|after|for)\s+\d+\s*(second|seconds|sec|secs|minute|minutes|min|mins|hour|hours|hr|hrs)\b",
            "",
            plain_message,
        )
        plain_message = re.sub(r"\bat\s+\d{1,2}(?::\d{2})?\s*(am|pm)?\b", "", plain_message)
        plain_message = re.sub(r"\b(tomorrow|today)\b", "", plain_message)
        plain_message = normalize_follow_up_text(plain_message)

        if plain_message and plain_message not in {
            "remind me",
            "remind me to",
            "remind me about",
            "set reminder",
            "set a reminder",
            "reminder",
            "timer",
            "set timer",
            "set a timer",
        }:
            details["message"] = plain_message

    if "timer" in command and not details.get("message"):
        details["message"] = "Your timer is up."

    return details


def schedule_reminder(message, delay_seconds):
    due_at = datetime.now() + timedelta(seconds=delay_seconds)
    reminder_text = message.strip().rstrip(".")
    timer = None

    def fire_reminder():
        print(f"[REMINDER] {reminder_text}")

        try:
            speak(f"Reminder. {reminder_text}")
        finally:
            ACTIVE_REMINDERS[:] = [
                item for item in ACTIVE_REMINDERS if item["timer"] is not timer
            ]

    timer = threading.Timer(delay_seconds, fire_reminder)
    timer.daemon = True
    timer.start()

    ACTIVE_REMINDERS.append({
        "message": reminder_text,
        "due_at": due_at,
        "timer": timer,
    })

    return due_at


def _press_media_key(key_code, repeat=1):
    try:
        import ctypes
    except ImportError:
        return False

    user32 = ctypes.windll.user32

    for _ in range(repeat):
        user32.keybd_event(key_code, 0, 0, 0)
        user32.keybd_event(key_code, 0, 2, 0)

    return True


def handle_media_command(command):
    command = command.lower()

    if "next" in command or "skip" in command:
        if not _press_media_key(0xB0):
            return "Media controls are not available on this system."
        return "Skipping to the next track."

    if "previous" in command or "last track" in command or "go back" in command:
        if not _press_media_key(0xB1):
            return "Media controls are not available on this system."
        return "Going back to the previous track."

    if "stop" in command:
        if not _press_media_key(0xB2):
            return "Media controls are not available on this system."
        return "Stopping media playback."

    if "unmute" in command:
        if not _press_media_key(0xAD):
            return "Media controls are not available on this system."
        return "Toggling mute."

    if "mute" in command:
        if not _press_media_key(0xAD):
            return "Media controls are not available on this system."
        return "Toggling mute."

    if "volume up" in command or "increase volume" in command or "louder" in command:
        if not _press_media_key(0xAF, repeat=3):
            return "Media controls are not available on this system."
        return "Turning the volume up."

    if "volume down" in command or "decrease volume" in command or "softer" in command:
        if not _press_media_key(0xAE, repeat=3):
            return "Media controls are not available on this system."
        return "Turning the volume down."

    if "pause" in command:
        if not _press_media_key(0xB3):
            return "Media controls are not available on this system."
        return "Pausing playback."

    if "resume" in command:
        if not _press_media_key(0xB3):
            return "Media controls are not available on this system."
        return "Resuming playback."

    return "I could not work out the media control you wanted."
