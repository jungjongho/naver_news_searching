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
        """결과 검증 및 정규화 (동적 필드 지원)"""
        if not isinstance(result, dict):
            return {}
        
        # 기본 정규화만 수행 (고정 필드 없음)
        normalized_result = {}
        
        for key, value in result.items():
            # 키 정규화 (대소문자 통일)
            normalized_key = key.lower().strip()
            
            # 값 기본 검증
            if value is None:
                normalized_result[normalized_key] = ""
            elif isinstance(value, (list, dict)):
                normalized_result[normalized_key] = value
            else:
                normalized_result[normalized_key] = str(value)
        
        return normalized_result
    
    @staticmethod
    def _get_default_analysis_result(news_id: str = None) -> Dict[str, Any]:
        """기본 분석 결과 반환 (동적 필드)"""
        result = {
            "analysis_status": "failed",
            "analysis_note": "분석 실패 또는 기본값이 사용됨"
        }
        
        if news_id:
            result["news_id"] = news_id
            
        return result
    
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
    def extract_text_content(news_item: Dict[str, Any]) -> tuple[str, str, str]:
        """뉴스 아이템에서 news_id, 제목과 내용 추출 (다양한 키 지원)"""
        # news_id 추출
        news_id = news_item.get("news_id", "")
        
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
        
        return news_id.strip(), title.strip(), content.strip()
    
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
        """분석 결과 통계 계산 (동적 필드)"""
        if not analyzed_data:
            return {
                "total_items": 0,
                "successfully_analyzed": 0,
                "failed_analysis": 0,
                "analysis_success_rate": 0.0
            }
        
        total_items = len(analyzed_data)
        successfully_analyzed = 0
        failed_analysis = 0
        
        # 각 필드별 통계
        field_statistics = {}
        
        for item in analyzed_data:
            # 분석 성공/실패 통계
            if item.get("analysis_status") == "failed":
                failed_analysis += 1
            else:
                successfully_analyzed += 1
            
            # 각 필드별 값 통계
            for key, value in item.items():
                if key.startswith(('title', 'content', 'description', '제목', '내용', 'link', 'pubdate')):
                    # 원본 데이터 필드는 제외
                    continue
                    
                if key not in field_statistics:
                    field_statistics[key] = {}
                
                value_str = str(value) if value is not None else "None"
                field_statistics[key][value_str] = field_statistics[key].get(value_str, 0) + 1
        
        success_rate = successfully_analyzed / total_items if total_items > 0 else 0
        
        return {
            "total_items": total_items,
            "successfully_analyzed": successfully_analyzed,
            "failed_analysis": failed_analysis,
            "analysis_success_rate": round(success_rate * 100, 1),
            "field_statistics": field_statistics
        }


# 전역 인스턴스
data_processor = DataProcessor()
