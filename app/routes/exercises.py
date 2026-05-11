from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import os, shutil, uuid
from typing import List, Optional
from sqlalchemy import func

from app.database import get_db
from app.models.exercise import Exercise, ExerciseCategory
from app.models.progress import Progress
from app.models.child import Child
from app.routes.auth import get_current_user
from app.models.parent import Parent
from app.schemas.exercise import ExerciseOut

router = APIRouter(prefix="/exercises", tags=["Exercises"])

AUDIO_UPLOAD_DIR = "uploads/audio"
os.makedirs(AUDIO_UPLOAD_DIR, exist_ok=True)

@router.get("/", response_model=List[ExerciseOut])
def get_exercises(
    category: Optional[ExerciseCategory] = None,
    db: Session = Depends(get_db),
    current_user: Parent = Depends(get_current_user)
):
    query = db.query(Exercise)
    if category:
        query = query.filter(Exercise.category == category)
    return query.all()

@router.post("/submit")
async def submit_exercise(
    child_id: int,
    exercise_id: int,
    score: float = None,  # Would come from AI in final system
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Parent = Depends(get_current_user)
):
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    child = db.query(Child).filter(
        Child.id == child_id, Child.parent_id == current_user.id
    ).first()
    if not child:
        raise HTTPException(status_code=403, detail="Child not found or not owned by parent.")

    # Unique audio file logic
    filename = f"{uuid.uuid4()}_{child_id}_{audio_file.filename}"
    rel_path = f"audio/{filename}"
    file_path = os.path.join("uploads", rel_path)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(audio_file.file, buffer)

    progress = Progress(
        child_id=child_id,
        exercise_id=exercise_id,
        audio_path=rel_path,  # store as relative
        score=score,
        ai_feedback=None
    )
    db.add(progress)

    # Gamification logic
    if score is not None and score > 80:
        child.total_stars = (child.total_stars or 0) + 10
        if child.total_stars > 100:
            child.level = (child.level or 1) + 1

    db.commit()
    db.refresh(progress)
    return {
        "id": progress.id,
        "child_id": progress.child_id,
        "exercise_id": progress.exercise_id,
        "score": progress.score,
        "audio_path": progress.audio_path,
        "ai_feedback": progress.ai_feedback,
        "created_at": progress.created_at
    }

@router.get("/children/{child_id}/report")
def get_progress_report(
    child_id: int,
    db: Session = Depends(get_db),
    current_user: Parent = Depends(get_current_user)
):
    child = db.query(Child).filter(Child.id == child_id, Child.parent_id == current_user.id).first()
    if not child:
        raise HTTPException(status_code=403, detail="Child not found or not owned by parent.")

    total_exercises = db.query(Progress).filter(Progress.child_id == child_id).count()
    avg_score = db.query(func.avg(Progress.score)).filter(Progress.child_id == child_id).scalar() or 0.0

    # Category performance
    cat_perf = db.query(Exercise.category, func.avg(Progress.score)).\
        join(Exercise, Progress.exercise_id == Exercise.id).\
        filter(Progress.child_id == child_id).\
        group_by(Exercise.category).all()
    category_performance = {cat.value: round(avg, 2) if avg else 0 for cat, avg in cat_perf}

    # Recent activity (last 10)
    ra = db.query(Progress, Exercise).\
        join(Exercise, Progress.exercise_id == Exercise.id).\
        filter(Progress.child_id == child_id).\
        order_by(Progress.created_at.desc()).limit(10).all()
    recent_activity = [
        {
            "exercise_title": e.title,
            "score": p.score,
            "date": p.created_at
        } for p, e in ra
    ]

    return {
        "summary": {
            "total_exercises": total_exercises,
            "total_stars": child.total_stars,
            "current_level": child.level,
            "average_score": round(avg_score, 2)
        },
        "category_performance": category_performance,
        "recent_activity": recent_activity
    }
