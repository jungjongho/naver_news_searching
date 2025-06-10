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
        logger.info(f"📤 WebSocket 메시지 전송 시도: session_id={session_id}, type={message.get('type', 'unknown')}")
        
        if session_id not in self.active_connections:
            logger.warning(f"⚠️ 세션 연결이 없음: session_id={session_id}")
            return
        
        if not self.active_connections[session_id]:
            logger.warning(f"⚠️ 세션에 활성 연결이 없음: session_id={session_id}")
            return
            
        # 연결이 끊어진 websocket들을 제거하기 위한 리스트
        active_websockets = []
        message_json = json.dumps(message, ensure_ascii=False)
        
        for websocket in self.active_connections[session_id]:
            try:
                await websocket.send_text(message_json)
                # 즉시 flush를 위해 짧은 대기
                await asyncio.sleep(0.001)  # 1ms 대기로 즉시 전송
                active_websockets.append(websocket)
                logger.info(f"✅ WebSocket 메시지 전송 성공: session_id={session_id}")
            except Exception as e:
                logger.warning(f"❌ WebSocket 메시지 전송 실패: session_id={session_id}, error={e}")
        
        # 활성 연결만 유지
        self.active_connections[session_id] = active_websockets
        
        if not active_websockets:
            logger.warning(f"⚠️ 모든 WebSocket 연결이 실패함: session_id={session_id}")
    
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
        
        logger.info(f"📊 진행률 업데이트 전송: {current}/{total} ({progress_data['percentage']}%) - {session_id}")
        await self.send_personal_message(progress_data, session_id)
    
    async def send_completion_message(self, session_id: str, stats: dict):
        """완료 메시지 전송"""
        completion_data = {
            "type": "analysis_complete",
            "stats": stats
        }
        
        logger.info(f"🎉 분석 완료 메시지 전송: session_id={session_id}")
        await self.send_personal_message(completion_data, session_id)
    
    async def send_error_message(self, session_id: str, error_message: str):
        """오류 메시지 전송"""
        error_data = {
            "type": "error",
            "message": error_message
        }
        
        logger.error(f"❌ 오류 메시지 전송: session_id={session_id}, error={error_message}")
        await self.send_personal_message(error_data, session_id)
    
    async def send_stop_message(self, session_id: str, current: int, total: int):
        """중지 메시지 전송"""
        stop_data = {
            "type": "analysis_stopped",
            "current": current,
            "total": total,
            "message": f"사용자 요청에 의해 분석이 중지되었습니다. ({current}/{total} 완료)"
        }
        
        logger.info(f"⏹️ 분석 중지 메시지 전송: session_id={session_id}, {current}/{total}")
        await self.send_personal_message(stop_data, session_id)


# 전역 연결 관리자 인스턴스
manager = ConnectionManager()
