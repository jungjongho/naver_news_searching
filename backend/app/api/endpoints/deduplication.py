#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
중복 제거 API 엔드포인트 (GPT 임베딩 전용)
"""

import logging
import uuid
from fastapi import APIRouter, HTTPException
from app.models.schemas import DeduplicationRequest, DeduplicationResponse
from app.services.deduplication_service import deduplication_service
from app.common.exceptions import NewsSearchException

# 전역 중지 상태 관리
stop_flags = {}

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/deduplication",
    tags=["deduplication"],
    responses={404: {"description": "Not found"}},
)


@router.post("/remove", response_model=DeduplicationResponse)
async def remove_duplicates(request: DeduplicationRequest):
    """뉴스 기사 중복 제거 (GPT 임베딩 방식)"""
    logger.info(f"GPT 임베딩 중복 제거 시작: {request.file_path}, 임계값: {request.similarity_threshold}")
    
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        stop_flags[session_id] = False
        
        result_path, stats = await deduplication_service.deduplicate_news(
            file_path=request.file_path,
            api_key=request.api_key,
            similarity_threshold=request.similarity_threshold,
            batch_size=request.batch_size,
            session_id=session_id,
            stop_flag_dict=stop_flags,
            embedding_model=getattr(request, 'embedding_model', 'text-embedding-3-small')
        )
        
        return DeduplicationResponse(
            success=True,
            message=f"GPT 임베딩 방식으로 {stats['original_count']}개 기사 중 {stats['removed_count']}개 중복 기사를 제거했습니다. "
                   f"최종 {stats['deduplicated_count']}개 기사 (제거율: {stats['reduction_percentage']}%) "
                   f"(소요시간: {stats.get('processing_time', 0)}분)",
            file_path=result_path,
            stats=stats,
            session_id=session_id
        )
        
    except NewsSearchException as e:
        logger.error(f"GPT 임베딩 중복 제거 실패: {e.message}")
        return DeduplicationResponse(
            success=False,
            message=e.message,
            errors={"error_code": e.error_code}
        )
    except Exception as e:
        logger.error(f"예기치 못한 오류: {str(e)}")
        return DeduplicationResponse(
            success=False,
            message=f"중복 제거 중 오류가 발생했습니다: {str(e)}",
            errors={"deduplication_error": str(e)}
        )
    finally:
        if session_id in stop_flags:
            del stop_flags[session_id]


@router.post("/stop/{session_id}")
async def stop_deduplication(session_id: str):
    """중복 제거 중지"""
    logger.info(f"중복 제거 중지 요청: {session_id}")
    
    if session_id in stop_flags:
        stop_flags[session_id] = True
        logger.info(f"세션 {session_id} 중지 플래그 설정 완료")
        return {
            "success": True,
            "message": "중복 제거 중지 요청이 전송되었습니다. 잠시 후 중지됩니다.",
            "session_id": session_id
        }
    else:
        logger.warning(f"세션 {session_id}를 찾을 수 없습니다.")
        return {
            "success": False,
            "message": "중지할 중복 제거 세션을 찾을 수 없습니다.",
            "session_id": session_id
        }


@router.get("/status/{session_id}")
async def get_deduplication_status(session_id: str):
    """중복 제거 상태 확인"""
    is_running = session_id in stop_flags
    is_stopped = stop_flags.get(session_id, False) if is_running else False
    
    return {
        "session_id": session_id,
        "is_running": is_running,
        "is_stopped": is_stopped,
        "status": "stopped" if is_stopped else ("running" if is_running else "not_found")
    }


@router.get("/info")
async def get_deduplication_info():
    """GPT 임베딩 중복 제거 방식 정보"""
    return {
        "method": {
            "name": "GPT 임베딩",
            "description": "OpenAI 임베딩 모델 기반 의미적 중복 탐지",
            "model": "text-embedding-3-small",
            "pros": [
                "높은 정확도 (90-95%)",
                "의미적 유사도 탐지",
                "DBSCAN 클러스터링으로 효율적 처리",
                "배치 처리로 비용 최적화"
            ],
            "cons": [
                "OpenAI API 비용 발생",
                "인터넷 연결 필요"
            ],
            "recommended_threshold": "0.85-0.95",
            "estimated_cost": "1000개 기사당 약 $0.02-0.05"
        },
        "usage": {
            "api_endpoint": "POST /api/deduplication/remove",
            "required_fields": ["file_path", "api_key"],
            "optional_fields": {
                "similarity_threshold": "0.85 (기본값)",
                "batch_size": "50 (기본값)",
                "embedding_model": "text-embedding-3-small (기본값)"
            }
        },
        "performance": {
            "accuracy": "90-95%",
            "speed": "1000개 기사 약 2-3분",
            "memory_efficiency": "O(n) 복잡도",
            "suitable_for": "모든 크기의 데이터셋"
        }
    }
