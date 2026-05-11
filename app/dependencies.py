from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.child import Child
from app.routes.auth import get_current_user
from app.models.parent import Parent

# Usage: child = Depends(verify_child_access), child_id must be in path/query

def verify_child_access(child_id: int, db: Session = Depends(get_db), current_user: Parent = Depends(get_current_user)):
    child = db.query(Child).filter(Child.id == child_id, Child.parent_id == current_user.id).first()
    if not child:
        raise HTTPException(status_code=403, detail="Child not found or not owned by current parent.")
    return child
