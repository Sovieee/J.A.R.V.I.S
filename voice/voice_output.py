import edge_tts
import asyncio
import tempfile
import pygame

pygame.mixer.init()

async def speak_async(text):
    try:
        communicate = edge_tts.Communicate(
            text=text,
            voice="en-US-GuyNeural"  # Jarvis vibe 🔥
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            temp_path = f.name

        await communicate.save(temp_path)

        # 🔥 Play internally (NO media player)
        pygame.mixer.music.load(temp_path)
        pygame.mixer.music.play()

        # Wait until audio finishes
        while pygame.mixer.music.get_busy():
            continue

    except Exception as e:
        print("VOICE ERROR:", e)


def speak(text):
    asyncio.run(speak_async(text))