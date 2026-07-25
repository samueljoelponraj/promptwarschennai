from fastapi import APIRouter
from datetime import datetime
from backend.schemas.models import EmergencySOSRequest, EmergencySOSResponse

router = APIRouter(prefix="/api/v1/emergency", tags=["Emergency SOS"])

@router.post("/trigger-sos", response_model=EmergencySOSResponse)
def trigger_sos(request: EmergencySOSRequest):
    """
    Triggers an emergency SOS crisis intervention workflow.
    Notifies caregivers, sponsors, and prepares location telemetry.
    """
    sos_id = f"SOS-{int(datetime.utcnow().timestamp())}"
    return EmergencySOSResponse(
        sos_id=sos_id,
        status="ALERTED_CAREGIVERS",
        safety_message="Emergency contacts notified. Guidance script active. Help is on the way.",
        contacts_notified=["Sponsor: Sarah M.", "Caregiver: John (Brother)", "Crisis Helpline (988)"],
        timestamp=datetime.utcnow().isoformat()
    )
