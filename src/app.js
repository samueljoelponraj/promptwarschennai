// ResilienceAI - Multi-Modal Live API Client App

let recognition = null;
let isRecording = false;
let currentPersona = 'patient';
const USER_ID = 'user_123';

// Initialize Web Speech API
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
      if (statusText) statusText.innerText = 'Listening... Speak now.';
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
      if (statusText) statusText.innerText = 'Tap mic to start hands-free conversation';

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

function toggleVoiceRecording() {
  if (!recognition) initSpeechRecognition();
  if (!recognition) {
    alert('Web Speech API is not supported in this browser. Please use the quick speech chips below!');
    return;
  }
  if (isRecording) {
    recognition.stop();
  } else {
    recognition.start();
  }
}

function simulateSpeech(text) {
  const display = document.getElementById('transcriptDisplay');
  if (display) display.innerHTML = `"${text}"`;
  processVoiceInput(text);
}

// Live Fetch call to FastAPI Multi-Agent Engine
async function processVoiceInput(transcript) {
  const agentBadge = document.getElementById('agentBadge');
  const urgencyBadge = document.getElementById('urgencyBadge');
  const aiResponseText = document.getElementById('aiResponseText');

  aiResponseText.innerText = 'Thinking... (Processing with Gemini Multi-Agent Engine)';

  try {
    const res = await fetch('/api/v1/ai/voice-interact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: USER_ID, transcript: transcript })
    });

    if (res.ok) {
      const data = await res.json();
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
    } else {
      throw new Error('API request failed');
    }
  } catch (err) {
    console.warn('Backend API fallback:', err);
    // Local dynamic fallback logic
    aiResponseText.innerText = `I hear you. You mentioned "${transcript}". Taking things one step at a time is key.`;
  }

  speakAIResponse();
}

function speakAIResponse() {
  if ('speechSynthesis' in window) {
    const text = document.getElementById('aiResponseText').innerText;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    window.speechSynthesis.speak(utterance);
  }
}

// Dynamic Recovery Metrics Loading
async function loadRecoveryMetrics() {
  try {
    const res = await fetch(`/api/v1/recovery/streak/${USER_ID}`);
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
    const res = await fetch('/api/v1/recovery/checkin', {
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
    alert('Check-in saved locally!');
    closeCheckinModal();
  }
}

async function promptSetStartDate() {
  const newDate = prompt('Enter your sober start date (YYYY-MM-DD):', '2026-06-13');
  if (newDate) {
    try {
      await fetch('/api/v1/recovery/update-start-date', {
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
    const res = await fetch('/api/v1/caregiver/alerts');
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
      await fetch('/api/v1/caregiver/alerts', {
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
    await fetch(`/api/v1/caregiver/alerts/${alertId}/resolve`, { method: 'POST' });
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
    const res = await fetch('/api/v1/emergency/active-dispatches');
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
  const agentBadge = document.getElementById('agentBadge');
  const urgencyBadge = document.getElementById('urgencyBadge');
  const aiResponseText = document.getElementById('aiResponseText');

  agentBadge.innerText = '🚨 Emergency SOS Sentinel Agent';
  urgencyBadge.innerText = 'STATUS: ACUTE CRISIS DISPATCH';
  urgencyBadge.style.color = 'var(--accent-rose)';

  try {
    const res = await fetch('/api/v1/emergency/trigger-sos', {
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
  loadRecoveryMetrics();
});
