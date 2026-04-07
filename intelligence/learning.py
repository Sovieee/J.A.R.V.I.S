import json
import os
from datetime import datetime
from intelligence.time_context import get_time_period

LOG_FILE = "activity_log.json"


def load_logs():
    if not os.path.exists(LOG_FILE):
        return []

    with open(LOG_FILE, "r") as file:
        return json.load(file)


def save_logs(logs):
    with open(LOG_FILE, "w") as file:
        json.dump(logs, file, indent=4)


def log_activity(command):
    logs = load_logs()

    entry = {
        "command": command,
        "time": datetime.now().strftime("%H:%M"),
        "period": get_time_period()
    }

    logs.append(entry)
    save_logs(logs)


def get_frequent_actions():
    logs = load_logs()

    frequency = {}

    for log in logs:
        cmd = log.get("command")

# 🛡️ SAFETY FIX
        if isinstance(cmd, dict):
            cmd = cmd.get("command") or cmd.get("intent")

        if not isinstance(cmd, str):
            continue

        cmd = cmd.strip().lower()

        if not cmd:
            continue

        frequency[cmd] = frequency.get(cmd, 0) + 1

    # sort by frequency
    sorted_actions = sorted(frequency.items(), key=lambda x: x[1], reverse=True)

    return sorted_actions[:3]  # top 3

def get_time_based_suggestion():
    logs = load_logs()
    current_period = get_time_period()

    filtered = [
        log for log in logs
        if log.get("period") == current_period
    ]

    frequency = {}

    for log in filtered:
        cmd = log.get("command")

        # 🛡️ handle corrupted data
        if isinstance(cmd, dict):
            cmd = cmd.get("command") or cmd.get("intent")

        if not isinstance(cmd, str):
            continue

        cmd = cmd.strip().lower()

        frequency[cmd] = frequency.get(cmd, 0) + 1

    if not frequency:
        return None

    sorted_actions = sorted(frequency.items(), key=lambda x: x[1], reverse=True)

    return sorted_actions[0][0]