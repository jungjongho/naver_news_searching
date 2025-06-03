#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 사용자 홈 디렉토리 가져오기
HOME_DIR = Path.home()

class Settings:
    # 프로젝트 기본 정보
    PROJECT_NAME: str = "네이버 뉴스 검색 API"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "네이버 뉴스 API를 사용한 뉴스 검색 및 분석 서비스"
    
    # API 키
    NAVER_CLIENT_ID: str = os.getenv("NAVER_CLIENT_ID", "")
    NAVER_CLIENT_SECRET: str = os.getenv("NAVER_CLIENT_SECRET", "")
    
    # 결과 저장 경로
    BASE_DIR: Path = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))).resolve()
    RESULTS_PATH: str = os.path.join(BASE_DIR, "results")
    
    # 크롤링 결과 저장 경로
    CRAWLING_RESULTS_PATH: str = os.path.join(BASE_DIR, "results", "crawling")
    
    # 연관성 분석 결과 저장 경로
    RELEVANCE_RESULTS_PATH: str = os.path.join(BASE_DIR, "results", "relevance")
    
    # 사용자 다운로드 폴더 경로
    USER_DOWNLOAD_PATH: str = os.path.join(HOME_DIR, "Downloads")
    
    # 자동 다운로드 폴더 복사 여부
    AUTO_COPY_TO_DOWNLOADS: bool = True
    
    # CORS 설정
    CORS_ORIGINS: list = ["*"]  # 개발 환경에서는 모든 오리진 허용
    
    # 기본 API 설정
    DEFAULT_NEWS_COUNT: int = 100
    DEFAULT_NEWS_SORT: str = "date"  # date(최신순) 또는 sim(정확도순)
    DEFAULT_NEWS_DAYS: int = 30  # 최근 30일 뉴스
    
    # 관련성 분석 최적화 설정
    RELEVANCE_MAX_WORKERS: int = int(os.getenv("RELEVANCE_MAX_WORKERS", "3"))
    RELEVANCE_BATCH_SIZE: int = int(os.getenv("RELEVANCE_BATCH_SIZE", "5"))
    RELEVANCE_TIMEOUT: float = float(os.getenv("RELEVANCE_TIMEOUT", "15.0"))
    RELEVANCE_MAX_RETRIES: int = int(os.getenv("RELEVANCE_MAX_RETRIES", "2"))

settings = Settings()
