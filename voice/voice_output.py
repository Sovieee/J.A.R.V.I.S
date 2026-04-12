import pyttsx3
import threading

_lock = threading.Lock()

def speak(text):
    with _lock:
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 180)
            engine.setProperty('volume', 1.0)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            print("TTS ERROR:", e)