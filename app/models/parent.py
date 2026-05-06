from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship # لازم تكون موجودة هنا كمان
from app.database import Base

class Parent(Base):
    __tablename__ = "parents"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # الربط مع جدول الأطفال
    children = relationship("Child", back_populates="parent")