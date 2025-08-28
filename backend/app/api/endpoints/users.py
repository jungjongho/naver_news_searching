#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
사용자 API 엔드포인트 (소셜 로그인 전용)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.schemas import UserResponse
from app.services.user_service import UserService
from app.dependencies.auth import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    현재 로그인된 사용자 정보 조회
    """
    return current_user

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    사용자 ID로 사용자 정보 조회 (관리자 또는 본인만)
    """
    # 본인 정보만 조회 가능
    if current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="본인의 정보만 조회할 수 있습니다."
        )
    
    user_service = UserService(db)
    user = user_service.get_user_by_email(current_user.email)
    
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    return UserResponse.from_orm(user)