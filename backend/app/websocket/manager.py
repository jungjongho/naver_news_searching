#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WebSocket 연결 관리자
"""

import json
import logging
import asyncio
from typing import Dict, List
from fastapi import WebSocket

logger = logging.getLogger(__name__)

# WebSocket 관련 로깅을 INFO 레벨로 제한
websocket_logger = logging.getLogger(f"{__name__}.websocket")
websocket_logger.setLevel(logging.INFO)


class ConnectionManager:
    """WebSocket 연결 관리"""
    
    def __init__(self):
        # session_id별로 웹소켓 연결들을 관리
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """클라이언트 연결"""
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        
        self.active_connections[session_id].append(websocket)
        logger.info(f"WebSocket 연결됨: session_id={session_id}, 총 연결 수={len(self.active_connections[session_id])}")
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        """클라이언트 연결 해제"""
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
                logger.info(f"WebSocket 연결 해제됨: session_id={session_id}")
            
            # 해당 세션의 연결이 모두 해제되면 세션 제거
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
                logger.info(f"세션 제거됨: session_id={session_id}")
    
    def is_session_active(self, session_id: str) -> bool:
        """세션이 활성 상태인지 확인"""
        return session_id in self.active_connections and len(self.active_connections[session_id]) > 0
    
    async def send_personal_message(self, message: dict, session_id: str) -> bool:
        """특정 세션에 메시지 전송 (연결 단절 시 조용히 무시)"""
        
        if session_id not in self.active_connections:
            return False  # 연결 상태 반환
        
        if not self.active_connections[session_id]:
            # 빈 세션 제거
            del self.active_connections[session_id]
            return False
            
        # 연결이 끊어진 websocket들을 제거하기 위한 리스트
        active_websockets = []
        message_json = json.dumps(message, ensure_ascii=False)
        success_count = 0
        
        for websocket in self.active_connections[session_id]:
            try:
                # WebSocket 상태 확인
                if websocket.client_state.name != 'CONNECTED':
                    continue
                    
                await websocket.send_text(message_json)
                active_websockets.append(websocket)
                success_count += 1
            except Exception as e:
                # 연결 끊김은 정상적인 상황이므로 로그 레벨 낮춤
                websocket_logger.debug(f"WebSocket 메시지 전송 실패: session_id={session_id}, error={e}")
        
        # 활성 연결만 유지
        self.active_connections[session_id] = active_websockets
        
        if not active_websockets:
            websocket_logger.debug(f"WebSocket 연결 종료: session_id={session_id}")
            del self.active_connections[session_id]
            return False
        
        return success_count > 0
    
    async def send_progress_update(self, session_id: str, current: int, total: int, 
                                  category: str = None, confidence: float = None, 
                                  article_title: str = None, force_send: bool = False):
        """진행률 업데이트 메시지 전송 (연결 끊김 시 조용히 무시)"""
        
        # 연결 상태 확인 (로그 스팸 방지)
        if not self.is_session_active(session_id):
            return False
        
        # force_send가 True가 아니면 선택적 전송 (성능 최적화)
        if not force_send and total > 0:
            percentage = (current / total) * 100
            # 5% 간격, 첫 번째, 마지막 항목에서만 전송
            should_send = (
                current == 0 or 
                current == total or 
                percentage % 5 < (100 / total)
            )
            if not should_send:
                return True  # 전송하지 않았지만 성공으로 처리
        
        progress_data = {
            "type": "progress_update",
            "current": current,
            "total": total,
            "percentage": round((current / total) * 100, 1) if total > 0 else 0,
            "category": category,
            "confidence": confidence,
            "article_title": article_title[:100] + "..." if article_title and len(article_title) > 100 else article_title
        }
        
        # 진행률 업데이트는 실패해도 로그를 최소화
        try:
            success = await self.send_personal_message(progress_data, session_id)
            if success:
                # 성공 시만 로그 출력 (선택적)
                if force_send or current % 5 == 0 or current == total:
                    websocket_logger.info(f"진행률 전송 성공: {session_id} - {current}/{total} ({progress_data['percentage']}%)")
                return True
            else:
                # 연결 끊김은 정상 상황이므로 DEBUG 레벨로 변경
                websocket_logger.debug(f"WebSocket 연결 없음: session_id={session_id}")
                return False
        except Exception as e:
            websocket_logger.warning(f"진행률 업데이트 전송 실패: session_id={session_id}, error={e}")
            return False
    
    async def send_completion_message(self, session_id: str, stats: dict):
        """완료 메시지 전송"""
        
        if not self.is_session_active(session_id):
            return False
        
        # 통계 데이터 정리 및 검증
        processed_stats = {
            "total_items": stats.get("total_items", 0),
            "successfully_analyzed": stats.get("successfully_analyzed", 0),
            "failed_analysis": stats.get("failed_analysis", 0),
            "processing_errors": stats.get("processing_errors", 0),
            "analysis_success_percent": stats.get("analysis_success_percent", 0),
            "processing_time": stats.get("processing_time", 0),
            "batch_size": stats.get("batch_size", 1),
            "stopped_by_user": stats.get("stopped_by_user", False)
        }
        
        # 카테고리별 통계 처리 (동적 필드)
        field_stats = stats.get("field_statistics", {})
        categories = {}
        
        # 첫 번째 필드를 카테고리로 간주하고 통계 추출
        for field_name, field_values in field_stats.items():
            if field_name.lower() in ['category', '카테고리'] or field_name == list(field_stats.keys())[0]:
                for value, count in field_values.items():
                    if value and value != "None" and value != "unknown":
                        categories[str(value)] = count
                break
        
        # 전체 관련 기사 수 계산 (기타 제외)
        relevant_items = sum(count for category, count in categories.items() 
                           if category not in ['기타', 'unknown', 'default'])
        relevant_percent = round((relevant_items / processed_stats["total_items"]) * 100, 1) if processed_stats["total_items"] > 0 else 0
        
        processed_stats.update({
            "categories": categories,
            "relevant_items": relevant_items,
            "relevant_percent": relevant_percent
        })
        
        completion_data = {
            "type": "analysis_complete",
            "stats": processed_stats
        }
        
        logger.info(f"분석 완료 메시지 전송: session_id={session_id}, 총 {processed_stats['total_items']}개, 관련 {relevant_items}개 ({relevant_percent}%)")
        return await self.send_personal_message(completion_data, session_id)
    
    async def send_deduplication_completion_message(self, session_id: str, stats: dict):
        """중복 제거 완료 메시지 전송"""
        
        if not self.is_session_active(session_id):
            return False
        
        # 중복 제거 통계 데이터 정리
        processed_stats = {
            "original_count": stats.get("original_count", 0),
            "deduplicated_count": stats.get("deduplicated_count", 0),
            "removed_count": stats.get("removed_count", 0),
            "duplicate_groups_count": stats.get("duplicate_groups_count", 0),
            "reduction_percentage": stats.get("reduction_percentage", 0),
            "processing_time": stats.get("processing_time", 0),
            "similarity_threshold": stats.get("similarity_threshold", 0.85),
            "method": stats.get("method", "GPT 임베딩"),
            "embedding_model": stats.get("embedding_model", "text-embedding-3-small")
        }
        
        completion_data = {
            "type": "deduplication_complete",
            "stats": processed_stats
        }
        
        logger.info(f"중복 제거 완료 메시지 전송: session_id={session_id}, 원본 {processed_stats['original_count']}개 → 최종 {processed_stats['deduplicated_count']}개 ({processed_stats['reduction_percentage']}% 감소)")
        return await self.send_personal_message(completion_data, session_id)
    
    async def send_error_message(self, session_id: str, error_message: str):
        """오류 메시지 전송"""
        
        if not self.is_session_active(session_id):
            return False
        
        error_data = {
            "type": "error",
            "message": error_message
        }
        
        logger.error(f"오류 메시지 전송: session_id={session_id}, error={error_message}")
        return await self.send_personal_message(error_data, session_id)
    
    async def send_stop_message(self, session_id: str, current: int, total: int):
        """중지 메시지 전송"""
        
        if not self.is_session_active(session_id):
            return False
        
        stop_data = {
            "type": "analysis_stopped",
            "current": current,
            "total": total,
            "message": f"사용자 요청에 의해 분석이 중지되었습니다. ({current}/{total} 완료)"
        }
        
        logger.info(f"분석 중지 메시지 전송: session_id={session_id}, {current}/{total}")
        return await self.send_personal_message(stop_data, session_id)


# 전역 연결 관리자 인스턴스
manager = ConnectionManager()
