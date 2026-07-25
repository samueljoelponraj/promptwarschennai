from fastapi import APIRouter
from typing import List
from datetime import datetime
from backend.schemas.models import CaregiverAlert

router = APIRouter(prefix="/api/v1/caregiver", tags=["Caregiver Portal"])

@router.get("/alerts", response_model=List[CaregiverAlert])
def get_alerts():
    """
    Retrieves real-time alerts for caregivers and care teams.
    """
    return [
        CaregiverAlert(
            id="ALT-101",
            patient_name="Alex R.",
            severity="ELEVATED_STRESS",
            message="Speech analysis detected elevated stress & fatigue during morning check-in.",
            created_at=datetime.utcnow().isoformat(),
            is_resolved=False
        ),
        CaregiverAlert(
            id="ALT-102",
            patient_name="Alex R.",
            severity="MILESTONE",
            message="Completed 40 days sober milestone! Send a supportive message.",
            created_at=datetime.utcnow().isoformat(),
            is_resolved=True
        )
    ]
