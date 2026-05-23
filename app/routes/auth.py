from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from app.database import get_db
from app.models.parent import Parent
from app.schemas.parent import ParentCreate, ParentOut
from app.core import security
from app.core.logging_config import app_logger, error_logger
from app.core.exceptions import APIException, unified_error_handler
from app.utils.responses import success_response, error_response
from app.core.security import SECRET_KEY, ALGORITHM, oauth2_scheme

router = APIRouter(tags=['Authentication'])

@router.post("/register", response_model=dict)
def register(parent_in: ParentCreate, db: Session = Depends(get_db), request: Request = None):
    try:
        user_exists = db.query(Parent).filter(Parent.email == parent_in.email).first()
        if user_exists:
            app_logger.info(f"Registration failed: {parent_in.email} already exists")
            raise APIException(detail="Email already exists", status_code=400)
        
        hashed_pwd = security.hash_password(parent_in.password)
        new_parent = Parent(
            full_name=parent_in.full_name,
            email=parent_in.email,
            hashed_password=hashed_pwd
        )
        db.add(new_parent)
        db.commit()
        db.refresh(new_parent)
        app_logger.info(f"Registered new parent: {new_parent.email}")
        return success_response("Registration successful", data={"id": new_parent.id, "email": new_parent.email})
    except APIException as e:
        error_logger.warning(f"Registration error: {str(e.detail)}")
        return error_response(str(e.detail))
    except Exception as e:
        error_logger.error(f"Unexpected registration error: {str(e)}")
        return error_response("Registration failed due to server error.")

@router.post("/login", response_model=dict)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db), request: Request = None):
    try:
        user = db.query(Parent).filter(Parent.email == form_data.username).first()
        if not user or not security.verify_password(form_data.password, user.hashed_password):
            app_logger.warning(f"Auth failed for {form_data.username}")
            raise APIException(detail="Invalid Credentials", status_code=401)
        token = security.create_access_token(data={"sub": user.email})
        app_logger.info(f"Parent login: {user.email}")
        return success_response("Login successful", data={"access_token": token, "token_type": "bearer"})
    except APIException as e:
        error_logger.warning(f"Login error: {str(e.detail)}")
        return error_response(str(e.detail))
    except Exception as e:
        error_logger.error(f"Unexpected login error: {str(e)}")
        return error_response("Login failed due to server error.")

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = APIException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        details={"auth": "Invalid Bearer token"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            error_logger.warning("Auth token missing email")
            raise credentials_exception
    except JWTError:
        error_logger.warning("Auth token decode error")
        raise credentials_exception
        
    user = db.query(Parent).filter(Parent.email == email).first()
    if user is None:
        error_logger.warning("Token for unknown parent")
        raise credentials_exception
    return user
