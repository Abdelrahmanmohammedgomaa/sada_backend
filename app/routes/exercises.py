from fastapi import APIRouter, Depends, UploadFile, File, Request
from sqlalchemy.orm import Session
import os, shutil
from typing import List, Optional

from app.database import get_db
from app.models.exercise import Exercise, ExerciseCategory, ExerciseLevel
from app.models.progress import Progress
from app.models.child import Child
from app.routes.auth import get_current_user
from app.models.parent import Parent
from app.schemas.exercise import ExerciseOut

from app.utils.file_validation import (
    validate_extension, validate_file_size, is_valid_audio,
    get_secure_filename, FileValidationException
)
from app.core.exceptions import APIException
from app.services.analytics_service import (
    calculate_improvement_rate, calculate_average_score,
    get_weekly_progress, get_monthly_progress,
    get_strongest_exercise, get_weakest_exercise
)
from app.core.logging_config import app_logger, error_logger, upload_logger
from app.utils.responses import success_response, error_response

router = APIRouter(prefix="/exercises", tags=["Exercises"])

AUDIO_UPLOAD_DIR = "uploads/audio"
IMAGE_UPLOAD_DIR = "uploads/images"
os.makedirs(AUDIO_UPLOAD_DIR, exist_ok=True)
os.makedirs(IMAGE_UPLOAD_DIR, exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB

@router.post("/seed-exercises", tags=["Development"], response_model=dict)
def seed_exercises(db: Session = Depends(get_db), request: Request = None):
    try:
        sample_exercises = [
            Exercise(
                title="Say Fish",
                description="Practice saying fish clearly.",
                category=ExerciseCategory.articulation,
                target_text="fish",
                level=ExerciseLevel.beginner,
                word="fish",
                imageName="fish.png",
            ),
            Exercise(
                title="Say Cat",
                description="Practice saying cat clearly.",
                category=ExerciseCategory.articulation,
                target_text="cat",
                level=ExerciseLevel.beginner,
                word="cat",
                imageName="cat.png",
            ),
            Exercise(
                title="Say Sun",
                description="Practice saying sun clearly.",
                category=ExerciseCategory.articulation,
                target_text="sun",
                level=ExerciseLevel.intermediate,
                word="sun",
                imageName="sun.png",
            ),
            Exercise(
                title="Simple Story Retell",
                description="Repeat short sentences with smooth speech.",
                category=ExerciseCategory.fluency,
                target_text="the fish can swim",
                level=ExerciseLevel.intermediate,
                word="fish",
                imageName="story-fish.png",
            ),
            Exercise(
                title="Describe the Picture",
                description="Describe what you see in one sentence.",
                category=ExerciseCategory.fluency,
                target_text="a cat is on the mat",
                level=ExerciseLevel.advanced,
                word="cat",
                imageName="cat-mat.png",
            ),
        ]
        if db.query(Exercise).count() >= 5:
            app_logger.info("Seed attempted but already present")
            return success_response("Already seeded or enough exercises exist.")
        db.add_all(sample_exercises)
        db.commit()
        app_logger.info("Seeded 5 exercises")
        return success_response("Seeded 5 exercises.")
    except Exception as e:
        error_logger.error(f"seed_exercises error: {e}")
        return error_response("Failed to seed exercises.")

@router.post("/upload-image", response_model=dict)
async def upload_exercise_image(
    image_file: UploadFile = File(...),
    _: Parent = Depends(get_current_user),
):
    try:
        if not image_file.filename:
            raise FileValidationException("Image filename is required.")

        extension = os.path.splitext(image_file.filename)[1].lower()
        if extension not in ALLOWED_IMAGE_EXTENSIONS:
            raise FileValidationException("Unsupported image extension.")

        image_file.file.seek(0, os.SEEK_END)
        size = image_file.file.tell()
        image_file.file.seek(0)
        if size > MAX_IMAGE_SIZE:
            raise FileValidationException("Image is too large. Max size is 5MB.")

        filename = get_secure_filename(image_file.filename)
        file_path = os.path.join(IMAGE_UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            raise FileValidationException(
                "An image with this filename already exists. Please use a different filename."
            )

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image_file.file, buffer)
        upload_logger.info(f"Uploaded image file: {filename}")
        return success_response(
            "Image uploaded successfully.",
            data={
                "imageName": filename,
                "imageUrl": f"/uploads/images/{filename}",
            },
        )
    except (APIException, FileValidationException) as e:
        error_logger.warning(f"/upload-image error: {str(e.detail)}")
        return error_response(str(e.detail))
    except Exception as e:
        error_logger.error(f"upload_exercise_image error: {e}")
        return error_response("Failed to upload image.")

@router.get("/", response_model=List[ExerciseOut])
def get_exercises(
    category: Optional[ExerciseCategory] = None,
    db: Session = Depends(get_db),
    current_user: Parent = Depends(get_current_user)
):
    try:
        query = db.query(Exercise)
        if category:
            query = query.filter(Exercise.category == category)
        exercises = query.all()
        app_logger.info(f"Fetched exercises [category={category}]")
        return exercises
    except Exception as e:
        error_logger.error(f"get_exercises error: {e}")
        return []

@router.post("/submit", response_model=dict)
async def submit_exercise(
    child_id: int,
    exercise_id: int,
    score: float = None,  # Would come from AI in final system
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Parent = Depends(get_current_user),
    request: Request = None
):
    try:
        exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
        if not exercise:
            raise APIException(detail="Exercise not found", status_code=404)
        child = db.query(Child).filter(
            Child.id == child_id, Child.parent_id == current_user.id
        ).first()
        if not child:
            raise APIException(detail="Child not found or not owned by parent.", status_code=403)

        # Audio validation
        validate_extension(audio_file.filename)
        validate_file_size(audio_file)
        is_valid_audio(audio_file)

        filename = get_secure_filename(audio_file.filename)
        rel_path = f"audio/{filename}"
        file_path = os.path.join("uploads", rel_path)
        if os.path.exists(file_path):
            raise FileValidationException("Duplicate filename error.")

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        upload_logger.info(f"Uploaded file: {filename} for child {child_id}")

        progress = Progress(
            child_id=child_id,
            exercise_id=exercise_id,
            audio_path=rel_path,
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
        app_logger.info(f"Progress submitted for child {child_id}, exercise {exercise_id}")
        return success_response(
            "Progress submitted.",
            data={
                "id": progress.id,
                "child_id": progress.child_id,
                "exercise_id": progress.exercise_id,
                "score": progress.score,
                "audio_path": progress.audio_path,
                "ai_feedback": progress.ai_feedback,
                "created_at": progress.created_at,
            },
        )
    except (APIException, FileValidationException) as e:
        error_logger.warning(f"/submit file/validation error: {str(e.detail)}")
        return error_response(str(e.detail))
    except Exception as e:
        error_logger.error(f"submit_exercise error: {e}")
        return error_response("Failed to submit progress.")

@router.get("/children/{child_id}/report", response_model=dict)
def get_progress_report(
    child_id: int,
    db: Session = Depends(get_db),
    current_user: Parent = Depends(get_current_user),
    request: Request = None
):
    try:
        child = db.query(Child).filter(Child.id == child_id, Child.parent_id == current_user.id).first()
        if not child:
            raise APIException(detail="Child not found or not owned by parent.", status_code=403)
        progress_records = db.query(Progress).filter(Progress.child_id == child_id).all()
        scores = [p.score or 0 for p in progress_records]
        total_exercises = len(progress_records)
        avg_score = calculate_average_score(scores)

        # Strongest/weakest analytics
        activity_dicts = [
            {
                "exercise_id": p.exercise_id,
                "score": p.score or 0,
                "created_at": p.created_at,
            }
            for p in progress_records
        ]
        strongest = get_strongest_exercise(activity_dicts)
        weakest = get_weakest_exercise(activity_dicts)
        weekly = get_weekly_progress(activity_dicts)
        monthly = get_monthly_progress(activity_dicts)

        app_logger.info(f"Generated analytics report for child {child_id}")
        return success_response(
            "Analytics report generated.",
            data={
                "total_exercises": total_exercises,
                "average_score": avg_score,
                "strongest_exercise": strongest,
                "weakest_exercise": weakest,
                "weekly_progress": weekly,
                "monthly_progress": monthly,
            },
        )
    except APIException as e:
        error_logger.warning(f"Analytics report error: {str(e.detail)}")
        return error_response(str(e.detail))
    except Exception as e:
        error_logger.error(f"get_progress_report error: {e}")
        return error_response("Failed to generate progress report.")