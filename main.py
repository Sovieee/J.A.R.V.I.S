from commands.command_handler import handle_command
from voice.voice_input import listen_command


def run_jarvis():
    print("Jarvis is running...")

    # 🔹 Ask mode only once
    mode = input("Choose mode - voice (v) or text (t): ").lower()

    while True:
        if mode == "v":
            command = listen_command()
        else:
            command = input("You: ")

        if command:
            handle_command(command)


if __name__ == "__main__":
    run_jarvis()