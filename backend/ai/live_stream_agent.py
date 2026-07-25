"""
ResilienceAI - Live Gemini Multimodal Audio & Video Streaming Agent
Powered by google.genai SDK (client.aio.live.connect)
"""

import os
import asyncio
import base64
import io
import traceback
import argparse

import cv2
import PIL.Image

try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False

try:
    from google import genai
    from google.genai import types
    HAS_GENAI_SDK = True
except ImportError:
    HAS_GENAI_SDK = False

FORMAT = pyaudio.paInt16 if HAS_PYAUDIO else 16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

MODEL = "models/gemini-2.5-flash-native-audio"
DEFAULT_MODE = "camera"

class ResilienceLiveAudioLoop:
    """
    Bi-directional Live Multimodal Audio/Video streaming agent connecting to
    Gemini Live API using google.genai.
    """
    def __init__(self, video_mode=DEFAULT_MODE):
        self.video_mode = video_mode
        self.audio_in_queue = None
        self.out_queue = None
        self.session = None
        self.audio_stream = None

        if HAS_GENAI_SDK:
            self.client = genai.Client(
                http_options={"api_version": "v1beta"},
                api_key=os.environ.get("GEMINI_API_KEY"),
            )
            self.config = types.LiveConnectConfig(
                response_modalities=["AUDIO"],
                media_resolution="MEDIA_RESOLUTION_MEDIUM",
                context_window_compression=types.ContextWindowCompressionConfig(
                    trigger_tokens=0,
                    sliding_window=types.SlidingWindow(target_tokens=0),
                ),
                system_instruction=types.Content(
                    parts=[types.Part.from_text(
                        "You are an empathetic, clinical GenAI Recovery Companion (ResilienceAI). "
                        "You speak directly to individuals recovering from substance use disorder. "
                        "Use Motivational Interviewing (OARS) principles. Be warm, grounding, and immediate."
                    )]
                )
            )

    async def send_text(self):
        while True:
            text = await asyncio.to_thread(input, "ResilienceAI Voice Prompt > ")
            if text.lower() == "q":
                break
            if self.session is not None:
                await self.session.send(input=text or ".", end_of_turn=True)

    def _get_frame(self, cap):
        ret, frame = cap.read()
        if not ret:
            return None
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = PIL.Image.fromarray(frame_rgb)
        img.thumbnail([1024, 1024])

        image_io = io.BytesIO()
        img.save(image_io, format="jpeg")
        image_io.seek(0)
        return {"mime_type": "image/jpeg", "data": base64.b64encode(image_io.read()).decode()}

    async def get_frames(self):
        try:
            cap = await asyncio.to_thread(cv2.VideoCapture, 0)
            while True:
                frame = await asyncio.to_thread(self._get_frame, cap)
                if frame is None:
                    break
                await asyncio.sleep(1.0)
                if self.out_queue is not None:
                    await self.out_queue.put(frame)
            cap.release()
        except Exception as e:
            print(f"Video capture notice: {e}")

    async def send_realtime(self):
        while True:
            if self.out_queue is not None:
                msg = await self.out_queue.get()
                if self.session is not None:
                    await self.session.send(input=msg)

    async def listen_audio(self):
        if not HAS_PYAUDIO:
            return
        pya = pyaudio.PyAudio()
        try:
            mic_info = pya.get_default_input_device_info()
            self.audio_stream = await asyncio.to_thread(
                pya.open,
                format=FORMAT,
                channels=CHANNELS,
                rate=SEND_SAMPLE_RATE,
                input=True,
                input_device_index=mic_info["index"],
                frames_per_buffer=CHUNK_SIZE,
            )
            while True:
                data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, exception_on_overflow=False)
                if self.out_queue is not None:
                    await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})
        except Exception as e:
            print(f"Audio microphone capture notice: {e}")

    async def receive_audio(self):
        while True:
            if self.session is not None:
                turn = self.session.receive()
                async for response in turn:
                    if data := response.data:
                        if self.audio_in_queue:
                            self.audio_in_queue.put_nowait(data)
                        continue
                    if text := response.text:
                        print(text, end="", flush=True)

                while self.audio_in_queue and not self.audio_in_queue.empty():
                    self.audio_in_queue.get_nowait()

    async def play_audio(self):
        if not HAS_PYAUDIO:
            return
        pya = pyaudio.PyAudio()
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        while True:
            if self.audio_in_queue is not None:
                bytestream = await self.audio_in_queue.get()
                await asyncio.to_thread(stream.write, bytestream)

    async def run(self):
        if not HAS_GENAI_SDK or not os.environ.get("GEMINI_API_KEY"):
            print("Notice: google.genai SDK or GEMINI_API_KEY required for standalone live agent run.")
            return

        try:
            async with (
                self.client.aio.live.connect(model=MODEL, config=self.config) as session,
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

                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())

                await send_text_task
                raise asyncio.CancelledError("User requested exit")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            if self.audio_stream is not None:
                self.audio_stream.close()
            traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default=DEFAULT_MODE, choices=["camera", "screen", "none"])
    args = parser.parse_args()
    agent = ResilienceLiveAudioLoop(video_mode=args.mode)
    asyncio.run(agent.run())
