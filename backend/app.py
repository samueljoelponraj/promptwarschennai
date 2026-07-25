"""
FastAPI Server & Gemini Live WebSocket Bridge for MindCare AI.
Uses Vertex AI with Cloud Run native IAM credentials.
"""

import asyncio
import base64
import json
import os
import traceback
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from google import genai
from google.genai import types

# Load .env file if present
ROOT_DIR = Path(__file__).resolve().parent.parent
env_path = ROOT_DIR / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            os.environ[key.strip()] = val.strip().strip("'\"")

from backend.agent_prompts import (
    DEFAULT_VOICE_NAME,
    DEPRESSION_SUPPORT_SYSTEM_INSTRUCTION,
)
from backend.audio_utils import float32_to_int16, resample_pcm16

app = FastAPI(
    title="MindCare AI - Gemini Live Mental Health Bot",
    description="Real-time WebSocket AI companion for depression and emotional support",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/src", StaticFiles(directory=str(ROOT_DIR / "src")), name="src")


@app.get("/", response_class=HTMLResponse)
async def get_index():
    index_file = ROOT_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>MindCare AI Backend Running</h1>")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "MindCare AI"}


def build_live_config(voice_name: str = DEFAULT_VOICE_NAME):
    return types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        media_resolution="MEDIA_RESOLUTION_MEDIUM",
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
            )
        ),
        system_instruction=types.Content(
            parts=[types.Part.from_text(text=DEPRESSION_SUPPORT_SYSTEM_INSTRUCTION)]
        ),
        context_window_compression=types.ContextWindowCompressionConfig(
            trigger_tokens=104857,
            sliding_window=types.SlidingWindow(target_tokens=52428),
        ),
    )


# Vertex AI Live API compatible model names
VERTEX_LIVE_MODELS = [
    "gemini-live-2.5-flash-native-audio",
    "gemini-2.0-flash-live-001",
]

# Browser AudioContext default sample rate
BROWSER_SAMPLE_RATE = 48000
# Gemini Live API expected sample rate
GEMINI_SAMPLE_RATE = 16000

# Active caregiver WebSocket connections
caregivers = set()

# Crisis keywords to scan on the backend
CRISIS_KEYWORDS = [
    "kill myself", "suicide", "end my life", "want to die",
    "self harm", "self-harm", "harm myself", "cut myself",
    "no reason to live", "better off dead"
]


def scan_for_crisis(text: str) -> str:
    if not text:
        return None
    lower_text = text.lower()
    for kw in CRISIS_KEYWORDS:
        if kw in lower_text:
            return kw
    return None


async def broadcast_to_caregivers(message: dict):
    if caregivers:
        await asyncio.gather(
            *[cg.send_json(message) for cg in caregivers],
            return_exceptions=True
        )


@app.get("/caregiver", response_class=HTMLResponse)
async def get_caregiver_dashboard():
    caregiver_file = ROOT_DIR / "caregiver.html"
    if caregiver_file.exists():
        return HTMLResponse(content=caregiver_file.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Caregiver Dashboard HTML Not Found</h1>")


@app.websocket("/ws/caregiver")
async def websocket_caregiver_endpoint(websocket: WebSocket):
    await websocket.accept()
    caregivers.add(websocket)
    print(f"[WebSocket] Caregiver connected. Active caregivers: {len(caregivers)}")
    try:
        while True:
            # Accept signals from caregiver client
            data = await websocket.receive_json()
            if data.get("type") == "resolve_alert":
                action = data.get("action")
                print(f"[Caregiver] Alert resolved via: {action}")
    except WebSocketDisconnect:
        pass
    finally:
        caregivers.discard(websocket)
        print(f"[WebSocket] Caregiver disconnected. Active caregivers: {len(caregivers)}")



@app.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[WebSocket] Client connected for MindCare AI session.")
    await broadcast_to_caregivers({"type": "session_status", "status": "connected"})

    project = os.environ.get("GCP_PROJECT", "salesforce-503116")
    location = os.environ.get("GCP_LOCATION", "us-central1")
    config = build_live_config()

    # Use Vertex AI with Cloud Run's native Application Default Credentials
    client = genai.Client(vertexai=True, project=project, location=location)
    print(f"[Client Config] Using Vertex AI (Project: {project}, Region: {location})")

    session = None
    connected_context = None
    connected_model = None

    for target_model in VERTEX_LIVE_MODELS:
        try:
            print(f"[Gemini Live] Attempting connection: {target_model}...")
            connected_context = client.aio.live.connect(model=target_model, config=config)
            session = await connected_context.__aenter__()
            connected_model = target_model
            print(f"[Gemini Live] ✅ Connected to {target_model} successfully!")
            break
        except Exception as conn_err:
            err_str = str(conn_err)
            print(f"[Gemini Live] ❌ {target_model} failed: {err_str[:200]}")
            connected_context = None

    if not session:
        err_msg = (
            "[Connection Error] Could not connect to any Gemini Live API model on Vertex AI. "
            "Please ensure the Generative AI API is enabled on your GCP project and the "
            "Cloud Run service account has roles/aiplatform.user."
        )
        print(f"[Error] {err_msg}")
        await websocket.send_json({"type": "transcript", "role": "ai", "content": err_msg})
        await websocket.close()
        return

    audio_chunks_sent = 0
    audio_chunks_received = 0

    try:
        async with asyncio.TaskGroup() as tg:
            async def browser_to_gemini():
                nonlocal audio_chunks_sent
                while True:
                    try:
                        message = await websocket.receive()
                        if "bytes" in message and message["bytes"]:
                            raw_bytes = message["bytes"]

                            pcm_bytes = raw_bytes

                            # Browser now sends 16kHz PCM natively, no resampling needed
                            if len(pcm_bytes) > 0:
                                # Send with explicit sample rate in MIME type
                                await session.send(
                                    input={"data": pcm_bytes, "mime_type": "audio/pcm;rate=16000"}
                                )

                                audio_chunks_sent += 1
                                if audio_chunks_sent % 50 == 0:
                                    print(f"[Audio] Sent {audio_chunks_sent} chunks to Gemini (16kHz PCM, {len(pcm_bytes)} bytes)")

                        elif "text" in message and message["text"]:
                            payload = json.loads(message["text"])
                            msg_type = payload.get("type")

                            if msg_type == "text":
                                user_text = payload.get("content", "")
                                if user_text:
                                    print(f"[Text Input] User: {user_text[:100]}")
                                    await session.send(input=user_text, end_of_turn=True)
                                    # Scan for distress keywords in typed message
                                    if kw := scan_for_crisis(user_text):
                                        await broadcast_to_caregivers({"type": "crisis_alert", "phrase": kw})

                            elif msg_type == "image":
                                b64_img = payload.get("data")
                                mime_type = payload.get("mime_type", "image/jpeg")
                                if b64_img:
                                    img_bytes = base64.b64decode(b64_img)
                                    try:
                                        await session.send(
                                            input=types.LiveClientRealtimeInput(
                                                video=types.Blob(mime_type=mime_type, data=img_bytes)
                                            )
                                        )
                                    except TypeError:
                                        await session.send(
                                            input={"video": {"mime_type": mime_type, "data": img_bytes}}
                                        )

                    except WebSocketDisconnect:
                        print("[WebSocket] Client disconnected.")
                        break
                    except Exception as e:
                        print(f"[Browser -> Gemini Error]: {e}")
                        traceback.print_exc()
                        break

            async def gemini_to_browser():
                nonlocal audio_chunks_received
                try:
                    while True:
                        turn = session.receive()
                        async for response in turn:
                            # Try to get audio data from response
                            audio_data = None

                            # Method 1: Direct data attribute (raw bytes)
                            if hasattr(response, 'data') and response.data:
                                audio_data = response.data

                            # Method 2: server_content with inline parts
                            if audio_data is None and hasattr(response, 'server_content'):
                                sc = response.server_content
                                if sc and hasattr(sc, 'model_turn') and sc.model_turn:
                                    for part in (sc.model_turn.parts or []):
                                        if hasattr(part, 'inline_data') and part.inline_data:
                                            audio_data = part.inline_data.data

                            if audio_data:
                                await websocket.send_bytes(audio_data)
                                audio_chunks_received += 1
                                if audio_chunks_received % 20 == 0:
                                    print(f"[Audio] Sent {audio_chunks_received} audio chunks to browser")

                            # Get user spoken text transcript
                            if hasattr(response, 'server_content') and response.server_content:
                                sc = response.server_content
                                if hasattr(sc, 'user_turn') and sc.user_turn:
                                    for part in (sc.user_turn.parts or []):
                                        if hasattr(part, 'text') and part.text:
                                            print(f"[User Transcript] {part.text[:100]}")
                                            await websocket.send_json(
                                                {"type": "transcript", "role": "user", "content": part.text}
                                            )
                                            # Scan for distress keywords in spoken voice transcript
                                            if kw := scan_for_crisis(part.text):
                                                await broadcast_to_caregivers({"type": "crisis_alert", "phrase": kw})

                            # Get text transcript
                            if hasattr(response, 'text') and response.text:
                                print(f"[AI Transcript] {response.text[:100]}")
                                await websocket.send_json(
                                    {"type": "transcript", "role": "ai", "content": response.text}
                                )

                        await websocket.send_json({"type": "turn_complete"})
                        print(f"[Turn Complete] Audio sent: {audio_chunks_sent}, received: {audio_chunks_received}")

                except Exception as e:
                    print(f"[Gemini -> Browser Error]: {e}")
                    traceback.print_exc()

            tg.create_task(browser_to_gemini())
            tg.create_task(gemini_to_browser())

    finally:
        if connected_context:
            try:
                await connected_context.__aexit__(None, None, None)
            except Exception:
                pass
        print(f"[WebSocket] MindCare AI session terminated (model: {connected_model}). "
              f"Total audio chunks - sent: {audio_chunks_sent}, received: {audio_chunks_received}")
        await broadcast_to_caregivers({"type": "session_status", "status": "disconnected"})


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting MindCare AI server on http://{host}:{port}")
    uvicorn.run("backend.app:app", host=host, port=port, reload=True)
