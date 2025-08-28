#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
소셜 로그인 API 엔드포인트 (카카오, 네이버 전용)
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.schemas import (
    SocialAuthRequest, SocialAuthResponse, AuthUrlResponse, 
    SocialUserInfo, UserResponse
)
from app.services.user_service import UserService
from app.services.oauth_service import oauth_service
from app.utils.auth_utils import create_access_token
from app.core.config import settings
from app.dependencies.auth import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["social-authentication"])

@router.get("/{provider}/url", response_model=AuthUrlResponse)
async def get_social_auth_url(provider: str):
    """
    소셜 로그인 인증 URL 생성
    
    Args:
        provider: 로그인 제공자 (kakao, naver)
    
    Returns:
        소셜 로그인 인증 URL
    """
    try:
        if provider not in ["kakao", "naver"]:
            raise HTTPException(
                status_code=400,
                detail="지원하지 않는 로그인 제공자입니다. kakao 또는 naver만 지원합니다."
            )
        
        auth_data = oauth_service.generate_auth_url(provider)
        
        return AuthUrlResponse(
            auth_url=auth_data["auth_url"],
            state=auth_data["state"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"소셜 로그인 URL 생성 오류 ({provider}): {e}")
        raise HTTPException(
            status_code=500,
            detail="소셜 로그인 URL 생성 중 오류가 발생했습니다."
        )

@router.post("/{provider}/login", response_model=SocialAuthResponse)
async def social_login(
    provider: str,
    request: SocialAuthRequest,
    db: Session = Depends(get_db)
):
    """
    소셜 로그인 처리
    
    Args:
        provider: 로그인 제공자 (kakao, naver)
        request: 소셜 로그인 요청 데이터
        db: 데이터베이스 세션
    
    Returns:
        로그인 결과 및 JWT 토큰
    """
    try:
        if provider not in ["kakao", "naver"]:
            raise HTTPException(
                status_code=400,
                detail="지원하지 않는 로그인 제공자입니다. kakao 또는 naver만 지원합니다."
            )
        
        # 1. 인증 코드를 액세스 토큰으로 교환
        token_data = await oauth_service.exchange_code_for_token(provider, request.code)
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(
                status_code=400,
                detail="액세스 토큰을 받을 수 없습니다."
            )
        
        # 2. 액세스 토큰으로 사용자 정보 조회
        user_info_data = await oauth_service.get_user_info(provider, access_token)
        social_info = SocialUserInfo(**user_info_data)
        
        if not social_info.email:
            raise HTTPException(
                status_code=400,
                detail="이메일 정보를 받을 수 없습니다. 이메일 제공 동의가 필요합니다."
            )
        
        user_service = UserService(db)
        is_new_user = False
        
        # 3. 기존 소셜 계정 사용자 확인
        existing_user = user_service.get_user_by_provider_id(
            provider=social_info.provider,
            provider_id=social_info.provider_id
        )
        
        if existing_user:
            # 기존 소셜 사용자 - 정보 업데이트
            user = user_service.update_social_user_info(existing_user, social_info)
            
        else:
            # 이메일로 기존 계정 확인
            existing_email_user = user_service.get_user_by_email(social_info.email)
            
            if existing_email_user:
                # 같은 이메일로 다른 소셜 제공자 계정이 있는 경우
                raise HTTPException(
                    status_code=400,
                    detail=f"이미 {existing_email_user.provider}로 가입된 이메일입니다. {existing_email_user.provider}로 로그인해주세요."
                )
            else:
                # 신규 소셜 사용자 생성
                user = user_service.create_social_user(social_info)
                is_new_user = True
        
        # 4. JWT 토큰 생성
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        jwt_token = create_access_token(
            data={"sub": user.email}, 
            expires_delta=access_token_expires
        )
        
        # 5. 응답 생성
        user_response = UserResponse.from_orm(user)
        
        return SocialAuthResponse(
            success=True,
            access_token=jwt_token,
            token_type="bearer",
            user=user_response,
            is_new_user=is_new_user,
            message="로그인 성공" if not is_new_user else "회원가입 및 로그인 성공"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"소셜 로그인 처리 오류 ({provider}): {e}")
        raise HTTPException(
            status_code=500,
            detail="소셜 로그인 처리 중 오류가 발생했습니다."
        )

@router.delete("/account")
async def delete_account(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    계정 삭제
    
    Args:
        current_user: 현재 로그인된 사용자
        db: 데이터베이스 세션
    """
    try:
        user_service = UserService(db)
        user = user_service.get_user_by_email(current_user.email)
        
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        # 사용자 비활성화 (실제 삭제 대신)
        user_service.deactivate_user(user)
        
        return {"success": True, "message": "계정이 성공적으로 삭제되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"계정 삭제 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail="계정 삭제 중 오류가 발생했습니다."
        )
