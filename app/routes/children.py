from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.child import Child
from app.models.parent import Parent
from app.schemas.child_schema import ChildCreate, ChildResponse
from app.core.security import get_current_parent
from app.services.analytics_service import AnalyticsService
from app.core.logging_config import app_logger, error_logger
from app.utils.responses import success_response, error_response
from app.core.exceptions import APIException

router = APIRouter(
    prefix="/children",
    tags=["Children"]
)

@router.post("/", response_model=dict)
def create_child(
    child_data: ChildCreate,
    db: Session = Depends(get_db),
    current_parent: Parent = Depends(get_current_parent),
    request: Request = None
):
    try:
        new_child = Child(
            name=child_data.child_name,
            age=child_data.age,
            gender=child_data.gender,
            parent_id=current_parent.id,
            total_stars=0,
            level=1
        )
        db.add(new_child)
        db.commit()
        db.refresh(new_child)
        app_logger.info(f"Child created: {new_child.id}")
        return success_response(
            message="Child created successfully",
            data={
                "id": new_child.id,
                "name": new_child.name,
                "age": new_child.age,
                "gender": new_child.gender,
                "total_stars": new_child.total_stars,
                "level": new_child.level,
            }
        )
    except Exception as e:
        error_logger.error(f"Create child error: {str(e)}")
        return error_response("Failed to create child")

@router.get("/", response_model=dict)
def get_children(
    db: Session = Depends(get_db),
    current_parent: Parent = Depends(get_current_parent),
    request: Request = None
):
    try:
        children = db.query(Child).filter(
            Child.parent_id == current_parent.id
        ).all()
        app_logger.info(f"Fetched children for parent {current_parent.id}")
        return success_response(
            message="Children fetched successfully",
            data=[
                {
                    "id": c.id,
                    "name": c.name,
                    "age": c.age,
                    "gender": c.gender,
                    "total_stars": c.total_stars,
                    "level": c.level,
                }
                for c in children
            ]
        )
    except Exception as e:
        error_logger.error(f"Get children error: {str(e)}")
        return error_response("Failed to fetch children")

@router.get("/{child_id}", response_model=dict)
def get_child(
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
            return error_response("Child not found")
        return success_response(
            message="Child fetched successfully",
            data={
                "id": child.id,
                "name": child.name,
                "age": child.age,
                "gender": child.gender,
                "total_stars": child.total_stars,
                "level": child.level,
            }
        )
    except Exception as e:
        error_logger.error(f"Get child error: {str(e)}")
        return error_response("Failed to fetch child")

@router.delete("/{child_id}", response_model=dict)
def delete_child(
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
            return error_response("Child not found")
        db.delete(child)
        db.commit()
        app_logger.info(f"Child deleted: {child_id}")
        return success_response(
            message="Child deleted successfully",
            data=None
        )
    except Exception as e:
        error_logger.error(f"Delete child error: {str(e)}")
        return error_response("Failed to delete child")

@router.get("/{child_id}/analytics", response_model=dict)
def get_child_analytics(
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
            return error_response("Child not found")
        analytics = AnalyticsService.get_child_analytics(
            db=db,
            child_id=child_id
        )
        app_logger.info(f"Analytics generated for child: {child_id}")
        return success_response(
            message="Analytics fetched successfully",
            data=analytics
        )
    except Exception as e:
        error_logger.error(f"Analytics error: {str(e)}")
        return error_response("Failed to fetch analytics")
