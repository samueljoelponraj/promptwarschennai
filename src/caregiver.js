/**
 * Caregiver Dashboard WebSocket Monitor & Alerts Engine
 */

let ws = null;
let audioCtx = null;
let alarmInterval = null;

const alertsLog = document.getElementById('alertsLog');
const vitalState = document.getElementById('vitalState');
const vitalHeartRate = document.getElementById('vitalHeartRate');
const emergencyOverlay = document.getElementById('emergencyOverlay');
const patientConnState = document.getElementById('patientConnState');
const alertDescription = document.getElementById('alertDescription');

function appendAlertLog(type, message) {
  const logItem = document.createElement('div');
  logItem.className = `alert-log-item ${type}`;

  const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  logItem.innerHTML = `
    <span class="log-time">${time}</span>
    <span class="log-msg">${message}</span>
  `;

  alertsLog.appendChild(logItem);
  alertsLog.scrollTop = alertsLog.scrollHeight;
}

function initAudioContext() {
  if (!audioCtx) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    audioCtx = new AudioContextClass();
  }
  if (audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
}

function playAlarmSound() {
  initAudioContext();
  if (!audioCtx) return;

  if (alarmInterval) clearInterval(alarmInterval);

  alarmInterval = setInterval(() => {
    if (!emergencyOverlay.classList.contains('active')) {
      clearInterval(alarmInterval);
      alarmInterval = null;
      return;
    }

    try {
      const osc = audioCtx.createOscillator();
      const gainNode = audioCtx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(880, audioCtx.currentTime); // A5 note
      osc.frequency.exponentialRampToValueAtTime(440, audioCtx.currentTime + 0.4);

      gainNode.gain.setValueAtTime(0.08, audioCtx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.4);

      osc.connect(gainNode);
      gainNode.connect(audioCtx.destination);

      osc.start();
      osc.stop(audioCtx.currentTime + 0.45);
    } catch (e) {
      console.warn('[Alarm Audio Error]', e);
    }
  }, 900);
}

function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/caregiver`;
  
  console.log('[Caregiver] Connecting to monitor WebSocket:', wsUrl);
  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log('[Caregiver] Connected to backend monitor.');
    patientConnState.textContent = 'Monitoring';
    patientConnState.style.color = 'var(--primary-cyan)';
    appendAlertLog('info', 'Secure link to Patient Monitor established.');
  };

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    console.log('[Caregiver] Message received:', msg);

    if (msg.type === 'crisis_alert') {
      // 1. Update Patient Vitals
      vitalState.textContent = 'Crisis';
      vitalState.className = 'vital-val critical';
      vitalHeartRate.innerHTML = `<i class="fa-solid fa-heart pulse-fast text-danger"></i> 134 bpm`;

      // 2. Open warning overlay & start alarm sound
      alertDescription.innerHTML = `Patient Samuel Ponraj has triggered safety protocols.<br><strong>Trigger Phrase:</strong> "${msg.phrase}"`;
      emergencyOverlay.classList.add('active');
      playAlarmSound();

      // 3. Log event
      appendAlertLog('critical', `🚨 CRITICAL DISTRESS ALERT: Suicide/Self-harm indicators detected ("${msg.phrase}").`);
    } else if (msg.type === 'session_status') {
      if (msg.status === 'connected') {
        patientConnState.textContent = 'Active Call';
        patientConnState.style.color = 'var(--success-green)';
        appendAlertLog('info', 'Patient has initiated a call with MindCare AI.');
      } else if (msg.status === 'disconnected') {
        patientConnState.textContent = 'Monitoring';
        patientConnState.style.color = 'var(--primary-cyan)';
        appendAlertLog('info', 'Patient call with MindCare AI ended.');
      }
    }
  };

  ws.onerror = (err) => {
    console.error('[Caregiver] WebSocket error:', err);
    patientConnState.textContent = 'Error';
    patientConnState.style.color = 'var(--danger-red)';
  };

  ws.onclose = () => {
    console.log('[Caregiver] WebSocket disconnected. Retrying in 3s...');
    patientConnState.textContent = 'Offline';
    patientConnState.style.color = 'var(--text-dim)';
    setTimeout(connectWebSocket, 3000);
  };
}

function resolveEmergency(action) {
  // Dismiss Overlay & Alarm
  emergencyOverlay.classList.remove('active');
  if (alarmInterval) {
    clearInterval(alarmInterval);
    alarmInterval = null;
  }

  // Restore vitals to stable
  vitalState.textContent = 'Stable';
  vitalState.className = 'vital-val stable';
  vitalHeartRate.innerHTML = `<i class="fa-solid fa-heart pulse-slow text-danger"></i> 72 bpm`;

  let actionText = '';
  switch (action) {
    case 'called':
      actionText = '📞 Caregiver initiated direct phone call. Checking on patient.';
      break;
    case 'dispatched':
      actionText = '🚑 Caregiver contacted 988 emergency services.';
      break;
    case 'dismissed':
      actionText = '✔️ Caregiver dismissed alarm. Reset monitoring state.';
      break;
  }
  
  appendAlertLog('info', actionText);

  // Send resolve signal to backend if websocket is connected
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'resolve_alert',
      action: action
    }));
  }
}

// Bind resolveEmergency to window for HTML accessibility
window.resolveEmergency = resolveEmergency;

// Auto-connect on page load
connectWebSocket();
