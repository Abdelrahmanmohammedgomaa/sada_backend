from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ProgressOut(BaseModel):
    id: int
    child_id: int
    exercise_id: int
    score: Optional[float]
    audio_path: str
    ai_feedback: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True

class ExerciseAttempt(BaseModel):
    exercise_id: int
    score: Optional[float]
    status: str
    created_at: datetime

class ProgressReport(BaseModel):
    total_exercises: int
    average_score: float
    recent_exercises: List[ExerciseAttempt]
