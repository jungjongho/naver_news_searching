#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
인증 의존성 (소셜 로그인 전용)
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.user_service import UserService
from app.utils.auth_utils import verify_token
from app.models.schemas import UserResponse

# HTTP Bearer 토큰 스키마
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    현재 로그인된 사용자 정보 조회 (소셜 로그인 전용)
    
    Args:
        credentials: HTTP Bearer 토큰
        db: 데이터베이스 세션
    
    Returns:
        현재 사용자 정보
    
    Raises:
        HTTPException: 인증 실패시
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증에 실패했습니다. 다시 로그인해주세요.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # JWT 토큰에서 이메일 추출
        email = verify_token(credentials.credentials)
        if email is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    # 사용자 정보 조회
    user_service = UserService(db)
    user = user_service.get_user_by_email(email)
    
    if user is None:
        raise credentials_exception
    
    # 비활성화된 사용자 체크
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다."
        )
    
    # 소셜 로그인 사용자만 허용
    if user.provider not in ["kakao", "naver"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="소셜 로그인 사용자만 이용할 수 있습니다."
        )
    
    return UserResponse.from_orm(user)

async def get_current_active_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """
    현재 활성 사용자 정보 조회
    
    Args:
        current_user: 현재 사용자
    
    Returns:
        활성 사용자 정보
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비활성화된 사용자입니다."
        )
    return current_user