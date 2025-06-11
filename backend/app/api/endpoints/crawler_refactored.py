#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""리팩토링된 크롤러 엔드포인트"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
import logging
import os

from app.models.schemas import CrawlerRequest, CrawlerResponse, FileListResponse, DownloadLinkResponse
from app.services.naver_api_service_refactored import NaverApiService
from app.core.file_manager import file_manager
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/crawler",
    tags=["crawler"],
    responses={404: {"description": "Not found"}},
)

def get_naver_api_service() -> NaverApiService:
    return NaverApiService()

@router.post("/crawl", response_model=CrawlerResponse)
async def crawl_news(
    request: CrawlerRequest,
    background_tasks: BackgroundTasks,
    naver_api_service: NaverApiService = Depends(get_naver_api_service)
):
    """키워드 목록에 대한 뉴스 크롤링 (리팩토링됨)"""
    logger.info(f"뉴스 검색 시작: {request.keywords}")
    
    try:
        # API 키 검증
        if not settings.NAVER_CLIENT_ID or not settings.NAVER_CLIENT_SECRET:
            return CrawlerResponse(
                success=False,
                message="네이버 API 키가 설정되어 있지 않습니다. .env 파일을 확인해주세요.",
                errors={"api_key_error": "NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET이 설정되어 있지 않습니다."}
            )
        
        # 뉴스 검색 (리팩토링된 서비스 사용)
        news_items, errors = naver_api_service.search_keywords(
            request.keywords, 
            max_news_per_keyword=request.max_news_per_keyword,
            sort=request.sort,
            days=request.days,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        if not news_items:
            return CrawlerResponse(
                success=False,
                message="입력한 키워드에 대한 뉴스를 찾을 수 없습니다.",
                errors=errors
            )
        
        # 결과 저장
        file_path, download_path = naver_api_service.save_results(news_items, request.keywords)
        
        if not file_path:
            return CrawlerResponse(
                success=False,
                message="결과 저장에 실패했습니다.",
                errors={"save_error": "결과 파일을 저장할 수 없습니다."}
            )
        
        # 상대 경로로 변환
        rel_path = os.path.relpath(file_path, settings.CRAWLING_RESULTS_PATH)
        
        # 메시지 생성
        message = f"{len(news_items)}개의 뉴스 항목을 성공적으로 수집했습니다."
        if download_path:
            message += f" 결과 파일이 다운로드 폴더에 자동으로 저장되었습니다: {os.path.basename(download_path)}"
        
        return CrawlerResponse(
            success=True,
            message=message,
            file_path=rel_path,
            item_count=len(news_items),
            keywords=request.keywords,
            download_path=download_path if download_path else None,
            errors=errors if errors else None
        )
    
    except Exception as e:
        logger.error(f"뉴스 검색 오류: {str(e)}")
        return CrawlerResponse(
            success=False,
            message=f"뉴스 검색 중 오류가 발생했습니다: {str(e)}",
            errors={"search_error": str(e)}
        )

@router.get("/files", response_model=FileListResponse)
async def get_files():
    """크롤링 결과 파일 목록 조회 (최적화됨)"""
    files = file_manager.get_excel_files_optimized()
    return FileListResponse(files=files)

@router.get("/files/{file_name}/preview")
async def get_file_preview(file_name: str, max_rows: int = 5):
    """파일 내용 미리보기 (최적화됨)"""
    file_path = file_manager.find_file_path(file_name)
    
    if not file_path:
        raise HTTPException(status_code=404, detail=f"File '{file_name}' not found")
    
    from app.utils.file_utils import get_excel_preview
    preview = get_excel_preview(file_path, max_rows)
    
    if "error" in preview:
        raise HTTPException(status_code=500, detail=preview["error"])
    
    return preview

@router.get("/files/{file_name}/statistics")
async def get_file_stats(file_name: str):
    """파일 통계 정보 (최적화됨)"""
    file_path = file_manager.find_file_path(file_name)
    
    if not file_path:
        raise HTTPException(status_code=404, detail=f"File '{file_name}' not found")
    
    from app.utils.file_utils import get_excel_statistics
    stats = get_excel_statistics(file_path)
    
    if "error" in stats:
        raise HTTPException(status_code=500, detail=stats["error"])
    
    return stats

@router.get("/files/{file_name}/download-link", response_model=DownloadLinkResponse)
async def get_file_download_link(file_name: str):
    """파일 다운로드 링크 생성 (최적화됨)"""
    file_path = file_manager.find_file_path(file_name)
    
    if not file_path:
        raise HTTPException(status_code=404, detail=f"File '{file_name}' not found")
    
    download_link = f"/api/download/{file_name}"
    
    return DownloadLinkResponse(
        success=True,
        download_link=download_link,
        file_name=file_name
    )

@router.get("/search-statistics")
async def get_search_statistics(keywords: List[str]):
    """키워드별 검색 통계 정보 조회"""
    try:
        naver_api_service = NaverApiService()
        stats = naver_api_service.get_search_statistics(keywords)
        return {"success": True, "statistics": stats}
    
    except Exception as e:
        logger.error(f"검색 통계 조회 오류: {str(e)}")
        return {"success": False, "error": str(e)}
