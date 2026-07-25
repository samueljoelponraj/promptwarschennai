from fastapi import APIRouter
from backend.schemas.models import RecoveryStreak

router = APIRouter(prefix="/api/v1/recovery", tags=["Recovery Tracking"])

@router.get("/streak/{user_id}", response_model=RecoveryStreak)
def get_streak(user_id: str):
    """
    Returns sobriety streak and recovery metrics for the user.
    """
    return RecoveryStreak(
        user_id=user_id,
        days_sober=42,
        current_streak_start="2026-06-13",
        triggers_log_count=5,
        mood_score_avg=8.4
    )
