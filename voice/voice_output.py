import asyncio
import os
import queue
import tempfile
import threading
import time

import edge_tts
import pygame

pygame.mixer.init()

_speech_queue = queue.Queue()
_speech_active = threading.Event()


async def speak_async(text):
    temp_path = None

    try:
        communicate = edge_tts.Communicate(
            text=text,
            voice="en-US-GuyNeural"
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as file:
            temp_path = file.name

        await communicate.save(temp_path)

        pygame.mixer.music.load(temp_path)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.wait(50)

    except Exception as error:
        print("VOICE ERROR:", error)
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def _speech_worker():
    while True:
        text = _speech_queue.get()

        if text is None:
            _speech_queue.task_done()
            break

        _speech_active.set()

        try:
            asyncio.run(speak_async(text))
        finally:
            _speech_active.clear()
            _speech_queue.task_done()


_worker_thread = threading.Thread(target=_speech_worker, daemon=True)
_worker_thread.start()


def speak(text):
    if not text:
        return

    _speech_queue.put(str(text))


def is_speaking():
    return _speech_active.is_set() or not _speech_queue.empty()


def wait_until_idle():
    while is_speaking():
        time.sleep(0.05)
