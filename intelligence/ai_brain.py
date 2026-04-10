import requests
from intelligence.context_memory import conversation_history

API_URL = "http://127.0.0.1:11434/api/chat"

def ask_ai(prompt):
    try:
        messages = []

        # 🔹 System personality
        messages.append({
            "role": "system",
            "content": "You are Jarvis, a smart AI assistant. Answer clearly and briefly."
        })

        # 🔹 Add past conversation
        for entry in conversation_history:
            messages.append({
                "role": entry["role"],
                "content": entry["message"]
            })

        # 🔹 Current input
        messages.append({
            "role": "user",
            "content": prompt
        })

        response = requests.post(API_URL, json={
            "model": "llama3",
            "messages": messages,
            "stream": False
        })

        data = response.json()

        return data["message"]["content"]

    except Exception as e:
        print("AI ERROR:", e)
        return "AI brain is not connected."