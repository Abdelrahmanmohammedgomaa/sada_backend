from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.database import get_db
from app.models.parent import Parent
from app.schemas.parent import ParentCreate, ParentOut
from app.core import security

router = APIRouter(tags=['Authentication'])

@router.post("/register", response_model=ParentOut)
def register(parent_in: ParentCreate, db: Session = Depends(get_db)):
    user_exists = db.query(Parent).filter(Parent.email == parent_in.email).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # تشفير الباسورد قبل الحفظ
    hashed_pwd = security.hash_password(parent_in.password)
    new_parent = Parent(
        full_name=parent_in.full_name,
        email=parent_in.email,
        hashed_password=hashed_pwd
    )
    db.add(new_parent)
    db.commit()
    db.refresh(new_parent)
    return new_parent

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # بنجيب اليوزر بالإيميل (username في الفورم)
    user = db.query(Parent).filter(Parent.email == form_data.username).first()
    
    # التحقق
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    
    # إصدار التوكن
    token = security.create_access_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

from jose import JWTError, jwt
from app.core.security import SECRET_KEY, ALGORITHM, oauth2_scheme

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(Parent).filter(Parent.email == email).first()
    if user is None:
        raise credentials_exception
    return user