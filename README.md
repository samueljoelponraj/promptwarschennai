# MindCare AI - Gemini 3.1 Live WebRTC / Web Audio Mental Health & Depression Support Bot

MindCare AI is a real-time, bi-directional voice, video, and text emotional support bot powered by the **Google Gemini 3.1 Flash Live API** (`models/gemini-3.1-flash-live-preview`).

---

## Key Features

- **Real-Time Bidirectional Voice**: Built with Web Audio API & `AudioWorklet` for ultra-low latency microphone recording and playback.
- **Empathetic AI Companion**: Custom persona (`MindCare Companion`) trained for active listening, empathetic validation, and non-judgmental support.
- **Voice Response ("Zephyr")**: Expressive voice audio response using Gemini's prebuilt `Zephyr` voice.
- **Multimodal Visual Inputs**: Support for optional webcam and desktop screen share streaming directly into the Gemini Live context.
- **Dual Visualizer Canvas**: Real-time oscilloscope audio waveform canvas reacting to user voice and AI speech.
- **Built-In Crisis Escalation**: Automatic safety protocol including crisis hotline resource guidance (988 Lifeline).

---

## Quickstart Guide

### 1. Prerequisites
- Python 3.10+
- Google Gemini API Key with Live API access (`GEMINI_API_KEY`)

### 2. Installation

Install required dependencies:

```bash
pip install -r requirements.txt
```

### 3. Environment Setup

Set your Gemini API Key:

**PowerShell (Windows)**:
```powershell
$env:GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
```

**Bash (Linux/macOS)**:
```bash
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
```

### 4. Run the Server

Start the FastAPI application:

```bash
python backend/app.py
```

Or using uvicorn:

```bash
uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

### 5. Access the Web UI

Open your browser and navigate to:
```
http://localhost:8000
```

1. Click the **Call Button** (phone icon).
2. Allow microphone access when prompted.
3. Start speaking naturally to **MindCare Companion**.

---

## File Structure

```
promptwarchenai/
├── backend/
│   ├── app.py              # FastAPI server & WebSocket Gemini Live Bridge
│   ├── agent_prompts.py    # Empathetic depression support persona & system instructions
│   └── audio_utils.py      # Resampling utilities for browser & Gemini PCM audio
├── src/
│   ├── app.js              # Web Audio API controller, WebSocket manager & UI logic
│   ├── audio-processor.js  # AudioWorklet processor for raw PCM input
│   └── styles/
│       └── theme.css       # Soothing glassmorphic dark design system
├── index.html              # Main web app layout
├── gemini_live_client.py   # CLI version reference script
├── requirements.txt        # Backend python dependencies
└── README.md               # Project documentation
```

---

## Disclaimer

> **MindCare AI is an AI-assisted emotional listener, not a licensed medical professional, therapist, or crisis service.** If you or someone you know is experiencing a mental health emergency or thoughts of self-harm, please call or text **988** (US & Canada), call **111** (UK), or contact your local emergency services immediately.
