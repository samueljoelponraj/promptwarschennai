from fastapi import APIRouter
from datetime import datetime, date
from backend.schemas.models import RecoveryStreak, DailyCheckInRequest, StreakUpdate

router = APIRouter(prefix="/api/v1/recovery", tags=["Recovery Tracking"])

# In-memory dynamic store
STATE_STORE = {
    "user_123": {
        "sober_start_date": "2026-06-13",
        "checkins": [
            {"mood": 8, "notes": "Feeling focused and hopeful", "timestamp": "2026-07-24"},
            {"mood": 9, "notes": "Attended support group", "timestamp": "2026-07-25"}
        ],
        "triggers_count": 2
    }
}

@router.get("/streak/{user_id}", response_model=RecoveryStreak)
def get_streak(user_id: str):
    """
    Returns dynamically calculated sobriety streak & metrics for user.
    """
    user_data = STATE_STORE.get(user_id, {
        "sober_start_date": "2026-06-13",
        "checkins": [],
        "triggers_count": 0
    })
    
    start = datetime.strptime(user_data["sober_start_date"], "%Y-%m-%d").date()
    days_sober = (date.today() - start).days
    if days_sober < 0:
        days_sober = 0
        
    checkins = user_data.get("checkins", [])
    avg_mood = sum([c.get("mood", 7) for c in checkins]) / len(checkins) if checkins else 8.0

    return RecoveryStreak(
        user_id=user_id,
        days_sober=days_sober,
        current_streak_start=user_data["sober_start_date"],
        triggers_log_count=user_data.get("triggers_count", 0),
        mood_score_avg=round(avg_mood, 1),
        checkins_count=len(checkins)
    )

@router.post("/checkin")
def record_checkin(request: DailyCheckInRequest):
    """
    Records a real daily check-in with mood rating and optional notes.
    """
    if request.user_id not in STATE_STORE:
        STATE_STORE[request.user_id] = {
            "sober_start_date": date.today().isoformat(),
            "checkins": [],
            "triggers_count": 0
        }
        
    entry = {
        "mood": request.mood_score,
        "notes": request.notes,
        "timestamp": date.today().isoformat()
    }
    STATE_STORE[request.user_id]["checkins"].append(entry)
    if request.trigger_logged:
        STATE_STORE[request.user_id]["triggers_count"] += 1
        
    return {
        "status": "success",
        "message": "Daily check-in recorded successfully!",
        "total_checkins": len(STATE_STORE[request.user_id]["checkins"])
    }

@router.post("/update-start-date")
def update_start_date(update: StreakUpdate):
    """
    Updates the sober start date for dynamic streak calculation.
    """
    if update.user_id not in STATE_STORE:
        STATE_STORE[update.user_id] = {"checkins": [], "triggers_count": 0}
        
    STATE_STORE[update.user_id]["sober_start_date"] = update.sober_start_date
    return {"status": "success", "sober_start_date": update.sober_start_date}
