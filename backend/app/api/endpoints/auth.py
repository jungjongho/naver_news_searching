from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.schemas import Token, UserCreate, UserResponse
from app.services.user_service import UserService
from app.utils.auth_utils import create_access_token
from app.core.config import settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    user_service = UserService(db)
    
    # 이메일 중복 확인 및 상세한 에러 메시지 제공
    if user_service.get_user_by_email(user.email):
        raise HTTPException(
            status_code=400,
            detail="이미 등록된 이메일입니다. 다른 이메일을 사용해주세요."
        )

# 추가적인 유효성 검사
    try:
        # 비밀번호 길이 검사
        if len(user.password) < 6:
            raise HTTPException(
                status_code=400,
                detail="비밀번호는 최소 6자 이상이어야 합니다."
            )
        
        # 이메일 형식 검사 (이미 Pydantic에서 하지만 추가 검증)
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, user.email):
            raise HTTPException(
                status_code=400,
                detail="유효한 이메일 주소를 입력해주세요."
            )
        
        db_user = user_service.create_user(user)
        return db_user
    
    except HTTPException:
        # HTTPException은 그대로 re-raise
        raise
    except Exception as e:
        # 기타 예상치 못한 에러
        raise HTTPException(
            status_code=500,
            detail="회원가입 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )
    
    db_user = user_service.create_user(user)
    return db_user

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user_service = UserService(db)
    user = user_service.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}