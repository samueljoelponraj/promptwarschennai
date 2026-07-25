from fastapi import APIRouter
from typing import List
from datetime import datetime
from backend.schemas.models import CaregiverAlert, CaregiverAlertCreate

router = APIRouter(prefix="/api/v1/caregiver", tags=["Caregiver Portal"])

# Active Caregiver Alert Store
ALERTS_STORE: List[CaregiverAlert] = [
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
        message="Completed sobriety milestone! Send a supportive message.",
        created_at=datetime.utcnow().isoformat(),
        is_resolved=True
    )
]

@router.get("/alerts", response_model=List[CaregiverAlert])
def get_alerts():
    """
    Retrieves all real-time alerts for caregivers and care teams.
    """
    return ALERTS_STORE

@router.post("/alerts", response_model=CaregiverAlert)
def create_alert(payload: CaregiverAlertCreate):
    """
    Creates a new caregiver alert.
    """
    new_alert = CaregiverAlert(
        id=f"ALT-{len(ALERTS_STORE) + 101}",
        patient_name=payload.patient_name,
        severity=payload.severity,
        message=payload.message,
        created_at=datetime.utcnow().isoformat(),
        is_resolved=False
    )
    ALERTS_STORE.insert(0, new_alert)
    return new_alert

@router.post("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: str):
    """
    Marks an alert as resolved.
    """
    for alert in ALERTS_STORE:
        if alert.id == alert_id:
            alert.is_resolved = True
            return {"status": "success", "message": f"Alert {alert_id} resolved"}
    return {"status": "error", "message": "Alert not found"}
