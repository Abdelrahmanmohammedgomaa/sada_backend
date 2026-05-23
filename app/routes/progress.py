from fastapi import APIRouter, Depends, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
import shutil
import uuid
import os

from app.database import get_db
from app.models.progress import Progress
from app.models.child import Child
from app.models.parent import Parent
from app.schemas.progress_schema import ProgressResponse
from app.core.security import get_current_parent
from app.utils.file_validation import (
    validate_extension, validate_file_size, is_valid_audio, generate_safe_filename, FileValidationException
)
from app.services.ai_hooks import analyze_audio
from app.core.logging_config import app_logger, upload_logger, error_logger
from app.utils.responses import success_response, error_response
from app.core.exceptions import APIException

router = APIRouter(
    prefix="/progress",
    tags=["Progress"]
)

UPLOAD_DIR = "uploads/audio"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/submit", response_model=dict)
async def submit_progress(
    child_id: int = Form(...),
    exercise_id: int = Form(...),
    expected_text: str = Form(...),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_parent: Parent = Depends(get_current_parent),
    request: Request = None
):
    try:
        child = db.query(Child).filter(
            Child.id == child_id,
            Child.parent_id == current_parent.id
        ).first()
        if not child:
            raise APIException(detail="Child not found", status_code=404)

        validate_extension(audio_file.filename)
        validate_file_size(audio_file)
        is_valid_audio(audio_file)

        filename = generate_safe_filename(audio_file.filename)
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            raise FileValidationException("Duplicate filename error.")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        upload_logger.info(f"Audio uploaded: {filename}")

        ai_result = analyze_audio(
            audio_path=file_path,
            expected_text=expected_text
        )

        new_progress = Progress(
            child_id=child_id,
            exercise_id=exercise_id,
            audio_path=file_path,
            score=ai_result.get("score"),
            feedback=ai_result.get("feedback")
        )

        db.add(new_progress)

        child.total_stars = (child.total_stars or 0) + ai_result.get("stars", 0)
        if child.total_stars >= (child.level or 1) * 100:
            child.level = (child.level or 1) + 1

        db.commit()
        db.refresh(new_progress)
        app_logger.info(f"Progress submitted for child: {child_id}")

        return success_response(
            message="Progress submitted successfully",
            data={
                "progress": {
                    "id": new_progress.id,
                    "audio_path": new_progress.audio_path,
                    "score": new_progress.score,
                    "feedback": new_progress.feedback,
                    "created_at": new_progress.created_at,
                },
                "ai_analysis": ai_result
            }
        )

    except (APIException, FileValidationException) as e:
        error_logger.warning(f"Progress submission error: {str(e.detail)}")
        return error_response(str(e.detail))
    except Exception as e:
        error_logger.error(f"Progress submission unexpected error: {str(e)}")
        return error_response("Failed to submit progress")

@router.get("/{child_id}", response_model=dict)
def get_child_progress(
    child_id: int,
    db: Session = Depends(get_db),
    current_parent: Parent = Depends(get_current_parent),
    request: Request = None
):
    try:
        child = db.query(Child).filter(
            Child.id == child_id,
            Child.parent_id == current_parent.id
        ).first()
        if not child:
            raise APIException(detail="Child not found", status_code=404)
        progress_records = db.query(Progress).filter(
            Progress.child_id == child_id
        ).all()
        app_logger.info(f"Progress fetched for child {child_id}")
        return success_response(
            message="Progress fetched successfully",
            data=[{
                "id": p.id,
                "audio_path": p.audio_path,
                "score": p.score,
                "feedback": getattr(p, "feedback", None),
                "created_at": p.created_at,
            } for p in progress_records]
        )
    except APIException as e:
        error_logger.warning(f"Get progress error: {str(e.detail)}")
        return error_response(str(e.detail))
    except Exception as e:
        error_logger.error(f"Get progress unexpected error: {str(e)}")
        return error_response("Failed to fetch progress")
