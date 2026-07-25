"""
Gemini Multimodal Live API Client

Demonstrates real-time bidirectional streaming (Audio, Video, Screen, Text)
with Google Gemini models using the `google-genai` SDK.

Prerequisites:
    pip install google-genai opencv-python pyaudio pillow mss

Usage:
    export GEMINI_API_KEY="your-api-key"
    python gemini_live_client.py --mode camera
    python gemini_live_client.py --mode screen
    python gemini_live_client.py --mode none
"""

import argparse
import asyncio
import base64
import io
import os
import sys
import traceback

import cv2
import PIL.Image
import pyaudio

from google import genai
from google.genai import types

# Audio Configuration
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

# Default Model & Mode
DEFAULT_MODEL = "models/gemini-2.0-flash-exp"
DEFAULT_MODE = "camera"

# Initialize PyAudio
pya = pyaudio.PyAudio()


def get_genai_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[WARNING] GEMINI_API_KEY environment variable is not set.")
        print("Please set your API key: export GEMINI_API_KEY='your_api_key'")
    return genai.Client(
        http_options={"api_version": "v1beta"},
        api_key=api_key,
    )


class GeminiLiveAudioVideoLoop:
    def __init__(self, video_mode=DEFAULT_MODE, model=DEFAULT_MODEL, target_lang="en"):
        self.video_mode = video_mode
        self.model = model
        self.target_lang = target_lang

        self.audio_in_queue = None
        self.out_queue = None
        self.session = None
        self.audio_stream = None

    def build_config(self):
        """Constructs LiveConnectConfig with audio output and optional translation configuration."""
        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            media_resolution="MEDIA_RESOLUTION_MEDIUM",
            context_window_compression=types.ContextWindowCompressionConfig(
                trigger_tokens=0,
                sliding_window=types.SlidingWindow(target_tokens=0),
            ),
            translation_config=types.TranslationConfig(
                target_language_code=self.target_lang,
            ) if self.target_lang else None,
        )

    async def send_text(self):
        """Task to capture text input from console and send to Gemini Live session."""
        print("\n[Controls] Type a message and press Enter. Type 'q' to quit.\n")
        while True:
            text = await asyncio.to_thread(
                input,
                "message > ",
            )
            if text.lower() == "q":
                break
            if self.session is not None:
                await self.session.send(input=text or ".", end_of_turn=True)

    def _get_frame(self, cap):
        """Reads a frame from OpenCV VideoCapture and formats as JPEG dict."""
        ret, frame = cap.read()
        if not ret:
            return None
        # Convert BGR (OpenCV default) to RGB (PIL format) to avoid color tinting
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = PIL.Image.fromarray(frame_rgb)
        img.thumbnail([1024, 1024])

        image_io = io.BytesIO()
        img.save(image_io, format="jpeg")
        image_io.seek(0)

        image_bytes = image_io.read()
        return {"mime_type": "image/jpeg", "data": base64.b64encode(image_bytes).decode()}

    async def get_frames(self):
        """Background task capturing camera video frames asynchronously."""
        cap = await asyncio.to_thread(cv2.VideoCapture, 0)
        try:
            while True:
                frame = await asyncio.to_thread(self._get_frame, cap)
                if frame is None:
                    break

                await asyncio.sleep(1.0)

                if self.out_queue is not None:
                    await self.out_queue.put(frame)
        finally:
            cap.release()

    def _get_screen(self):
        """Captures primary monitor screen and formats as JPEG dict."""
        try:
            import mss
        except ImportError as e:
            raise ImportError("Please install the mss package using 'pip install mss'") from e

        with mss.mss() as sct:
            monitor = sct.monitors[0]
            sct_img = sct.grab(monitor)
            image_bytes = mss.tools.to_png(sct_img.rgb, sct_img.size)
            img = PIL.Image.open(io.BytesIO(image_bytes))

            image_io = io.BytesIO()
            img.save(image_io, format="jpeg")
            image_io.seek(0)
            return {"mime_type": "image/jpeg", "data": base64.b64encode(image_io.read()).decode()}

    async def get_screen(self):
        """Background task capturing desktop screen frames asynchronously."""
        while True:
            frame = await asyncio.to_thread(self._get_screen)
            if frame is None:
                break

            await asyncio.sleep(1.0)

            if self.out_queue is not None:
                await self.out_queue.put(frame)

    async def send_realtime(self):
        """Pulls audio/image items from output queue and sends to live session."""
        while True:
            if self.out_queue is not None:
                msg = await self.out_queue.get()
                if self.session is not None:
                    await self.session.send(input=msg)

    async def listen_audio(self):
        """Background task reading audio chunks from microphone and putting in output queue."""
        try:
            mic_info = pya.get_default_input_device_info()
            input_device_idx = mic_info["index"]
        except Exception:
            input_device_idx = None

        self.audio_stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=SEND_SAMPLE_RATE,
            input=True,
            input_device_index=input_device_idx,
            frames_per_buffer=CHUNK_SIZE,
        )

        kwargs = {"exception_on_overflow": False} if __debug__ else {}

        while True:
            data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, **kwargs)
            if self.out_queue is not None:
                await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})

    async def receive_audio(self):
        """Background task reading responses from websocket session and writing audio/text."""
        while True:
            if self.session is not None:
                turn = self.session.receive()
                async for response in turn:
                    if data := response.data:
                        self.audio_in_queue.put_nowait(data)
                        continue
                    if text := response.text:
                        print(text, end="", flush=True)

                # Clear queued output audio on interruption
                while not self.audio_in_queue.empty():
                    self.audio_in_queue.get_nowait()

    async def play_audio(self):
        """Background task reading audio chunks from queue and playing to output speaker."""
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        try:
            while True:
                if self.audio_in_queue is not None:
                    bytestream = await self.audio_in_queue.get()
                    await asyncio.to_thread(stream.write, bytestream)
        finally:
            stream.stop_stream()
            stream.close()

    async def run(self):
        """Main execution loop initializing session and starting async task group."""
        client = get_genai_client()
        config = self.build_config()

        try:
            print(f"Connecting to Gemini Live API with model: {self.model} ...")
            async with (
                client.aio.live.connect(model=self.model, config=config) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session

                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=5)

                send_text_task = tg.create_task(self.send_text())
                tg.create_task(self.send_realtime())
                tg.create_task(self.listen_audio())

                if self.video_mode == "camera":
                    tg.create_task(self.get_frames())
                elif self.video_mode == "screen":
                    tg.create_task(self.get_screen())

                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())

                await send_text_task
                raise asyncio.CancelledError("User requested exit")

        except asyncio.CancelledError:
            print("\nExiting session cleanly.")
        except ExceptionGroup as eg:
            print(f"\n[Error] Task execution error occurred:")
            traceback.print_exception(eg)
        except Exception as e:
            print(f"\n[Error] Failed to execute Live session: {e}")
        finally:
            if self.audio_stream is not None:
                try:
                    self.audio_stream.stop_stream()
                    self.audio_stream.close()
                except Exception:
                    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gemini Multimodal Live API Client")
    parser.add_argument(
        "--mode",
        type=str,
        default=DEFAULT_MODE,
        help="Input source to stream: camera, screen, or none",
        choices=["camera", "screen", "none"],
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help="Gemini Live Model (e.g. models/gemini-2.0-flash-exp or models/gemini-3.5-live-translate-preview)",
    )
    parser.add_argument(
        "--lang",
        type=str,
        default="en",
        help="Target translation language code (e.g., 'en', 'es', 'fr')",
    )

    args = parser.parse_args()

    main = GeminiLiveAudioVideoLoop(
        video_mode=args.mode,
        model=args.model,
        target_lang=args.lang,
    )
    asyncio.run(main.run())
