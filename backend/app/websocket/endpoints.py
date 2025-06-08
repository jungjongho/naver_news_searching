#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WebSocket 엔드포인트
"""

import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """진행률 업데이트를 위한 WebSocket 엔드포인트"""
    logger.info(f"WebSocket 연결 요청: session_id={session_id}")
    
    try:
        await manager.connect(websocket, session_id)
        logger.info(f"WebSocket 연결 성공: session_id={session_id}")
        
        # 연결 확인 메시지 전송
        await manager.send_personal_message({
            "type": "connection_established",
            "session_id": session_id,
            "message": "WebSocket 연결이 성공적으로 설정되었습니다."
        }, session_id)
        
        while True:
            # 클라이언트로부터 메시지를 대기 (연결 유지용)
            data = await websocket.receive_text()
            logger.debug(f"WebSocket 메시지 수신: session_id={session_id}, data={data}")
            
            # ping 메시지에 pong으로 응답
            try:
                message_data = json.loads(data)
                if message_data.get('type') == 'ping':
                    await manager.send_personal_message({
                        "type": "pong",
                        "session_id": session_id
                    }, session_id)
                    logger.debug(f"Pong 응답 전송: session_id={session_id}")
            except json.JSONDecodeError:
                logger.warning(f"JSON 파싱 실패: session_id={session_id}, data={data}")
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
        logger.info(f"WebSocket 연결이 클라이언트에 의해 종료됨: session_id={session_id}")
    except Exception as e:
        logger.error(f"WebSocket 오류: session_id={session_id}, error={str(e)}")
        manager.disconnect(websocket, session_id)
