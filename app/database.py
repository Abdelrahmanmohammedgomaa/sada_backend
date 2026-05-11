from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship  # السطر ده اللي ناقص!
from app.database import Base

class Child(Base):
    __tablename__ = "children"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer)
    gender = Column(String)
    
    parent_id = Column(Integer, ForeignKey("parents.id"))
    
    # الـ relationship هنا بتعتمد على الـ import اللي فوق
    parent = relationship("Parent", back_populates="children")

    
