#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import sys
import logging
import gc
import asyncio
from contextlib import asynccontextmanager

from app.api.endpoints import crawler, relevance, download, prompts, deduplication
from app.websocket import endpoints as websocket_endpoints
from app.core.config import settings
from app.common.exceptions import NewsSearchException
from app.common.exception_handlers import (
    news_search_exception_handler,
    general_exception_handler
)

# 로깅 설정 - 메모리 사용량 모니터링 포함
logging.basicConfig(
    level=logging.INFO,  # DEBUG에서 INFO로 변경하여 로그 스팸 방지
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# 메모리 모니터링 함수
def log_memory_usage():
    """메모리 사용량 로깅"""
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        logger.info(f"💾 메모리 사용량: {memory_mb:.1f} MB")
        
        # 메모리 사용량이 500MB 초과시 가비지 컬렉션 강제 실행
        if memory_mb > 500:
            gc.collect()
            logger.warning(f"🧹 가비지 컬렉션 실행됨 (메모리 사용량: {memory_mb:.1f} MB)")
    except ImportError:
        # psutil이 없으면 건너뛰기
        pass

# 주기적 메모리 정리 작업
async def periodic_cleanup():
    """주기적으로 메모리 정리"""
    while True:
        await asyncio.sleep(300)  # 5분마다
        log_memory_usage()
        gc.collect()  # 가비지 컬렉션 실행

# 애플리케이션 라이프사이클 관리
@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 시 실행되는 코드"""
    # 시작 시
    logger.info("🚀 애플리케이션 시작")
    log_memory_usage()
    
    # 백그라운드 작업 시작
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    try:
        yield
    finally:
        # 종료 시
        logger.info("🛑 애플리케이션 종료 중...")
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
        gc.collect()  # 최종 정리
        logger.info("✅ 애플리케이션 종료 완료")

# 결과 디렉토리 생성
os.makedirs(settings.RESULTS_PATH, exist_ok=True)

app = FastAPI(
    title="네이버 뉴스 검색 API",
    description="네이버 뉴스 API를 활용한 뉴스 검색 및 분석 서비스 (최적화됨)",
    version="2.1.0",
    lifespan=lifespan  # 라이프사이클 관리 추가
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
app.include_router(deduplication.router)
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
    """헬스 체크 - 메모리 정보 포함"""
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        return {
            "status": "healthy",
            "memory_usage_mb": round(memory_mb, 1),
            "memory_percent": round(process.memory_percent(), 1)
        }
    except ImportError:
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
    # uvicorn 설정 최적화
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        
        # 연결 관리 최적화
        timeout_keep_alive=600,  # Keep-alive 10분으로 증가
        timeout_graceful_shutdown=60,  # 종료 대기 시간 1분으로 증가
        
        # 동시 연결 수 제한
        limit_concurrency=100,  # 최대 100개 동시 연결
        limit_max_requests=1000,  # 연결당 최대 1000개 요청
        
        # 백로그 설정
        backlog=2048,
        
        # 로그 레벨
        log_level="info",
        
        # 액세스 로그 비활성화 (성능 향상)
        access_log=False,
        
        # 워커 프로세스 설정 (개발 환경에서는 1개)
        workers=1,
    )
