import os
from voice.voice_output import speak

def open_chrome():
    speak("Opening Chrome")
    os.system("start chrome")
    return "Opening Chrome"

def open_notepad():
    speak("Opening Notepad")
    os.system("notepad")
    return "Opening Notepad"