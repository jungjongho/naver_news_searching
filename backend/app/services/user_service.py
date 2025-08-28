#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
사용자 서비스 (소셜 로그인 전용)
"""

from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from app.db.models import User
from app.models.schemas import SocialUserInfo
from typing import Optional

class UserService:
    """소셜 로그인 전용 사용자 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """이메일로 사용자 찾기"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_provider_id(self, provider: str, provider_id: str) -> Optional[User]:
        """제공자와 제공자 ID로 사용자 찾기"""
        return self.db.query(User).filter(
            User.provider == provider,
            User.provider_id == provider_id
        ).first()
    
    def create_social_user(self, social_info: SocialUserInfo) -> User:
        """소셜 로그인 사용자 생성"""
        db_user = User(
            email=social_info.email,
            name=social_info.name,
            provider=social_info.provider,
            provider_id=social_info.provider_id,
            profile_image=social_info.profile_image
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def update_social_user_info(self, user: User, social_info: SocialUserInfo) -> User:
        """소셜 로그인 사용자 정보 업데이트"""
        user.name = social_info.name
        if social_info.profile_image:
            user.profile_image = social_info.profile_image
        user.updated_at = func.now()
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def increment_crawl_count(self, user: User) -> User:
        """크롤링 횟수 증가"""
        user.crawl_count += 1
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_subscription_type(self, user: User, subscription_type: str) -> User:
        """구독 타입 업데이트"""
        user.subscription_type = subscription_type
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def deactivate_user(self, user: User) -> User:
        """사용자 비활성화"""
        user.is_active = False
        self.db.commit()
        self.db.refresh(user)
        return user