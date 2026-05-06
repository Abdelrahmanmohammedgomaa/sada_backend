from pydantic import BaseModel, EmailStr

class ParentCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class ParentOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr

    class Config:
        from_attributes = True
        