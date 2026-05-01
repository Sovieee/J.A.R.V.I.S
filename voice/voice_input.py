import speech_recognition as sr
import time
from voice.voice_output import wait_until_idle

time.sleep(1)
def listen_command():
    wait_until_idle()

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.pause_threshold = 0.8

    with sr.Microphone() as source:
        print("Listening...")

        recognizer.adjust_for_ambient_noise(source, duration=1)

        try:
            audio = recognizer.listen(
                source,
                timeout=5,              # wait for speech
                phrase_time_limit=5     # max speaking time
            )

            print("Recognizing...")
            command = recognizer.recognize_google(audio)
            print(f"You said: {command}")

            return command.lower()

        except sr.WaitTimeoutError:
            print("Listening timed out...")
            return ""

        except sr.UnknownValueError:
            print("Sorry, I could not understand.")
            return ""

        except sr.RequestError:
            print("Network error.")
            return ""
