import requests

API_URL = "http://127.0.0.1:11434/api/generate"  # for local LLM (Ollama)

def ask_ai(prompt):
    try:
        response = requests.post(API_URL, json={
            "model": "llama3",   # you can change later
            "prompt": prompt,
            "stream": False
        })

        data = response.json()
        return data.get("response", "Sorry, I couldn't think of a response.")

    except Exception as e:
        return "AI brain is not connected."