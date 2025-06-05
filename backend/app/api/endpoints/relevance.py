#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
개선된 관련성 분석 API 엔드포인트
"""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.schemas import RelevanceRequest, RelevanceResponse
from app.services.news_analysis_service import news_analysis_service
from app.services.prompt_service import PromptService
from app.common.progress import progress_tracker
from app.common.responses import ResponseFormatter, create_progress_response
from app.common.exceptions import NewsSearchException

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/relevance",
    tags=["relevance"],
    responses={404: {"description": "Not found"}},
)

prompt_service = PromptService()


@router.post("/analyze-sync", response_model=RelevanceResponse)
async def analyze_relevance_sync(request: RelevanceRequest):
    """뉴스 기사 관련성 분석 - 동기 방식"""
    logger.info(f"관련성 분석 시작: {request.file_path}, 모델: {request.model}")
    
    try:
        # 프롬프트 템플릿 가져오기
        prompt_template = None
        if request.prompt_id:
            prompt_template = prompt_service.get_prompt_by_id(request.prompt_id)
            if not prompt_template:
                raise HTTPException(
                    status_code=404,
                    detail=f"프롬프트를 찾을 수 없습니다: {request.prompt_id}"
                )
        else:
            prompt_template = prompt_service.get_active_prompt()
        
        # 분석 수행
        result_path, stats = news_analysis_service.analyze_news_batch(
            file_path=request.file_path,
            api_key=request.api_key,
            model=request.model,
            prompt_template=prompt_template,
            session_id="current_analysis"
        )
        
        return RelevanceResponse(
            success=True,
            message=f"{stats['total_items']}개 뉴스 항목의 관련성 분석이 완료되었습니다. "
                   f"관련 기사: {stats['relevant_items']}개 ({stats['relevant_percent']}%)",
            file_path=result_path,
            stats=stats,
            session_id="current_analysis"
        )
        
    except NewsSearchException as e:
        logger.error(f"관련성 분석 실패: {e.message}")
        return RelevanceResponse(
            success=False,
            message=e.message,
            errors={"error_code": e.error_code}
        )
    except Exception as e:
        logger.error(f"예기치 못한 오류: {str(e)}")
        return RelevanceResponse(
            success=False,
            message=f"관련성 분석 중 오류가 발생했습니다: {str(e)}",
            errors={"analysis_error": str(e)}
        )


@router.post("/analyze", response_model=RelevanceResponse)
async def analyze_relevance_background(
    request: RelevanceRequest,
    background_tasks: BackgroundTasks
):
    """뉴스 기사 관련성 분석 - 백그라운드 처리"""
    logger.info(f"백그라운드 관련성 분석 시작: {request.file_path}")
    
    try:
        # 프롬프트 템플릿 가져오기
        prompt_template = None
        if request.prompt_id:
            prompt_template = prompt_service.get_prompt_by_id(request.prompt_id)
        else:
            prompt_template = prompt_service.get_active_prompt()
        
        # 파일 기본 검증 (데이터 로드)
        from app.services.file_service import file_service
        news_data = file_service.load_news_data(request.file_path)
        
        # 백그라운드 작업 추가
        def perform_background_analysis():
            try:
                news_analysis_service.analyze_news_batch(
                    file_path=request.file_path,
                    api_key=request.api_key,
                    model=request.model,
                    prompt_template=prompt_template,
                    session_id="background_analysis"
                )
                logger.info("백그라운드 분석 완료")
            except Exception as e:
                logger.error(f"백그라운드 분석 실패: {str(e)}")
        
        background_tasks.add_task(perform_background_analysis)
        
        return RelevanceResponse(
            success=True,
            message=f"{len(news_data)}개 뉴스 항목의 관련성 분석을 시작했습니다. "
                   f"백그라운드에서 진행되며, 완료되면 결과 파일이 생성됩니다.",
            file_path=None,
            stats={
                "total_items": len(news_data),
                "status": "processing",
                "message": "분석 진행 중"
            },
            session_id="background_analysis"
        )
        
    except NewsSearchException as e:
        logger.error(f"백그라운드 분석 시작 실패: {e.message}")
        return RelevanceResponse(
            success=False,
            message=e.message,
            errors={"error_code": e.error_code}
        )
    except Exception as e:
        logger.error(f"예기치 못한 오류: {str(e)}")
        return RelevanceResponse(
            success=False,
            message=f"분석 시작 중 오류가 발생했습니다: {str(e)}",
            errors={"startup_error": str(e)}
        )


@router.get("/progress/{session_id}")
async def get_analysis_progress(session_id: str):
    """분석 진행 상황 조회"""
    try:
        progress_data = progress_tracker.get_progress(session_id)
        
        return ResponseFormatter.success(
            message="진행 상황 조회 성공",
            data={"progress": progress_data}
        )
        
    except Exception as e:
        logger.error(f"진행 상황 조회 실패: {str(e)}")
        return ResponseFormatter.error(
            message=f"진행 상황 조회 중 오류가 발생했습니다: {str(e)}",
            details={"progress": create_progress_response(0, 0, "오류 발생")}
        )


@router.get("/status/{file_name}")
async def get_analysis_status(file_name: str):
    """분석 상태 확인"""
    try:
        from app.services.file_service import file_service
        
        # relevance 폴더에서 분석된 파일 확인
        analyzed_files = file_service.get_file_list("relevance")
        
        # 해당 파일명으로 시작하는 분석된 파일 찾기
        base_name = file_name.replace('.csv', '').replace('.xlsx', '')
        matching_files = [
            f for f in analyzed_files 
            if f["name"].startswith(base_name) and "_analyzed_" in f["name"]
        ]
        
        if matching_files:
            latest_file = matching_files[0]  # 이미 최신순으로 정렬됨
            return ResponseFormatter.success(
                message="분석이 완료되었습니다.",
                data={
                    "status": "completed",
                    "file": latest_file,
                    "all_files": matching_files
                }
            )
        else:
            return ResponseFormatter.success(
                message="분석이 진행 중이거나 아직 시작되지 않았습니다.",
                data={
                    "status": "processing",
                    "file": None
                }
            )
            
    except Exception as e:
        logger.error(f"분석 상태 확인 실패: {str(e)}")
        return ResponseFormatter.error(
            message=f"상태 확인 중 오류가 발생했습니다: {str(e)}",
            details={"status": "error"}
        )


@router.post("/initialize-progress")
async def initialize_progress(request: RelevanceRequest):
    """분석 시작 전 진행 상황 초기화"""
    try:
        from app.services.file_service import file_service
        
        # 파일 로드하여 전체 항목 수 확인
        news_data = file_service.load_news_data(request.file_path)
        
        session_id = "current_analysis"
        
        # 진행 상황 초기화
        progress_tracker.update_progress(
            session_id, 0, len(news_data), '분석 준비 완료', '',
            {'total_items': len(news_data), 'relevant_items': 0, 'irrelevant_items': 0, 'errors': 0, 'processing_rate': 0}
        )
        
        return ResponseFormatter.success(
            message="진행 상황 초기화 완료",
            data={
                "session_id": session_id,
                "total_items": len(news_data)
            }
        )
        
    except NewsSearchException as e:
        return ResponseFormatter.from_exception(e)
    except Exception as e:
        logger.error(f"진행 상황 초기화 실패: {str(e)}")
        return ResponseFormatter.error(
            message=f"진행 상황 초기화 중 오류가 발생했습니다: {str(e)}"
        )
