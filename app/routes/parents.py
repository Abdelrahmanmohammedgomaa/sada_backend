from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.routes.auth import get_current_user
from app.models.parent import Parent
from app.models.child import Child

router = APIRouter(prefix="/parents", tags=["Parents"])

@router.get("/me")
def get_my_profile(db: Session = Depends(get_db), current_user: Parent = Depends(get_current_user)):
    children = db.query(Child).filter(Child.parent_id == current_user.id).all()
    children_data = [
        {
            "id": c.id,
            "name": c.name,
            "level": c.level,
            "total_stars": c.total_stars
        } for c in children
    ]
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "children": children_data
    }
