#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""날짜 검증 유틸리티"""

import datetime
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class DateValidator:
    """날짜 검증 및 처리를 담당하는 클래스"""
    
    @staticmethod
    def parse_date(date_string: str, date_format: str = "%Y-%m-%d") -> Optional[datetime.datetime]:
        """문자열을 datetime 객체로 변환"""
        try:
            return datetime.datetime.strptime(date_string, date_format)
        except ValueError as e:
            logger.warning(f"날짜 파싱 실패: {date_string}, 오류: {str(e)}")
            return None
    
    @staticmethod
    def validate_date_range(start_date: str, end_date: str) -> Tuple[bool, Optional[str]]:
        """날짜 범위 검증"""
        start_dt = DateValidator.parse_date(start_date)
        end_dt = DateValidator.parse_date(end_date)
        
        if not start_dt:
            return False, f"잘못된 시작 날짜 형식: {start_date}"
        
        if not end_dt:
            return False, f"잘못된 종료 날짜 형식: {end_date}"
        
        if start_dt > end_dt:
            return False, "시작 날짜는 종료 날짜보다 이전이어야 합니다"
        
        # 미래 날짜 체크
        today = datetime.datetime.now()
        if start_dt > today:
            return False, "시작 날짜는 오늘 이전이어야 합니다"
        
        return True, None
    
    @staticmethod
    def get_date_range_from_days(days: int) -> Tuple[datetime.datetime, datetime.datetime]:
        """일수를 기반으로 날짜 범위 계산"""
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)
        return start_date, end_date
    
    @staticmethod
    def format_for_filename(date_obj: datetime.datetime) -> str:
        """파일명에 적합한 날짜 문자열 반환"""
        return date_obj.strftime("%Y%m%d_%H%M%S")
    
    @staticmethod
    def is_within_range(
        target_date: datetime.datetime, 
        start_date: datetime.datetime, 
        end_date: datetime.datetime
    ) -> bool:
        """대상 날짜가 범위 내에 있는지 확인"""
        return start_date <= target_date <= end_date
