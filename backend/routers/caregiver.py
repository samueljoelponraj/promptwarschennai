from fastapi import APIRouter
from typing import List
from datetime import datetime
from backend.schemas.models import CaregiverAlert, CaregiverAlertCreate

router = APIRouter(prefix="/api/v1/caregiver", tags=["Caregiver Portal"])

# Clean Active Caregiver Alert Store (no hardcoded pre-populated alerts)
ALERTS_STORE: List[CaregiverAlert] = []

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
