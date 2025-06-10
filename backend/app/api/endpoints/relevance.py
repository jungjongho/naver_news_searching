#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
최적화된 관련성 분석 API 엔드포인트
"""

import logging
import uuid
from fastapi import APIRouter, HTTPException
from app.models.schemas import RelevanceRequest, RelevanceResponse
from app.services.news_analysis_service import news_analysis_service
from app.services.prompt_service import PromptService
from app.common.exceptions import NewsSearchException

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/relevance",
    tags=["relevance"],
    responses={404: {"description": "Not found"}},
)

prompt_service = PromptService()


@router.post("/analyze", response_model=RelevanceResponse)
async def analyze_relevance_optimized(request: RelevanceRequest):
    """뉴스 기사 관련성 분석 (최적화됨)"""
    logger.info(f"최적화된 관련성 분석 시작: {request.file_path}, 모델: {request.model}")
    
    # 세션 ID 설정
    session_id = request.session_id or str(uuid.uuid4())
    
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
        
        # 최적화된 분석 수행
        result_path, stats = await news_analysis_service.analyze_news_batch(
            file_path=request.file_path,
            api_key=request.api_key,
            model=request.model,
            prompt_template=prompt_template,
            session_id=session_id,
            batch_size=request.batch_size,
            use_batch_processing=request.use_batch_processing
        )
        
        return RelevanceResponse(
            success=True,
            message=f"{stats['total_items']}개 뉴스 항목의 관련성 분석이 완료되었습니다. "
                   f"관련 기사: {stats['relevant_items']}개 ({stats['relevant_percent']}%) "
                   f"(소요시간: {stats.get('processing_time', 0)}분)",
            file_path=result_path,
            stats=stats,
            session_id=session_id
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

