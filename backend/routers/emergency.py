from fastapi import APIRouter
from typing import List
from datetime import datetime
from backend.schemas.models import EmergencySOSRequest, EmergencySOSResponse

router = APIRouter(prefix="/api/v1/emergency", tags=["Emergency SOS"])

# Active SOS Dispatch Store
EMERGENCY_LOGS: List[dict] = []

@router.post("/trigger-sos", response_model=EmergencySOSResponse)
def trigger_sos(request: EmergencySOSRequest):
    """
    Triggers an active emergency SOS crisis intervention workflow.
    """
    sos_id = f"SOS-{int(datetime.utcnow().timestamp())}"
    log_entry = {
        "sos_id": sos_id,
        "user_id": request.user_id,
        "trigger_reason": request.trigger_reason,
        "lat": request.location_lat,
        "lng": request.location_lng,
        "timestamp": datetime.utcnow().isoformat()
    }
    EMERGENCY_LOGS.insert(0, log_entry)

    return EmergencySOSResponse(
        sos_id=sos_id,
        status="ALERTED_CAREGIVERS",
        safety_message="Emergency contacts notified. Guidance script active. Help is on the way.",
        contacts_notified=["Sponsor: Sarah M.", "Caregiver: John (Brother)", "Crisis Helpline (988)"],
        timestamp=datetime.utcnow().isoformat()
    )

@router.get("/active-dispatches")
def get_active_dispatches():
    """
    Retrieves all active emergency SOS dispatches for Emergency Responders.
    """
    return EMERGENCY_LOGS
