import webbrowser
from voice.voice_output import speak

def search_google(query):
    speak(f"Searching for {query}")
    
    url = f"https://www.google.com/search?q={query}"
    webbrowser.open(url)
    return f"Searching for {query}"