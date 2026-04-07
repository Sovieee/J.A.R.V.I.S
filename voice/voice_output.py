import pyttsx3

def speak(text):
    engine = pyttsx3.init()   # 🔥 move inside function

    engine.setProperty('rate', 130)

    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)

    print(f"Jarvis: {text}")
    
    engine.say(text)
    engine.runAndWait()