#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
import logging
import os

from app.models.schemas import CrawlerRequest, CrawlerResponse, FileListResponse, DownloadLinkResponse
from app.services.naver_api_service import NaverApiService
from app.utils.file_utils import get_excel_files, get_excel_preview, get_excel_statistics
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/crawler",
    tags=["crawler"],
    responses={404: {"description": "Not found"}},
)

# NaverApiService 인스턴스 생성 함수
def get_naver_api_service() -> NaverApiService:
    return NaverApiService()

@router.post("/crawl", response_model=CrawlerResponse)
async def crawl_news(
    request: CrawlerRequest,
    background_tasks: BackgroundTasks,
    naver_api_service: NaverApiService = Depends(get_naver_api_service)
):
    """
    키워드 목록에 대한 뉴스 크롤링
    """
    logger.info(f"Searching news for keywords: {request.keywords}")
    
    try:
        # API 키 검증
        if not settings.NAVER_CLIENT_ID or not settings.NAVER_CLIENT_SECRET:
            return CrawlerResponse(
                success=False,
                message="네이버 API 키가 설정되어 있지 않습니다. .env 파일을 확인해주세요.",
                errors={"api_key_error": "NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET이 설정되어 있지 않습니다."}
            )
        
        # 뉴스 검색
        news_items, errors = naver_api_service.search_keywords(
            request.keywords, 
            max_news_per_keyword=request.max_news_per_keyword,
            sort=request.sort,
            days=request.days
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
        
        # 상대 경로로 변환 (crawling 폴더 기준)
        rel_path = os.path.relpath(file_path, settings.CRAWLING_RESULTS_PATH)
        
        # 다운로드 폴더 저장 결과 추가
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
        logger.error(f"Error during news search: {str(e)}")
        return CrawlerResponse(
            success=False,
            message=f"뉴스 검색 중 오류가 발생했습니다: {str(e)}",
            errors={"search_error": str(e)}
        )

@router.get("/files", response_model=FileListResponse)
async def get_files():
    """
    크롤링 결과 파일 목록 조회
    """
    files = get_excel_files()  # 모든 폴더에서 파일 조회
    return FileListResponse(files=files)

@router.get("/files/{file_name}/preview")
async def get_file_preview(file_name: str, max_rows: int = 5):
    """
    파일 내용 미리보기
    """
    # 파일 경로 찾기
    file_path = None
    for search_path in [settings.CRAWLING_RESULTS_PATH, settings.RELEVANCE_RESULTS_PATH, settings.RESULTS_PATH]:
        potential_path = os.path.join(search_path, file_name)
        if os.path.exists(potential_path):
            file_path = potential_path
            break
    
    if not file_path:
        raise HTTPException(status_code=404, detail=f"File '{file_name}' not found")
    
    preview = get_excel_preview(file_path, max_rows)
    
    if "error" in preview:
        raise HTTPException(status_code=500, detail=preview["error"])
    
    return preview

@router.get("/files/{file_name}/statistics")
async def get_file_stats(file_name: str):
    """
    파일 통계 정보
    """
    # 파일 경로 찾기
    file_path = None
    for search_path in [settings.CRAWLING_RESULTS_PATH, settings.RELEVANCE_RESULTS_PATH, settings.RESULTS_PATH]:
        potential_path = os.path.join(search_path, file_name)
        if os.path.exists(potential_path):
            file_path = potential_path
            break
    
    if not file_path:
        raise HTTPException(status_code=404, detail=f"File '{file_name}' not found")
    
    stats = get_excel_statistics(file_path)
    
    if "error" in stats:
        raise HTTPException(status_code=500, detail=stats["error"])
    
    return stats

@router.get("/files/{file_name}/download-link", response_model=DownloadLinkResponse)
async def get_file_download_link(file_name: str):
    """
    파일 다운로드 링크 생성
    """
    # 파일 경로 찾기
    file_path = None
    for search_path in [settings.CRAWLING_RESULTS_PATH, settings.RELEVANCE_RESULTS_PATH, settings.RESULTS_PATH]:
        potential_path = os.path.join(search_path, file_name)
        if os.path.exists(potential_path):
            file_path = potential_path
            break
    
    if not file_path:
        raise HTTPException(status_code=404, detail=f"File '{file_name}' not found")
    
    download_link = f"/api/download/{file_name}"
    
    return DownloadLinkResponse(
        success=True,
        download_link=download_link,
        file_name=file_name
    )
