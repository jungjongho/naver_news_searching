#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WebSocket 연결 관리자
"""

import json
import logging
from typing import Dict, List
from fastapi import WebSocket

logger = logging.getLogger(__name__)


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
    
    async def send_personal_message(self, message: dict, session_id: str):
        """특정 세션에 메시지 전송"""
        if session_id in self.active_connections:
            # 연결이 끊어진 websocket들을 제거하기 위한 리스트
            active_websockets = []
            
            for websocket in self.active_connections[session_id]:
                try:
                    await websocket.send_text(json.dumps(message, ensure_ascii=False))
                    active_websockets.append(websocket)
                except Exception as e:
                    logger.warning(f"WebSocket 메시지 전송 실패: {e}")
            
            # 활성 연결만 유지
            self.active_connections[session_id] = active_websockets
    
    async def send_progress_update(self, session_id: str, current: int, total: int, 
                                  category: str = None, confidence: float = None, 
                                  article_title: str = None):
        """진행률 업데이트 메시지 전송"""
        progress_data = {
            "type": "progress_update",
            "current": current,
            "total": total,
            "percentage": round((current / total) * 100, 1) if total > 0 else 0,
            "category": category,
            "confidence": confidence,
            "article_title": article_title[:100] + "..." if article_title and len(article_title) > 100 else article_title
        }
        
        await self.send_personal_message(progress_data, session_id)
    
    async def send_completion_message(self, session_id: str, stats: dict):
        """완료 메시지 전송"""
        completion_data = {
            "type": "analysis_complete",
            "stats": stats
        }
        
        await self.send_personal_message(completion_data, session_id)
    
    async def send_error_message(self, session_id: str, error_message: str):
        """오류 메시지 전송"""
        error_data = {
            "type": "error",
            "message": error_message
        }
        
        await self.send_personal_message(error_data, session_id)


# 전역 연결 관리자 인스턴스
manager = ConnectionManager()
