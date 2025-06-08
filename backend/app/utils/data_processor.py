#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class DataProcessor:
    """데이터 처리 유틸리티 클래스"""
    
    @staticmethod
    def clean_dataframe_efficient(df: pd.DataFrame) -> pd.DataFrame:
        """효율적인 DataFrame 정리"""
        # 한 번에 모든 inf 값과 NaN 처리
        return df.replace([float('inf'), float('-inf')], None).fillna('')
    
    @staticmethod
    def safe_json_parse(response_text: str) -> Dict[str, Any]:
        """안전하고 효율적인 JSON 파싱"""
        try:
            # 1. 코드 블록 제거 (가장 흔한 경우)
            cleaned_text = response_text.strip()
            
            if "```json" in cleaned_text:
                # json 코드 블록 추출
                start = cleaned_text.find("```json") + 7
                end = cleaned_text.find("```", start)
                if end != -1:
                    cleaned_text = cleaned_text[start:end].strip()
            elif "```" in cleaned_text:
                # 일반 코드 블록에서 JSON 찾기
                parts = cleaned_text.split("```")
                for part in parts:
                    part = part.strip()
                    if part.startswith('{') and part.endswith('}'):
                        cleaned_text = part
                        break
            
            # 2. JSON 객체 경계 찾기
            start_idx = cleaned_text.find('{')
            end_idx = cleaned_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = cleaned_text[start_idx:end_idx + 1]
                result = json.loads(json_str)
                
                # 3. 필수 필드 검증 및 기본값 설정
                return DataProcessor._validate_and_normalize_result(result)
            
            # JSON 파싱 실패 시 기본값 반환
            return DataProcessor._get_default_analysis_result()
            
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.debug(f"JSON 파싱 실패, 기본값 반환: {str(e)}")
            return DataProcessor._get_default_analysis_result()
    
    @staticmethod
    def _validate_and_normalize_result(result: Dict[str, Any]) -> Dict[str, Any]:
        """결과 검증 및 정규화"""
        # 필수 필드 기본값 설정
        result.setdefault("category", "기타")
        result.setdefault("confidence", 0.5)
        result.setdefault("keywords", [])
        
        # 카테고리명 정규화 (매핑 테이블 사용)
        category_mapping = {
            "자사 언급기사": "자사언급기사",
            "업계 관련기사": "업계관련기사", 
            "건기식·펫푸드 관련기사": "건기식펫푸드관련기사",
            "건강기능식품·펫푸드": "건기식펫푸드관련기사",
            "건기식펫푸드": "건기식펫푸드관련기사"
        }
        
        category = result["category"]
        if category in category_mapping:
            result["category"] = category_mapping[category]
        
        # confidence 값 검증 (0-1 범위)
        confidence = result["confidence"]
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
            result["confidence"] = 0.5
        
        # keywords가 리스트인지 확인
        if not isinstance(result["keywords"], list):
            result["keywords"] = []
        
        return result
    
    @staticmethod
    def _get_default_analysis_result() -> Dict[str, Any]:
        """기본 분석 결과 반환"""
        return {
            "category": "기타",
            "confidence": 0.0,
            "keywords": []
        }
    
    @staticmethod
    def batch_process_news_items(news_items: List[Dict[str, Any]], 
                                batch_size: int = 100) -> List[List[Dict[str, Any]]]:
        """뉴스 아이템을 배치 단위로 분할"""
        batches = []
        for i in range(0, len(news_items), batch_size):
            batch = news_items[i:i + batch_size]
            batches.append(batch)
        return batches
    
    @staticmethod
    def extract_text_content(news_item: Dict[str, Any]) -> tuple[str, str]:
        """뉴스 아이템에서 제목과 내용 추출 (다양한 키 지원)"""
        # 제목 추출
        title = (
            news_item.get("title") or 
            news_item.get("제목") or 
            ""
        )
        
        # 내용 추출
        content = (
            news_item.get("description") or 
            news_item.get("content") or 
            news_item.get("내용") or 
            ""
        )
        
        return title.strip(), content.strip()
    
    @staticmethod
    def format_keywords_for_filename(keywords: List[str], max_length: int = 100) -> str:
        """키워드를 파일명에 적합한 형식으로 변환"""
        if not keywords:
            return "unknown"
        
        # 키워드 수 제한
        if len(keywords) > 3:
            keywords_str = '_'.join(keywords[:3]) + f"_and_{len(keywords)-3}_more"
        else:
            keywords_str = '_'.join(keywords)
        
        # 파일명 특수문자 제거
        safe_chars = []
        for char in keywords_str:
            if char.isalnum() or char in ['_', '-']:
                safe_chars.append(char)
            elif char in [' ', '/', '\\']:
                safe_chars.append('_')
        
        keywords_str = ''.join(safe_chars)
        
        # 길이 제한
        if len(keywords_str) > max_length:
            return keywords_str[:max_length-3] + '...'
        
        return keywords_str
    
    @staticmethod
    def calculate_statistics(analyzed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """분석 결과 통계 계산"""
        if not analyzed_data:
            return {
                "total_items": 0,
                "relevant_items": 0,
                "categories": {},
                "relevant_ratio": 0.0,
                "relevant_percent": 0.0
            }
        
        total_items = len(analyzed_data)
        categories = {}
        relevant_items = 0
        
        for item in analyzed_data:
            category = item.get("category", "기타")
            categories[category] = categories.get(category, 0) + 1
            
            if category != "기타":
                relevant_items += 1
        
        relevant_ratio = relevant_items / total_items if total_items > 0 else 0
        
        return {
            "total_items": total_items,
            "relevant_items": relevant_items,
            "categories": categories,
            "relevant_ratio": relevant_ratio,
            "relevant_percent": round(relevant_ratio * 100, 1)
        }


# 전역 인스턴스
data_processor = DataProcessor()
