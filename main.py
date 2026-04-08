from voice.wake_listener import listen_wake_word
from commands.command_handler import handle_command

print("🚀 Jarvis is running... Say 'Hey Jarvis'")

while True:
    command = listen_wake_word()

    if command:
        print(f"[WAKE] Command: {command}")
        response = handle_command(command)
        print("Jarvis:", response)