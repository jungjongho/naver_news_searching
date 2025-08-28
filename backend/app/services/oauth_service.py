#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
소셜 로그인 OAuth 서비스 (카카오, 네이버 전용)
"""

import os
import httpx
import secrets
from typing import Dict, Any
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)

class OAuthService:
    """소셜 로그인 OAuth 서비스 (카카오, 네이버 전용)"""
    
    def __init__(self):
        # 환경 변수에서 OAuth 설정 로드
        self.naver_client_id = os.getenv("NAVER_OAUTH_CLIENT_ID")
        self.naver_client_secret = os.getenv("NAVER_OAUTH_CLIENT_SECRET")
        
        self.kakao_client_id = os.getenv("KAKAO_CLIENT_ID")
        self.kakao_client_secret = os.getenv("KAKAO_CLIENT_SECRET")
        
        self.redirect_uri = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:3000/auth/callback")
        
        # 🔥 카카오, 네이버만 지원
        self.providers = {
            "naver": {
                "auth_url": "https://nid.naver.com/oauth2.0/authorize",
                "token_url": "https://nid.naver.com/oauth2.0/token",
                "user_info_url": "https://openapi.naver.com/v1/nid/me",
                "client_id": self.naver_client_id,
                "client_secret": self.naver_client_secret,
                "scope": "name email profile_image"
            },
            "kakao": {
                "auth_url": "https://kauth.kakao.com/oauth/authorize",
                "token_url": "https://kauth.kakao.com/oauth/token",
                "user_info_url": "https://kapi.kakao.com/v2/user/me",
                "client_id": self.kakao_client_id,
                "client_secret": self.kakao_client_secret,
                "scope": "profile_nickname profile_image account_email"
            }
        }
    
    def generate_auth_url(self, provider: str) -> Dict[str, str]:
        """
        소셜 로그인 인증 URL 생성
        
        Args:
            provider: 로그인 제공자 (kakao, naver)
        
        Returns:
            인증 URL과 state 딕셔너리
        """
        if provider not in ["kakao", "naver"]:
            raise ValueError(f"지원하지 않는 제공자: {provider}. kakao 또는 naver만 지원합니다.")
        
        config = self.providers[provider]
        state = secrets.token_urlsafe(32)  # CSRF 방지용 state
        
        # OAuth 인증 파라미터
        params = {
            "client_id": config["client_id"],
            "redirect_uri": self.redirect_uri,
            "scope": config["scope"],
            "response_type": "code",
            "state": state
        }
        
        auth_url = f"{config['auth_url']}?{urlencode(params)}"
        
        return {
            "auth_url": auth_url,
            "state": state
        }
    
    async def exchange_code_for_token(self, provider: str, code: str) -> Dict[str, Any]:
        """
        인증 코드를 액세스 토큰으로 교환
        
        Args:
            provider: 로그인 제공자 (kakao, naver)
            code: OAuth 인증 코드
        
        Returns:
            토큰 정보 딕셔너리
        """
        if provider not in ["kakao", "naver"]:
            raise ValueError(f"지원하지 않는 제공자: {provider}")
        
        config = self.providers[provider]
        
        # 토큰 요청 데이터
        data = {
            "grant_type": "authorization_code",
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "redirect_uri": self.redirect_uri,
            "code": code
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                config["token_url"],
                data=data,
                headers={"Accept": "application/json"}
            )
            
            if response.status_code != 200:
                logger.error(f"{provider} 토큰 교환 실패: {response.text}")
                raise Exception(f"토큰 교환 실패: {response.status_code}")
            
            return response.json()
    
    async def get_user_info(self, provider: str, access_token: str) -> Dict[str, Any]:
        """
        액세스 토큰으로 사용자 정보 조회
        
        Args:
            provider: 로그인 제공자 (kakao, naver)
            access_token: 액세스 토큰
        
        Returns:
            사용자 정보 딕셔너리
        """
        if provider not in ["kakao", "naver"]:
            raise ValueError(f"지원하지 않는 제공자: {provider}")
        
        config = self.providers[provider]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                config["user_info_url"],
                headers=headers
            )
            
            if response.status_code != 200:
                logger.error(f"{provider} 사용자 정보 조회 실패: {response.text}")
                raise Exception(f"사용자 정보 조회 실패: {response.status_code}")
            
            user_data = response.json()
            
            # 제공자별 사용자 정보 정규화
            return self._normalize_user_info(provider, user_data)
    
    def _normalize_user_info(self, provider: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        제공자별 사용자 정보를 공통 형식으로 정규화
        
        Args:
            provider: 로그인 제공자 (kakao, naver)
            user_data: 원본 사용자 데이터
        
        Returns:
            정규화된 사용자 정보
        """
        if provider == "naver":
            response_data = user_data.get("response", {})
            return {
                "provider": "naver",
                "provider_id": response_data.get("id"),
                "email": response_data.get("email"),
                "name": response_data.get("name"),
                "profile_image": response_data.get("profile_image")
            }
        
        elif provider == "kakao":
            kakao_account = user_data.get("kakao_account", {})
            profile = kakao_account.get("profile", {})
            
            return {
                "provider": "kakao",
                "provider_id": str(user_data.get("id")),
                "email": kakao_account.get("email"),
                "name": profile.get("nickname"),
                "profile_image": profile.get("profile_image_url")
            }
        
        else:
            raise ValueError(f"지원하지 않는 제공자: {provider}")

# 전역 OAuth 서비스 인스턴스
oauth_service = OAuthService()
