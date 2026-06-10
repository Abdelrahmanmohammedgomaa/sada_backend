from enum import Enum

from sqlalchemy import Column, Enum as SqlEnum, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class ExerciseCategory(str, Enum):
    articulation = "Articulation"
    fluency = "Fluency"


class ExerciseLevel(str, Enum):
    beginner = "Beginner"
    intermediate = "Intermediate"
    advanced = "Advanced"


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(SqlEnum(ExerciseCategory, native_enum=False), nullable=False)
    target_text = Column(String, nullable=False)
    level = Column(SqlEnum(ExerciseLevel, native_enum=False), nullable=False)
    word = Column(String, nullable=False)
    imageName = Column(String, nullable=True)

    progress_records = relationship("Progress", back_populates="exercise")

    @property
    def imageUrl(self):
        if not self.imageName:
            return None
        return f"/uploads/images/{self.imageName}"
