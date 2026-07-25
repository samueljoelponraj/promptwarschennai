# ResilienceAI - Multi-Modal GenAI Recovery & Prevention Platform
## System Architecture & Technical Blueprint

### 1. Executive Summary & Vision
**ResilienceAI** is an enterprise-grade, multi-modal, voice-first AI platform engineered to support individuals recovering from substance use disorders (SUD) and empower their caregivers and multidisciplinary care teams. Designed with a **Zero-Typing Philosophy**, the platform integrates multi-agent Generative AI, real-time emotion and speech analysis, predictive risk modeling, and safety-first crisis intervention workflows.

---

### 2. Multi-Agent AI System Architecture

```mermaid
graph TD
    User([User / Voice / Audio]) --> VoiceGateway[Web Speech / Voice Gateway]
    VoiceGateway --> SafetyGuard[Safety & Guardrail Layer]
    
    subgraph Multi-Agent AI Orchestrator
        SafetyGuard --> EvaluatorAgent[Crisis & Urgency Evaluator Agent]
        EvaluatorAgent -->|Low Risk| RecoveryAgent[Motivational Interviewing Agent]
        EvaluatorAgent -->|Moderate Risk| CravingAgent[Craving & De-escalation Agent]
        EvaluatorAgent -->|High Crisis| EmergencyAgent[Emergency SOS Sentinel Agent]
    end
    
    subgraph Data & Memory Layer
        RecoveryAgent <--> VectorDB[(Vector DB / RAG Memory)]
        RecoveryAgent <--> UserProfile[(Firestore User Profile & Streaks)]
        EmergencyAgent --> CaregiverAlerts[Caregiver & Sponsor Alert Dispatch]
    end
    
    Multi-Agent AI Orchestrator --> VoiceSynth[Text-to-Speech Engine]
    VoiceSynth --> User
```

#### Agent Roles & Responsibilities
1. **Crisis & Urgency Evaluator Agent**: Analyzes sentiment, speech velocity, acoustic indicators, and trigger keyphrases ("I want to give up", "I used", "I'm scared") to classify user state into `SAFE`, `ELEVATED_STRESS`, `HIGH_CRAVING`, or `ACUTE_CRISIS`.
2. **Motivational Interviewing (MI) Agent**: Implements evidence-based clinical conversation frameworks (OARS: Open questions, Affirmations, Reflective listening, Summaries) to foster intrinsic motivation without judgment.
3. **Craving Assistant Agent**: Directs users through instant grounded mindfulness, somatic breathing exercises, and cognitive reframing micro-tasks during acute craving spikes.
4. **Emergency SOS Sentinel Agent**: Executes autonomous crisis protocols—dispatching encrypted alerts to designated caregivers/sponsors, serving immediate grounding prompts, and providing one-click emergency responder connections.

---

### 3. Google Cloud Production Architecture

- **Compute & Serverless**: Google Cloud Run hosting FastAPI microservices with auto-scaling down to 0 instances.
- **AI & Foundation Models**: 
  - **Gemini 1.5 Pro / Flash via Vertex AI API** for complex conversational reasoning and multi-modal understanding (document/image OCR for medication labels).
  - **Vertex AI Search & Conversation (RAG)** for clinical knowledge retrieval (CBT exercises, 12-step literature, recovery toolkits).
- **Storage & Database**:
  - **Google Cloud Firestore**: Real-time NoSQL document store for user states, streaks, check-in logs, and caregiver subscriptions.
  - **Cloud Storage (GCS)**: Encrypted storage for optional user voice clips and OCR document scans.
- **Security & Infrastructure**:
  - **Google Cloud Armor & API Gateway**: TLS 1.3 encryption, DDoS mitigation, and OAuth2/JWT authentication.
  - **Secret Manager**: Secure management of API keys and database credentials.

---

### 4. Data Security & HIPAA-Inspired Principles

1. **Zero Knowledge Data Encryption**: All user conversation telemetry, mood logs, and emergency contacts encrypted at rest (AES-256) and in transit (TLS 1.3).
2. **Emergency Override Protocols**: Role-Based Access Control (RBAC) enforcing explicit patient consent before sharing status telemetry with family or clinicians. Emergency overrides trigger audit logs.
3. **Privacy-Preserving Local Fallback**: Safety guardrail evaluation executes locally before API calls, preventing PII leakage during sensitive query parsing.

---

### 5. Multi-Persona Access Matrix

| Persona | Primary Interface | Access Permissions |
| :--- | :--- | :--- |
| **Patient / Recoveree** | Voice-First Mobile/PWA | Full personal access, Voice Assistant, SOS Trigger, Daily Check-in |
| **Caregiver / Family** | Real-time Dashboard | Read-only risk trend indicators, immediate SOS emergency alerts |
| **Sponsor** | Peer Companion View | Check-in streak notifications, peer chat, craving alert notifications |
| **Therapist / Clinician** | Clinical Portal | Aggregate recovery analytics, relapse risk probability, session notes |
| **Emergency Responder** | SOS Alert Gateway | Direct GPS location, critical medical/allergy notes, active contact |
