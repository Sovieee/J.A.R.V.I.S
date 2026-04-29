from groq import Groq
import os
from intelligence.context_memory import conversation_history
from intelligence.memory import get_fact
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MAX_HISTORY = 10  # limit memory


def build_memory_context():
    """🔹 Build long-term memory context"""
    name = get_fact("name")
    nickname = get_fact("nickname")
    likes = get_fact("likes")

    memory_parts = []

    if name:
        memory_parts.append(f"User's name is {name}.")

    if nickname:
        memory_parts.append(f"You call the user '{nickname}'.")

    if likes:
        memory_parts.append(f"User likes {likes}.")

    return " ".join(memory_parts)


def ask_ai(prompt):
    try:
        messages = []
        from intelligence.context_state import get_context

        location = get_context("location")

        if location:
            location_text = f"User is currently in {location.get('city')}."
        else:
            location_text = "User location is unknown."

        # 🔥 Inject MEMORY into system prompt
        memory_context = build_memory_context()

        messages.append({
            "role": "system",
            "content": (
                "You are J.A.R.V.I.S, a smart, witty, and slightly sarcastic AI assistant. "
                "Keep responses concise, helpful, and confident.\n\n"
                f"{memory_context}\n"
                f"{location_text}\n"
                "Use this information naturally when relevant."
            )
        })

        # 🔹 Short-term memory
        recent_history = conversation_history[-MAX_HISTORY:]

        for entry in recent_history:
            messages.append({
                "role": entry["role"],
                "content": entry["message"]
            })

        # 🔹 Current input
        messages.append({
            "role": "user",
            "content": prompt
        })

        # 🔹 API call
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )

        reply = response.choices[0].message.content

        # 🔹 Save conversation
        conversation_history.append({"role": "user", "message": prompt})
        conversation_history.append({"role": "assistant", "message": reply})

        return reply

    except Exception as e:
        print("AI ERROR:", e)
        return "JARVIS is currently offline. Try again shortly."