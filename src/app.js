/**
 * MindCare AI - Client-side Web Audio API, WebSocket & Media Controller
 */

// DOM Elements
const btnCall = document.getElementById('btnCall');
const callIcon = document.getElementById('callIcon');
const btnMic = document.getElementById('btnMic');
const micIcon = document.getElementById('micIcon');
const btnCam = document.getElementById('btnCam');
const camIcon = document.getElementById('camIcon');
const btnScreen = document.getElementById('btnScreen');
const screenIcon = document.getElementById('screenIcon');

const statusBadge = document.getElementById('statusBadge');
const statusText = document.getElementById('statusText');
const avatarGlow = document.getElementById('avatarGlow');

const chatFeed = document.getElementById('chatFeed');
const textInput = document.getElementById('textInput');
const btnSendText = document.getElementById('btnSendText');

const videoPreviewContainer = document.getElementById('videoPreviewContainer');
const videoElement = document.getElementById('videoElement');
const visualizerCanvas = document.getElementById('visualizerCanvas');

// Audio & WebSocket State
let ws = null;
let audioCtx = null;         // For mic capture (browser default rate)
let playbackCtx = null;      // Dedicated 24kHz context for Gemini audio playback
let micStream = null;
let audioWorkletNode = null;
let micSource = null;

let videoStream = null;
let videoFrameInterval = null;

let isCallActive = false;
let isMuted = false;
let isCamActive = false;
let isScreenActive = false;

// Audio Playback & Visualizer
let nextPlaybackTime = 0;
let analyserUser = null;
let analyserAI = null;
let animFrameId = null;

// Initialize Visualizer Canvas
const canvasCtx = visualizerCanvas.getContext('2d');

function resizeCanvas() {
  if (visualizerCanvas && visualizerCanvas.parentElement) {
    visualizerCanvas.width = visualizerCanvas.parentElement.clientWidth;
    visualizerCanvas.height = visualizerCanvas.parentElement.clientHeight;
  }
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

function updateStatus(state, text) {
  statusBadge.className = 'status-badge ' + state;
  statusText.textContent = text;
}

function appendMessage(role, text) {
  const lastBubble = chatFeed.lastElementChild;
  if (lastBubble && lastBubble.classList.contains(role) && role === 'ai') {
    lastBubble.textContent += text;
  } else {
    const bubble = document.createElement('div');
    bubble.className = `msg-bubble ${role}`;
    bubble.textContent = text;
    chatFeed.appendChild(bubble);
  }
  chatFeed.scrollTop = chatFeed.scrollHeight;
}

/**
 * Converts Float32 audio array to 16-bit Int16 PCM ArrayBuffer
 */
function floatTo16BitPCM(float32Array) {
  const buffer = new ArrayBuffer(float32Array.length * 2);
  const view = new DataView(buffer);
  for (let i = 0; i < float32Array.length; i++) {
    let s = float32Array[i];
    // Handle NaN/Infinity
    if (isNaN(s) || !isFinite(s)) s = 0;
    s = Math.max(-1, Math.min(1, s));
    view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }
  return buffer;
}

/**
 * Initializes WebSocket connection and AudioContext
 */
async function startCall() {
  try {
    updateStatus('', 'Connecting to MindCare AI...');

    // Capture AudioContext at 16kHz - matches Gemini Live API expected input rate
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    audioCtx = new AudioCtx({ sampleRate: 16000 });
    if (audioCtx.state === 'suspended') {
      await audioCtx.resume();
    }
    console.log('[MindCare] Mic AudioContext sample rate:', audioCtx.sampleRate);

    // Dedicated playback AudioContext at 24kHz for Gemini output
    playbackCtx = new AudioCtx({ sampleRate: 24000 });
    if (playbackCtx.state === 'suspended') {
      await playbackCtx.resume();
    }
    console.log('[MindCare] Playback AudioContext sample rate:', playbackCtx.sampleRate);

    // Setup Analysers
    analyserUser = audioCtx.createAnalyser();
    analyserUser.fftSize = 128;
    analyserAI = playbackCtx.createAnalyser();
    analyserAI.fftSize = 128;

    // Request Microphone Stream
    micStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });

    // Load AudioWorklet Processor
    await audioCtx.audioWorklet.addModule('/src/audio-processor.js');
    audioWorkletNode = new AudioWorkletNode(audioCtx, 'pcm-processor');

    micSource = audioCtx.createMediaStreamSource(micStream);
    micSource.connect(analyserUser);
    micSource.connect(audioWorkletNode);

    // Establish WebSocket connection
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/live`;
    ws = new WebSocket(wsUrl);
    ws.binaryType = 'arraybuffer';

    ws.onopen = () => {
      isCallActive = true;
      nextPlaybackTime = 0;
      updateStatus('connected', 'Connected - MindCare Active');

      // Update Toolbar Controls
      btnCall.className = 'btn-circle danger';
      callIcon.className = 'fa-solid fa-phone-slash';
      btnMic.disabled = false;
      btnCam.disabled = false;
      btnScreen.disabled = false;
      textInput.disabled = false;
      btnSendText.disabled = false;

      avatarGlow.classList.add('active');

      // Send initial trigger to prompt MindCare AI greeting
      ws.send(JSON.stringify({
        type: 'text',
        content: 'Hello MindCare, I am ready to talk. Please greet me warmly.',
      }));

      // Start Microphone Worklet Stream
      audioWorkletNode.port.onmessage = (event) => {
        if (isCallActive && !isMuted && ws && ws.readyState === WebSocket.OPEN) {
          const float32Array = event.data;
          const pcm16Buffer = floatTo16BitPCM(float32Array);
          ws.send(pcm16Buffer);
        }
      };

      startVisualizer();
    };

    ws.onmessage = async (event) => {
      if (typeof event.data === 'string') {
        const msg = JSON.parse(event.data);
        if (msg.type === 'transcript') {
          appendMessage(msg.role, msg.content);
        }
      } else if (event.data instanceof ArrayBuffer && event.data.byteLength > 0) {
        // Incoming 24kHz PCM Audio from Gemini Live API
        playGeminiAudioChunk(event.data);
      }
    };

    ws.onerror = (err) => {
      console.error('WebSocket Error:', err);
      updateStatus('', 'Connection error');
    };

    ws.onclose = () => {
      endCall();
    };

  } catch (err) {
    console.error('Failed to start MindCare call:', err);
    alert('Could not access microphone or connect: ' + err.message);
    endCall();
  }
}

/**
 * Plays 24kHz PCM audio chunks received from Gemini Live API
 */
function playGeminiAudioChunk(arrayBuffer) {
  if (!playbackCtx) return;

  if (playbackCtx.state === 'suspended') {
    playbackCtx.resume();
  }

  const int16Array = new Int16Array(arrayBuffer);
  if (int16Array.length === 0) return;

  const float32Array = new Float32Array(int16Array.length);
  for (let i = 0; i < int16Array.length; i++) {
    float32Array[i] = int16Array[i] / 32768.0;
  }

  // Create AudioBuffer at 24kHz (matches playbackCtx sample rate)
  const audioBuffer = playbackCtx.createBuffer(1, float32Array.length, 24000);
  audioBuffer.getChannelData(0).set(float32Array);

  const source = playbackCtx.createBufferSource();
  source.buffer = audioBuffer;

  source.connect(analyserAI);
  analyserAI.connect(playbackCtx.destination);

  const currentTime = playbackCtx.currentTime;
  if (nextPlaybackTime < currentTime) {
    nextPlaybackTime = currentTime;
  }

  source.start(nextPlaybackTime);
  nextPlaybackTime += audioBuffer.duration;

  updateStatus('speaking', 'MindCare Speaking...');
  const endTime = nextPlaybackTime;
  setTimeout(() => {
    if (playbackCtx && playbackCtx.currentTime >= endTime) {
      updateStatus('connected', 'MindCare Listening');
    }
  }, (endTime - currentTime) * 1000 + 100);
}

/**
 * Canvas Audio Waveform Visualizer
 */
function startVisualizer() {
  const userFreqData = new Uint8Array(analyserUser.frequencyBinCount);
  const aiFreqData = new Uint8Array(analyserAI.frequencyBinCount);

  function draw() {
    animFrameId = requestAnimationFrame(draw);

    if (!analyserUser || !analyserAI) return;
    analyserUser.getByteFrequencyData(userFreqData);
    analyserAI.getByteFrequencyData(aiFreqData);

    canvasCtx.clearRect(0, 0, visualizerCanvas.width, visualizerCanvas.height);

    const centerY = visualizerCanvas.height / 2;
    const barWidth = 4;
    const gap = 3;
    const numBars = Math.floor(visualizerCanvas.width / (barWidth + gap));

    for (let i = 0; i < numBars; i++) {
      const uVal = userFreqData[i % userFreqData.length] || 0;
      const aVal = aiFreqData[i % aiFreqData.length] || 0;

      const combinedVal = Math.max(uVal, aVal);
      const barHeight = (combinedVal / 255) * (visualizerCanvas.height * 0.7) + 4;

      const x = i * (barWidth + gap);
      const y = centerY - barHeight / 2;

      if (aVal > uVal) {
        canvasCtx.fillStyle = '#06b6d4';
      } else if (uVal > 20) {
        canvasCtx.fillStyle = '#0d9488';
      } else {
        canvasCtx.fillStyle = 'rgba(255, 255, 255, 0.1)';
      }

      canvasCtx.beginPath();
      canvasCtx.roundRect(x, y, barWidth, barHeight, 2);
      canvasCtx.fill();
    }
  }

  draw();
}

/**
 * Ends MindCare call
 */
function endCall() {
  isCallActive = false;

  if (ws) { ws.close(); ws = null; }

  if (micStream) {
    micStream.getTracks().forEach((track) => track.stop());
    micStream = null;
  }

  stopVideo();

  if (audioCtx) { audioCtx.close(); audioCtx = null; }
  if (playbackCtx) { playbackCtx.close(); playbackCtx = null; }
  if (animFrameId) { cancelAnimationFrame(animFrameId); }

  updateStatus('', 'Call ended');
  avatarGlow.classList.remove('active');

  btnCall.className = 'btn-circle danger';
  callIcon.className = 'fa-solid fa-phone';

  btnMic.disabled = true;
  btnCam.disabled = true;
  btnScreen.disabled = true;
  textInput.disabled = true;
  btnSendText.disabled = true;

  btnMic.classList.remove('active');
  btnCam.classList.remove('active');
  btnScreen.classList.remove('active');
}

function toggleMic() {
  isMuted = !isMuted;
  if (micStream) {
    micStream.getAudioTracks().forEach((t) => (t.enabled = !isMuted));
  }
  btnMic.classList.toggle('active', isMuted);
  micIcon.className = isMuted ? 'fa-solid fa-microphone-slash' : 'fa-solid fa-microphone';
}

function startVideoFrameSender() {
  if (videoFrameInterval) clearInterval(videoFrameInterval);

  const offCanvas = document.createElement('canvas');
  const offCtx = offCanvas.getContext('2d');

  videoFrameInterval = setInterval(() => {
    if (isCallActive && videoElement.videoWidth && ws && ws.readyState === WebSocket.OPEN) {
      offCanvas.width = 640;
      offCanvas.height = (640 / videoElement.videoWidth) * videoElement.videoHeight;
      offCtx.drawImage(videoElement, 0, 0, offCanvas.width, offCanvas.height);

      const b64Image = offCanvas.toDataURL('image/jpeg', 0.6).split(',')[1];
      ws.send(JSON.stringify({
        type: 'image',
        mime_type: 'image/jpeg',
        data: b64Image,
      }));
    }
  }, 1000);
}

function stopVideo() {
  if (videoFrameInterval) { clearInterval(videoFrameInterval); videoFrameInterval = null; }
  if (videoStream) { videoStream.getTracks().forEach((track) => track.stop()); videoStream = null; }
  videoElement.srcObject = null;
  videoPreviewContainer.classList.remove('active');
  isCamActive = false;
  isScreenActive = false;
  btnCam.classList.remove('active');
  camIcon.className = 'fa-solid fa-video-slash';
  btnScreen.classList.remove('active');
}

async function toggleCam() {
  if (isCamActive) { stopVideo(); return; }
  try {
    stopVideo();
    videoStream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
    videoElement.srcObject = videoStream;
    videoPreviewContainer.classList.add('active');
    isCamActive = true;
    btnCam.classList.add('active');
    camIcon.className = 'fa-solid fa-video';
    startVideoFrameSender();
  } catch (err) { alert('Webcam error: ' + err.message); }
}

async function toggleScreen() {
  if (isScreenActive) { stopVideo(); return; }
  try {
    stopVideo();
    videoStream = await navigator.mediaDevices.getDisplayMedia({ video: true });
    videoElement.srcObject = videoStream;
    videoPreviewContainer.classList.add('active');
    isScreenActive = true;
    btnScreen.classList.add('active');
    videoStream.getVideoTracks()[0].onended = () => stopVideo();
    startVideoFrameSender();
  } catch (err) { alert('Screen share error: ' + err.message); }
}

function sendTextMessage() {
  const text = textInput.value.trim();
  if (text && ws && ws.readyState === WebSocket.OPEN) {
    appendMessage('user', text);
    ws.send(JSON.stringify({ type: 'text', content: text }));
    textInput.value = '';
  }
}

// Event Listeners
btnCall.addEventListener('click', () => {
  if (isCallActive) endCall();
  else startCall();
});

btnMic.addEventListener('click', toggleMic);
btnCam.addEventListener('click', toggleCam);
btnScreen.addEventListener('click', toggleScreen);
btnSendText.addEventListener('click', sendTextMessage);
textInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') sendTextMessage();
});

/**
 * Triggers interactive test scenarios (Crisis Prevention, Panic Grounding, Recovery Guidance)
 */
async function triggerScenario(type) {
  if (!isCallActive) {
    alert('Please start the call first (click the green/red phone icon) to connect to MindCare AI before triggering a scenario.');
    return;
  }

  let prompt = '';
  switch(type) {
    case 'crisis':
      prompt = "I feel completely overwhelmed, hopeless, and I don't want to live anymore. Nothing is working.";
      break;
    case 'panic':
      prompt = "I am having a massive panic attack right now. I can't catch my breath and my chest is tight. Please guide me through the 5-4-3-2-1 grounding exercise.";
      break;
    case 'guidance':
      prompt = "I've been feeling deeply depressed and struggle to get out of bed. Can we design a simple, realistic weekly recovery routine to help me stay active?";
      break;
    default:
      return;
  }

  appendMessage('user', prompt);
  ws.send(JSON.stringify({
    type: 'text',
    content: prompt
  }));
}

// Bind to window so inline HTML onclick handlers can access it
window.triggerScenario = triggerScenario;


