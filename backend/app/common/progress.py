#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
진행상황 추적 서비스
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)


class ProgressTracker:
    """진행상황 추적 서비스"""
    
    def __init__(self):
        self.progress_dir = os.path.join(settings.RESULTS_PATH, 'progress')
        os.makedirs(self.progress_dir, exist_ok=True)
    
    def update_progress(
        self,
        session_id: str,
        current: int,
        total: int,
        stage: str = '',
        current_item: str = '',
        stats: Optional[Dict[str, Any]] = None,
        processed_item: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """진행상황 업데이트"""
        try:
            # 기존 진행상황 불러오기
            existing_progress = self.get_progress(session_id)
            
            # 새 진행상황 데이터 생성
            progress_data = {
                'current': current,
                'total': total,
                'stage': stage,
                'current_item': current_item[:100] if current_item else '',
                'timestamp': datetime.now().isoformat(),
                'stats': stats or {},
                'processed_items': existing_progress.get('processed_items', []),
                'errors': existing_progress.get('errors', [])
            }
            
            # 새로 처리된 항목 추가
            if processed_item:
                progress_data['processed_items'].append({
                    'title': processed_item.get('title', processed_item.get('제목', ''))[:50],
                    'category': processed_item.get('category', ''),
                    'status': 'success',
                    'index': current,
                    'timestamp': datetime.now().isoformat()
                })
                # 최대 20개까지만 유지
                if len(progress_data['processed_items']) > 20:
                    progress_data['processed_items'] = progress_data['processed_items'][-20:]
            
            # 오류 추가
            if error:
                progress_data['errors'].append({
                    'message': error[:200],  # 에러 메시지 길이 제한
                    'item': current_item[:50] if current_item else '',
                    'timestamp': datetime.now().isoformat()
                })
                # 최대 10개까지만 유지
                if len(progress_data['errors']) > 10:
                    progress_data['errors'] = progress_data['errors'][-10:]
            
            # 파일에 저장
            self._save_to_file(session_id, progress_data)
            
        except Exception as e:
            logger.error(f"진행상황 업데이트 실패: {str(e)}")
    
    def get_progress(self, session_id: str) -> Dict[str, Any]:
        """진행상황 조회"""
        try:
            progress_file = os.path.join(self.progress_dir, f'{session_id}_progress.json')
            
            if os.path.exists(progress_file):
                with open(progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {
                    'current': 0,
                    'total': 0,
                    'stage': '대기 중',
                    'processed_items': [],
                    'errors': []
                }
                
        except Exception as e:
            logger.error(f"진행상황 조회 실패: {str(e)}")
            return {
                'current': 0,
                'total': 0,
                'stage': '오류 발생',
                'error': str(e),
                'processed_items': [],
                'errors': []
            }
    
    def cleanup_session(self, session_id: str) -> None:
        """세션 정리"""
        try:
            progress_file = os.path.join(self.progress_dir, f'{session_id}_progress.json')
            if os.path.exists(progress_file):
                os.remove(progress_file)
                logger.info(f"진행상황 파일 정리 완료: {session_id}")
        except Exception as e:
            logger.error(f"진행상황 파일 정리 실패: {str(e)}")
    
    def _save_to_file(self, session_id: str, progress_data: Dict[str, Any]) -> None:
        """파일에 진행상황 저장"""
        progress_file = os.path.join(self.progress_dir, f'{session_id}_progress.json')
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2, default=str)


# 전역 인스턴스
progress_tracker = ProgressTracker()
