import os
import subprocess
from voice.voice_output import speak

def open_chrome():
    speak("Opening Chrome")
    os.system("start chrome")
    return "Opening Chrome"

def open_notepad():
    speak("Opening Notepad")
    os.system("notepad")
    return "Opening Notepad"

def open_spotify():
    speak("Opening Spotify")
    os.system("start spotify:")
    return "Opening Spotify"

def open_calculator():
    speak("Opening Calculator")
    os.system("start calc")
    return "Opening Calculator"

def open_vscode():
    speak("Opening VS Code")
    os.system("start code")
    return "Opening VS Code"

def open_whatsapp():
    speak("Opening WhatsApp")
    os.system("start whatsapp:")
    return "Opening WhatsApp"

def open_file_explorer(path=None):
    speak("Opening File Explorer")
    if path:
        os.system(f'start explorer "{path}"')
        return f"Opening {path}"
    else:
        os.system("start explorer")
        return "Opening File Explorer"

def open_netflix():
    speak("Opening Netflix")
    os.system("start shell:AppsFolder\\4DF9E0F8.Netflix_mcm4njqhnhss8!Netflix.App")
    return "Opening Netflix"

def open_prime_video():
    speak("Opening Amazon Prime Video")
    os.system("start shell:AppsFolder\\AmazonVideo.PrimeVideo_pwbj9vvecjh7j!PWA")
    return "Opening Amazon Prime Video"

def open_word():
    speak("Opening Microsoft Word")
    os.system("start winword")
    return "Opening Microsoft Word"

def open_excel():
    speak("Opening Microsoft Excel")
    os.system("start excel")
    return "Opening Microsoft Excel"

def open_powerpoint():
    speak("Opening Microsoft PowerPoint")
    os.system("start powerpnt")
    return "Opening Microsoft PowerPoint"

def open_settings():
    speak("Opening Settings")
    os.system("start ms-settings:")
    return "Opening Settings"