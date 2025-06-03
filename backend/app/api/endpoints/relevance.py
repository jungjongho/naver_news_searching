#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
import logging
import os
import pandas as pd
import datetime

from app.models.schemas import RelevanceRequest, RelevanceResponse
from app.services.relevance_service_optimized import OptimizedRelevanceService
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/relevance",
    tags=["relevance"],
    responses={404: {"description": "Not found"}},
)

@router.post("/analyze", response_model=RelevanceResponse)
async def analyze_relevance(
    request: RelevanceRequest,
    background_tasks: BackgroundTasks
):
    """
    뉴스 기사 관련성 분석 - 실제 LLM을 사용한 분석 (백그라운드 처리)
    """
    logger.info(f"Analyzing relevance for file: {request.file_path}")
    
    try:
        # 파일 경로 확인 (크롤링 결과는 crawling 폴더에 있음)
        if os.path.exists(os.path.join(settings.CRAWLING_RESULTS_PATH, request.file_path)):
            file_path = os.path.join(settings.CRAWLING_RESULTS_PATH, request.file_path)
        else:
            file_path = os.path.join(settings.RESULTS_PATH, request.file_path)
        
        if not os.path.exists(file_path):
            return RelevanceResponse(
                success=False,
                message=f"파일을 찾을 수 없습니다: {request.file_path}",
                errors={"file_error": "File not found"}
            )
        
        # OptimizedRelevanceService 인스턴스 생성 (설정값 사용)
        relevance_service = OptimizedRelevanceService(
            max_workers=settings.RELEVANCE_MAX_WORKERS, 
            batch_size=settings.RELEVANCE_BATCH_SIZE
        )
        
        # 파일 로드
        news_data = relevance_service.load_news_file(file_path)
        
        if not news_data:
            return RelevanceResponse(
                success=False,
                message="파일에서 뉴스 데이터를 읽을 수 없습니다.",
                errors={"data_error": "No news data found"}
            )
        
        # 백그라운드에서 분석 수행
        def perform_analysis():
            try:
                # 실제 LLM을 사용한 분석 수행
                analyzed_data, stats = relevance_service.analyze_news_batch(
                    news_data, 
                    request.api_key, 
                    request.model
                )
                
                # 결과 파일 생성
                file_name = os.path.basename(file_path)
                base_name, ext = os.path.splitext(file_name)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                result_file_name = f"{base_name}_analyzed_{timestamp}{ext}"
                
                # 분석 결과 저장 (relevance 폴더에 저장)
                success = relevance_service.save_analyzed_results(
                    analyzed_data, 
                    result_file_name,  # 파일명만 전달
                    use_relevance_folder=True
                )
                
                if success:
                    logger.info(f"관련성 분석 완료: {result_file_name}")
                else:
                    logger.error(f"분석 결과 저장 실패: {result_file_name}")
                    
            except Exception as e:
                logger.error(f"백그라운드 분석 중 오류: {str(e)}")
        
        # 백그라운드에서 분석 수행
        background_tasks.add_task(perform_analysis)
        
        # 즉시 응답 반환 (분석은 백그라운드에서 진행)
        return RelevanceResponse(
            success=True,
            message=f"{len(news_data)}개 뉴스 항목의 관련성 분석을 시작했습니다. 분석은 백그라운드에서 진행되며, 완료되면 결과 파일이 생성됩니다.",
            file_path=None,  # 분석 진행 중이므로 아직 파일 없음
            stats={
                "total_items": len(news_data),
                "status": "processing",
                "message": "분석 진행 중"
            }
        )
    
    except Exception as e:
        logger.error(f"Error analyzing relevance: {str(e)}")
        return RelevanceResponse(
            success=False,
            message=f"관련성 분석 중 오류가 발생했습니다: {str(e)}",
            errors={"analysis_error": str(e)}
        )


@router.post("/analyze-sync", response_model=RelevanceResponse)
async def analyze_relevance_sync(
    request: RelevanceRequest
):
    """
    뉴스 기사 관련성 분석 - 동기 방식 (즉시 결과 반환)
    """
    logger.info(f"Analyzing relevance synchronously for file: {request.file_path}")
    
    try:
        # 파일 경로 확인 (크롤링 결과는 crawling 폴더에 있음)
        if os.path.exists(os.path.join(settings.CRAWLING_RESULTS_PATH, request.file_path)):
            file_path = os.path.join(settings.CRAWLING_RESULTS_PATH, request.file_path)
        else:
            file_path = os.path.join(settings.RESULTS_PATH, request.file_path)
        
        if not os.path.exists(file_path):
            return RelevanceResponse(
                success=False,
                message=f"파일을 찾을 수 없습니다: {request.file_path}",
                errors={"file_error": "File not found"}
            )
        
        # OptimizedRelevanceService 인스턴스 생성 (설정값 사용)
        relevance_service = OptimizedRelevanceService(
            max_workers=settings.RELEVANCE_MAX_WORKERS, 
            batch_size=settings.RELEVANCE_BATCH_SIZE
        )
        
        # 파일 로드
        news_data = relevance_service.load_news_file(file_path)
        
        if not news_data:
            return RelevanceResponse(
                success=False,
                message="파일에서 뉴스 데이터를 읽을 수 없습니다.",
                errors={"data_error": "No news data found"}
            )
        
        # 실제 LLM을 사용한 분석 수행
        analyzed_data, stats = relevance_service.analyze_news_batch(
            news_data, 
            request.api_key, 
            request.model
        )
        
        # 결과 파일 생성
        file_name = os.path.basename(file_path)
        base_name, ext = os.path.splitext(file_name)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file_name = f"{base_name}_analyzed_{timestamp}{ext}"
        
        # 분석 결과 저장 (relevance 폴더에 저장)
        success = relevance_service.save_analyzed_results(
            analyzed_data, 
            result_file_name,  # 파일명만 전달
            use_relevance_folder=True
        )
        
        if not success:
            return RelevanceResponse(
                success=False,
                message="분석 결과 저장에 실패했습니다.",
                errors={"save_error": "Failed to save analysis results"}
            )
        
        return RelevanceResponse(
            success=True,
            message=f"{stats['total_items']}개 뉴스 항목의 관련성 분석이 완료되었습니다. 관련 기사: {stats['relevant_items']}개 ({stats['relevant_percent']}%)",
            file_path=result_file_name,
            stats=stats
        )
    
    except Exception as e:
        logger.error(f"Error analyzing relevance synchronously: {str(e)}")
        return RelevanceResponse(
            success=False,
            message=f"관련성 분석 중 오류가 발생했습니다: {str(e)}",
            errors={"analysis_error": str(e)}
        )


@router.get("/status/{file_name}")
async def get_analysis_status(file_name: str):
    """
    분석 상태 확인 (분석된 파일이 존재하는지 확인)
    """
    try:
        # relevance 폴더에서 분석된 파일 확인
        results_dir = settings.RELEVANCE_RESULTS_PATH
        analyzed_files = []
        
        if os.path.exists(results_dir):
            for file in os.listdir(results_dir):
                if file.startswith(file_name.replace('.csv', '').replace('.xlsx', '')) and '_analyzed_' in file:
                    file_path = os.path.join(results_dir, file)
                    file_stats = os.stat(file_path)
                    analyzed_files.append({
                        "file_name": file,
                        "created_at": datetime.datetime.fromtimestamp(file_stats.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                        "size": file_stats.st_size
                    })
        
        if analyzed_files:
            # 가장 최근 파일 반환
            latest_file = max(analyzed_files, key=lambda x: x["created_at"])
            return {
                "status": "completed",
                "message": "분석이 완료되었습니다.",
                "file": latest_file,
                "all_files": analyzed_files
            }
        else:
            return {
                "status": "processing",
                "message": "분석이 진행 중이거나 아직 시작되지 않았습니다.",
                "file": None
            }
    
    except Exception as e:
        logger.error(f"Error checking analysis status: {str(e)}")
        return {
            "status": "error",
            "message": f"상태 확인 중 오류가 발생했습니다: {str(e)}",
            "file": None
        }
