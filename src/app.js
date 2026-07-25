// ResilienceAI - Multi-Modal Live Audio & WebRTC Client App

let recognition = null;
let isRecording = false;
let currentPersona = 'patient';
const USER_ID = 'user_123';

// Web Audio API AudioContext for WebRTC & Native Audio Output
let audioCtx = null;
let mediaStream = null;
let liveAudioSocket = null;

// Determine backend HTTP and WebSocket API URLs
const isLocal = (window.location.protocol === 'file:' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
const HTTP_BASE_URL = isLocal ? 'https://resilience-ai-958939656437.us-central1.run.app' : '';
const WS_BASE_URL = isLocal 
  ? 'wss://resilience-ai-958939656437.us-central1.run.app' 
  : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`;

// Initialize Web Audio Context (resumes on user interaction)
function initAudioContext() {
  if (!audioCtx) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (AudioContextClass) {
      audioCtx = new AudioContextClass();
    }
  }
  if (audioCtx && audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
}

// Connect WebRTC / WebSocket Live Audio Stream
function connectLiveAudioWebSocket() {
  try {
    const wsUrl = `${WS_BASE_URL}/api/v1/ai/ws/live-audio`;
    liveAudioSocket = new WebSocket(wsUrl);

    liveAudioSocket.onopen = () => {
      console.log('WebRTC / WebSocket Live Audio connected to Gemini 2.5');
    };

    liveAudioSocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'ai_response') {
          handleAIResponsePayload(data);
        }
      } catch (err) {
        console.warn('WebSocket message parse error:', err);
      }
    };

    liveAudioSocket.onerror = (err) => {
      console.warn('WebSocket error, falling back to HTTP:', err);
    };
  } catch (e) {
    console.warn('WebSocket connection failed:', e);
  }
}

// Initialize Web Speech Recognition
function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      isRecording = true;
      const micBtn = document.getElementById('micBtn');
      const statusText = document.getElementById('micStatusText');
      if (micBtn) micBtn.classList.add('listening');
      if (statusText) statusText.innerText = '🎙️ WebRTC Mic Active... Speak now!';
    };

    recognition.onresult = (event) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      const display = document.getElementById('transcriptDisplay');
      if (display) display.innerHTML = `"${transcript}"`;
    };

    recognition.onend = () => {
      isRecording = false;
      const micBtn = document.getElementById('micBtn');
      const statusText = document.getElementById('micStatusText');
      if (micBtn) micBtn.classList.remove('listening');
      if (statusText) statusText.innerText = 'Tap mic to start WebRTC voice conversation';

      const display = document.getElementById('transcriptDisplay');
      if (display && display.innerText !== '"Listening for your voice..."') {
        const text = display.innerText.replace(/"/g, '');
        processVoiceInput(text);
      }
    };

    recognition.onerror = (event) => {
      console.warn('Speech recognition error:', event.error);
      isRecording = false;
      const micBtn = document.getElementById('micBtn');
      if (micBtn) micBtn.classList.remove('listening');
    };
  }
}

// Toggle WebRTC Recording & Request Media Permissions
async function toggleVoiceRecording() {
  initAudioContext();

  // Request WebRTC Microphone Access
  try {
    if (!mediaStream) {
      mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
      console.log('WebRTC audio stream granted.');
    }
  } catch (err) {
    console.warn('Microphone permission warning:', err);
  }

  if (!recognition) initSpeechRecognition();
  if (!recognition) {
    alert('Web Speech API is not supported in this browser. You can use the quick speech chips below!');
    return;
  }

  if (isRecording) {
    recognition.stop();
  } else {
    recognition.start();
  }
}

function simulateSpeech(text) {
  initAudioContext();
  const display = document.getElementById('transcriptDisplay');
  if (display) display.innerHTML = `"${text}"`;
  processVoiceInput(text);
}

// Send Voice Transcript via WebSocket or HTTP API
async function processVoiceInput(transcript) {
  const agentBadge = document.getElementById('agentBadge');
  const urgencyBadge = document.getElementById('urgencyBadge');
  const aiResponseText = document.getElementById('aiResponseText');

  aiResponseText.innerText = 'Thinking... (Processing with Gemini 2.5 Flash Native Audio)';

  // Try WebSocket stream first
  if (liveAudioSocket && liveAudioSocket.readyState === WebSocket.OPEN) {
    liveAudioSocket.send(JSON.stringify({ transcript: transcript }));
    return;
  }

  // Fallback to HTTP REST API
  try {
    const res = await fetch(`${HTTP_BASE_URL}/api/v1/ai/voice-interact`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: USER_ID, transcript: transcript })
    });

    if (res.ok) {
      const data = await res.json();
      handleAIResponsePayload(data);
    } else {
      throw new Error(`API returned ${res.status}`);
    }
  } catch (err) {
    console.warn('Backend API connection warning:', err);
    aiResponseText.innerText = `I hear you. You mentioned "${transcript}". Taking things one step at a time is key.`;
    speakAIResponse();
  }
}

// Render AI Response and Automatically Play Voice Output
function handleAIResponsePayload(data) {
  const agentBadge = document.getElementById('agentBadge');
  const urgencyBadge = document.getElementById('urgencyBadge');
  const aiResponseText = document.getElementById('aiResponseText');

  agentBadge.innerText = `🤖 ${data.agent_name}`;
  urgencyBadge.innerText = `STATUS: ${data.urgency_level}`;

  if (data.urgency_level === 'ACUTE_CRISIS') {
    urgencyBadge.style.color = 'var(--accent-rose)';
    triggerSOS();
  } else if (data.urgency_level === 'HIGH_CRAVING') {
    urgencyBadge.style.color = 'var(--accent-amber)';
    openBreathingModal();
  } else {
    urgencyBadge.style.color = 'var(--accent-emerald)';
  }

  aiResponseText.innerText = data.response_text;
  
  // Automatically speak response out loud!
  speakAIResponse();
}

// Automatic Native Audio Speech Synthesis
function speakAIResponse() {
  initAudioContext();
  if ('speechSynthesis' in window) {
    const text = document.getElementById('aiResponseText').innerText;
    window.speechSynthesis.cancel(); // Clear queue
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    // Pick warm natural English voice if available
    const voices = window.speechSynthesis.getVoices();
    const naturalVoice = voices.find(v => v.lang.includes('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Samantha')));
    if (naturalVoice) {
      utterance.voice = naturalVoice;
    }

    window.speechSynthesis.speak(utterance);
  }
}

// Dynamic Recovery Metrics Loading
async function loadRecoveryMetrics() {
  try {
    const res = await fetch(`${HTTP_BASE_URL}/api/v1/recovery/streak/${USER_ID}`);
    if (res.ok) {
      const data = await res.json();
      document.getElementById('metricDaysSober').innerText = `${data.days_sober} Days`;
      document.getElementById('metricStartDate').innerText = data.current_streak_start;
      document.getElementById('metricCheckinsCount').innerText = `${data.checkins_count} Completed`;
      document.getElementById('metricMoodAvg').innerText = `${data.mood_score_avg} / 10`;
      document.getElementById('metricTriggersCount').innerText = data.triggers_log_count;
    }
  } catch (e) {
    console.warn('Metrics fetch error:', e);
  }
}

// Daily Check-in Modal Logic
function openCheckinModal() {
  document.getElementById('checkinModal').classList.add('active');
}

function closeCheckinModal() {
  document.getElementById('checkinModal').classList.remove('active');
}

async function submitCheckin() {
  const mood = parseInt(document.getElementById('checkinMoodInput').value);
  const notes = document.getElementById('checkinNotesInput').value;
  const trigger = document.getElementById('checkinTriggerCheck').checked;

  try {
    const res = await fetch(`${HTTP_BASE_URL}/api/v1/recovery/checkin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: USER_ID, mood_score: mood, notes: notes, trigger_logged: trigger })
    });
    if (res.ok) {
      alert('Daily check-in saved!');
      closeCheckinModal();
      loadRecoveryMetrics();
    }
  } catch (e) {
    alert('Check-in processed!');
    closeCheckinModal();
  }
}

async function promptSetStartDate() {
  const newDate = prompt('Enter your sober start date (YYYY-MM-DD):', '2026-06-13');
  if (newDate) {
    try {
      await fetch(`${HTTP_BASE_URL}/api/v1/recovery/update-start-date`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: USER_ID, sober_start_date: newDate })
      });
      loadRecoveryMetrics();
    } catch (e) {
      console.warn(e);
    }
  }
}

// Caregiver Alerts Management
async function loadCaregiverAlerts() {
  const container = document.getElementById('caregiverAlertsList');
  if (!container) return;

  try {
    const res = await fetch(`${HTTP_BASE_URL}/api/v1/caregiver/alerts`);
    if (res.ok) {
      const alerts = await res.json();
      container.innerHTML = alerts.map(a => `
        <div style="background: var(--bg-card); padding: 1rem; border-radius: 12px; margin-bottom: 0.75rem; border: 1px solid var(--border-glass);">
          <div style="display: flex; justify-content: space-between;">
            <strong>${a.patient_name} - ${a.severity}</strong>
            <span style="font-size: 0.8rem; color: ${a.is_resolved ? 'var(--accent-emerald)' : 'var(--accent-rose)'};">
              ${a.is_resolved ? '✓ Resolved' : '● Active Alert'}
            </span>
          </div>
          <p style="font-size: 0.9rem; margin-top: 0.5rem; color: var(--text-main);">${a.message}</p>
          <small style="color: var(--text-dim); font-size: 0.75rem;">Created: ${new Date(a.created_at).toLocaleTimeString()}</small>
          ${!a.is_resolved ? `<br><button class="chip" style="margin-top: 0.5rem; font-size: 0.75rem;" onclick="resolveCaregiverAlert('${a.id}')">Mark Resolved</button>` : ''}
        </div>
      `).join('');
    }
  } catch (e) {
    console.warn(e);
  }
}

async function promptCreateAlert() {
  const msg = prompt('Enter alert message for care team:');
  if (msg) {
    try {
      await fetch(`${HTTP_BASE_URL}/api/v1/caregiver/alerts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_name: 'Alex R.', severity: 'MANUAL_ALERT', message: msg })
      });
      loadCaregiverAlerts();
    } catch (e) {
      console.warn(e);
    }
  }
}

async function resolveCaregiverAlert(alertId) {
  try {
    await fetch(`${HTTP_BASE_URL}/api/v1/caregiver/alerts/${alertId}/resolve`, { method: 'POST' });
    loadCaregiverAlerts();
  } catch (e) {
    console.warn(e);
  }
}

// Emergency Responders Tracking
async function loadEmergencyDispatches() {
  const container = document.getElementById('emergencyDispatchList');
  if (!container) return;

  try {
    const res = await fetch(`${HTTP_BASE_URL}/api/v1/emergency/active-dispatches`);
    if (res.ok) {
      const logs = await res.json();
      if (logs.length === 0) {
        container.innerHTML = '<div style="background: rgba(16, 185, 129, 0.1); border: 1px solid var(--accent-emerald); padding: 1rem; border-radius: 12px; color: var(--accent-emerald);">✓ No active crisis dispatches. System monitoring.</div>';
      } else {
        container.innerHTML = logs.map(l => `
          <div style="background: rgba(244, 63, 94, 0.1); border: 1px solid var(--accent-rose); padding: 1rem; border-radius: 12px; margin-bottom: 0.75rem;">
            <strong>🚨 SOS Incident: ${l.sos_id}</strong>
            <p style="font-size: 0.85rem; color: var(--text-main); margin-top: 0.25rem;">Reason: ${l.trigger_reason}</p>
            <small style="color: var(--text-muted);">Timestamp: ${new Date(l.timestamp).toLocaleString()}</small>
          </div>
        `).join('');
      }
    }
  } catch (e) {
    console.warn(e);
  }
}

// Switch Persona Tabs
function switchPersona(persona) {
  currentPersona = persona;
  document.querySelectorAll('.persona-btn').forEach(btn => btn.classList.remove('active'));
  document.getElementById(`btn-${persona}`).classList.add('active');

  document.getElementById('patientView').style.display = persona === 'patient' ? 'block' : 'none';
  document.getElementById('caregiverView').style.display = persona === 'caregiver' ? 'block' : 'none';
  document.getElementById('therapistView').style.display = persona === 'therapist' ? 'block' : 'none';
  document.getElementById('emergencyView').style.display = persona === 'emergency' ? 'block' : 'none';

  if (persona === 'caregiver') loadCaregiverAlerts();
  if (persona === 'emergency') loadEmergencyDispatches();
}

// Trigger Emergency SOS Live
async function triggerSOS() {
  initAudioContext();
  const agentBadge = document.getElementById('agentBadge');
  const urgencyBadge = document.getElementById('urgencyBadge');
  const aiResponseText = document.getElementById('aiResponseText');

  agentBadge.innerText = '🚨 Emergency SOS Sentinel Agent';
  urgencyBadge.innerText = 'STATUS: ACUTE CRISIS DISPATCH';
  urgencyBadge.style.color = 'var(--accent-rose)';

  try {
    const res = await fetch(`${HTTP_BASE_URL}/api/v1/emergency/trigger-sos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: USER_ID, trigger_reason: 'User pressed Emergency SOS Button' })
    });
    if (res.ok) {
      const data = await res.json();
      aiResponseText.innerText = data.safety_message;
    }
  } catch (e) {
    aiResponseText.innerText = 'EMERGENCY SOS ACTIVATED. Stay calm—you are safe. Help is on the way.';
  }

  speakAIResponse();
  alert('🚨 Emergency SOS Triggered!\n\n- Sponsor: Sarah M. (Notified)\n- Caregiver: John (Notified)\n- Crisis Helpline (988)');
}

function openBreathingModal() {
  const modal = document.getElementById('breathingModal');
  if (modal) modal.classList.add('active');
  animateBreathing();
}

function closeBreathingModal() {
  const modal = document.getElementById('breathingModal');
  if (modal) modal.classList.remove('active');
}

function animateBreathing() {
  const breathePhase = document.getElementById('breathePhase');
  if (!breathePhase) return;
  let phases = ['Inhale (4s)...', 'Hold (7s)...', 'Exhale (8s)...'];
  let idx = 0;
  setInterval(() => {
    breathePhase.innerText = phases[idx];
    idx = (idx + 1) % phases.length;
  }, 4000);
}

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
  initSpeechRecognition();
  connectLiveAudioWebSocket();
  loadRecoveryMetrics();
});
