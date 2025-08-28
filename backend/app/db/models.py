from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    
    # 🔥 소셜 로그인 전용 필드들 (비밀번호 관련 필드 완전 제거)
    provider = Column(String(50), nullable=False)  # kakao, naver만 허용
    provider_id = Column(String(255), nullable=False, unique=True)  # 소셜 로그인 고유 ID
    profile_image = Column(String(500), nullable=True)  # 프로필 이미지 URL
    
    # 기본 필드들
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 사용량 추적을 위한 필드들
    crawl_count = Column(Integer, default=0)
    api_calls_today = Column(Integer, default=0)
    subscription_type = Column(String(50), default="free")  # free, basic, premium
    
    # 🔥 소셜 로그인 전용이므로 이메일은 항상 인증됨
    # is_email_verified, hashed_password, is_superuser 등 제거