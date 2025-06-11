#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""키워드 검증 유틸리티"""

from typing import List, Tuple
import re
import logging

logger = logging.getLogger(__name__)


class KeywordValidator:
    """키워드 검증을 담당하는 클래스"""
    
    # 허용되지 않는 특수문자 패턴
    INVALID_CHARS_PATTERN = re.compile(r'[<>:"/\\|?*]')
    
    @staticmethod
    def validate_keyword(keyword: str) -> Tuple[bool, Optional[str]]:
        """단일 키워드 검증"""
        if not keyword or not keyword.strip():
            return False, "키워드가 비어있습니다"
        
        keyword = keyword.strip()
        
        # 길이 검증
        if len(keyword) > 100:
            return False, "키워드는 100자를 초과할 수 없습니다"
        
        # 최소 길이 검증
        if len(keyword) < 1:
            return False, "키워드는 최소 1자 이상이어야 합니다"
        
        # 특수문자 검증 (일부 허용)
        if KeywordValidator.INVALID_CHARS_PATTERN.search(keyword):
            return False, "키워드에 허용되지 않는 특수문자가 포함되어 있습니다"
        
        return True, None
    
    @staticmethod
    def validate_keywords(keywords: List[str]) -> Tuple[bool, List[str], List[str]]:
        """키워드 목록 검증"""
        if not keywords:
            return False, [], ["키워드 목록이 비어있습니다"]
        
        valid_keywords = []
        errors = []
        
        for keyword in keywords:
            is_valid, error_msg = KeywordValidator.validate_keyword(keyword)
            if is_valid:
                # 중복 제거
                clean_keyword = keyword.strip()
                if clean_keyword not in valid_keywords:
                    valid_keywords.append(clean_keyword)
            else:
                errors.append(f"키워드 '{keyword}': {error_msg}")
        
        if not valid_keywords:
            errors.append("유효한 키워드가 없습니다")
            return False, [], errors
        
        return True, valid_keywords, errors
    
    @staticmethod
    def sanitize_for_filename(keyword: str) -> str:
        """파일명에 적합하도록 키워드 정제"""
        # 공백을 언더스코어로 변경
        sanitized = keyword.replace(' ', '_')
        
        # 파일명에 사용할 수 없는 문자 제거
        sanitized = re.sub(r'[<>:"/\\|?*]', '', sanitized)
        
        # 연속된 언더스코어 제거
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # 앞뒤 언더스코어 제거
        sanitized = sanitized.strip('_')
        
        return sanitized
    
    @staticmethod
    def format_keywords_for_filename(keywords: List[str], max_length: int = 50) -> str:
        """키워드 목록을 파일명에 적합한 형식으로 변환"""
        if not keywords:
            return "unknown"
        
        sanitized_keywords = [
            KeywordValidator.sanitize_for_filename(keyword) 
            for keyword in keywords
        ]
        
        # 길이 제한을 고려한 키워드 선택
        if len(sanitized_keywords) <= 3:
            result = '_'.join(sanitized_keywords)
        else:
            result = '_'.join(sanitized_keywords[:3]) + f"_and_{len(sanitized_keywords)-3}_more"
        
        # 최대 길이 제한
        if len(result) > max_length:
            result = result[:max_length-3] + "..."
        
        return result
