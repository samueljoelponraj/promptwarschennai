// ResilienceAI - Multi-Modal Voice Recovery Client App

let recognition = null;
let isRecording = false;
let currentPersona = 'patient';

// Initialize Web Speech API if supported by browser
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

// Toggle recording state
function toggleVoiceRecording() {
  if (!recognition) {
    initSpeechRecognition();
  }
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

// Simulate speech chips
function simulateSpeech(text) {
  const display = document.getElementById('transcriptDisplay');
  if (display) display.innerHTML = `"${text}"`;
  processVoiceInput(text);
}

// Client-side simulation of Multi-Agent AI System
function processVoiceInput(transcript) {
  const agentBadge = document.getElementById('agentBadge');
  const urgencyBadge = document.getElementById('urgencyBadge');
  const aiResponseText = document.getElementById('aiResponseText');

  const textLower = transcript.toLowerCase();

  if (textLower.includes('craving') || textLower.includes('urge') || textLower.includes('stress')) {
    agentBadge.innerText = '🫁 Craving De-escalation Agent';
    urgencyBadge.innerText = 'STATUS: HIGH CRAVING';
    urgencyBadge.style.color = 'var(--accent-amber)';
    aiResponseText.innerText = 'Thank you for speaking up. Cravings are temporary feelings that rise and fall like waves. Let us perform a quick 4-7-8 breathing grounding exercise right now.';
    openBreathingModal();
  } else if (textLower.includes('milestone') || textLower.includes('sober') || textLower.includes('days')) {
    agentBadge.innerText = '🤖 Motivational Companion Agent';
    urgencyBadge.innerText = 'STATUS: MILESTONE CELEBRATION';
    urgencyBadge.style.color = 'var(--accent-emerald)';
    aiResponseText.innerText = 'Congratulations on hitting your 40 days sobriety milestone! That demonstrates incredible commitment and resilience.';
  } else {
    agentBadge.innerText = '🤖 Motivational Companion Agent';
    urgencyBadge.innerText = 'STATUS: SAFE';
    urgencyBadge.style.color = 'var(--accent-emerald)';
    aiResponseText.innerText = `I hear you. You mentioned "${transcript}". What is one small positive goal you can focus on today to maintain your strength?`;
  }

  speakAIResponse();
}

// Text-to-Speech synthesis
function speakAIResponse() {
  if ('speechSynthesis' in window) {
    const text = document.getElementById('aiResponseText').innerText;
    window.speechSynthesis.cancel(); // Cancel any ongoing speech
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    window.speechSynthesis.speak(utterance);
  }
}

// Switch Persona Views
function switchPersona(persona) {
  currentPersona = persona;
  const buttons = document.querySelectorAll('.persona-btn');
  buttons.forEach(btn => btn.classList.remove('active'));

  event.target.classList.add('active');

  document.getElementById('patientView').style.display = persona === 'patient' ? 'block' : 'none';
  document.getElementById('caregiverView').style.display = persona === 'caregiver' ? 'block' : 'none';
  document.getElementById('therapistView').style.display = persona === 'therapist' ? 'block' : 'none';
  document.getElementById('emergencyView').style.display = persona === 'emergency' ? 'block' : 'none';
}

// Emergency SOS trigger
function triggerSOS() {
  const agentBadge = document.getElementById('agentBadge');
  const urgencyBadge = document.getElementById('urgencyBadge');
  const aiResponseText = document.getElementById('aiResponseText');

  agentBadge.innerText = '🚨 Emergency SOS Sentinel Agent';
  urgencyBadge.innerText = 'STATUS: ACUTE CRISIS DISPATCH';
  urgencyBadge.style.color = 'var(--accent-rose)';

  aiResponseText.innerText = 'EMERGENCY SOS ACTIVATED. Stay calm—you are safe. Notifications with your GPS location have been sent to your primary caregiver, sponsor, and local crisis line.';

  speakAIResponse();
  alert('🚨 Emergency SOS Activated!\n\n- Sponsor: Sarah M. (Notified)\n- Caregiver: John (Brother) (Notified)\n- Crisis Line (988) Standby');
}

// Breathing exercise modal controls
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
});
