from pydantic import BaseModel
from enum import Enum
from typing import Optional

class ExerciseCategory(str, Enum):
    articulation = "Articulation"
    fluency = "Fluency"

class ExerciseLevel(str, Enum):
    beginner = "Beginner"
    intermediate = "Intermediate"
    advanced = "Advanced"

class ExerciseOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    category: ExerciseCategory
    target_text: str
    level: ExerciseLevel
    word: str
    imageName: Optional[str] = None
    imageUrl: Optional[str] = None

    class Config:
        orm_mode = True
