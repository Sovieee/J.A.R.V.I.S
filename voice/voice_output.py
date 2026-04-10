import pyttsx3

def speak(text):
    try:
        engine = pyttsx3.init()   # 🔥 NEW ENGINE EVERY TIME
        engine.setProperty('rate', 180)
        engine.setProperty('volume', 1.0)

        engine.say(text)
        engine.runAndWait()
        engine.stop()  # 🔥 IMPORTANT

    except Exception as e:
        print("TTS ERROR:", e)