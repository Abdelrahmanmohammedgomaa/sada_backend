from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import os, shutil
from typing import List, Optional
from sqlalchemy import func

from app.database import get_db
from app.models.exercise import Exercise, ExerciseCategory
from app.models.progress import Progress
from app.models.child import Child
from app.routes.auth import get_current_user
from app.models.parent import Parent
from app.schemas.exercise import ExerciseOut
from app.schemas.progress import ProgressReport, ProgressOut

router = APIRouter(prefix="/exercises", tags=["Exercises"])

UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)

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

@router.post("/submit", response_model=ProgressOut)
async def submit_exercise(
    child_id: int,
    exercise_id: int,
    score: float = None,  # Would come from AI in final system
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Parent = Depends(get_current_user)
):
    child = db.query(Child).filter(
        Child.id == child_id, Child.parent_id == current_user.id
    ).first()
    if not child:
        raise HTTPException(status_code=403, detail="Child not found or not owned by parent.")

    filename = f"{child_id}_{exercise_id}_{audio_file.filename}"
    file_path = os.path.join(UPLOADS_DIR, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(audio_file.file, buffer)

    progress = Progress(
        child_id=child_id,
        exercise_id=exercise_id,
        audio_path=file_path,
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
    return progress

@router.get("/children/{child_id}/report", response_model=ProgressReport)
def get_progress_report(
    child_id: int,
    db: Session = Depends(get_db),
    current_user: Parent = Depends(get_current_user)
):
    child = db.query(Child).filter(
        Child.id == child_id, Child.parent_id == current_user.id
    ).first()
    if not child:
        raise HTTPException(status_code=403, detail="Child not found or not owned by parent.")

    progress_qs = db.query(Progress).filter(Progress.child_id == child_id).order_by(Progress.created_at.desc())

    total_exercises = progress_qs.count()
    avg_score = progress_qs.filter(Progress.score != None).with_entities(func.avg(Progress.score)).scalar() or 0

    last_5 = progress_qs.limit(5).all()
    last_5_list = []
    for record in last_5:
        status = "Passed" if record.score and record.score > 80 else "Failed"
        last_5_list.append({
            "exercise_id": record.exercise_id,
            "score": record.score,
            "status": status,
            "created_at": record.created_at
        })

    return ProgressReport(
        total_exercises=total_exercises,
        average_score=avg_score,
        recent_exercises=last_5_list
    )
