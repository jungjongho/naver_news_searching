#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import sys
import logging

from app.api.endpoints import crawler, relevance, download, prompts
from app.websocket import endpoints as websocket_endpoints
from app.core.config import settings
from app.common.exceptions import NewsSearchException
from app.common.exception_handlers import (
    news_search_exception_handler,
    general_exception_handler
)

# 로깅 설정 - 디버깅을 위해 DEBUG 레벨로 변경
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# 결과 디렉토리 생성
os.makedirs(settings.RESULTS_PATH, exist_ok=True)

app = FastAPI(
    title="네이버 뉴스 검색 API",
    description="네이버 뉴스 API를 활용한 뉴스 검색 및 분석 서비스 (리팩토링됨)",
    version="2.0.0",
)

# 전역 예외 핸들러 등록
app.add_exception_handler(NewsSearchException, news_search_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 설정
app.include_router(crawler.router)
app.include_router(relevance.router)
app.include_router(download.router)
app.include_router(prompts.router)
app.include_router(websocket_endpoints.router)

# 결과 파일 정적 호스팅
app.mount("/results", StaticFiles(directory=settings.RESULTS_PATH), name="results")

@app.get("/")
async def root():
    return {"message": "네이버 뉴스 검색 API에 오신 것을 환영합니다!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api-key-status")
async def api_key_status():
    """네이버 API 키 설정 상태 확인"""
    client_id = settings.NAVER_CLIENT_ID
    client_secret = settings.NAVER_CLIENT_SECRET
    
    if not client_id or not client_secret:
        return {
            "status": "missing",
            "message": "네이버 API 키가 설정되어 있지 않습니다. 백엔드 .env 파일을 확인해주세요."
        }
    
    return {
        "status": "configured",
        "message": "네이버 API 키가 올바르게 설정되어 있습니다."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        timeout_keep_alive=300,  # Keep-alive 연결 타임아웃 5분
        timeout_graceful_shutdown=30  # 종료 대기 시간 30초
    )
