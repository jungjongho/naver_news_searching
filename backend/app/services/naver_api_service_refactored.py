#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""리팩토링된 네이버 API 서비스"""

import datetime
import os
from typing import List, Dict, Any, Optional, Tuple
import logging

from app.services.search.naver_search_service import NaverSearchService
from app.services.data.news_processor import NewsProcessor
from app.utils.validators.keyword_validator import KeywordValidator
from app.utils.validators.date_validator import DateValidator
from app.utils.file_utils import save_to_excel
from app.utils.deduplication import deduplicate_by_url
from app.core.config import settings

logger = logging.getLogger(__name__)


class NaverApiService:
    """리팩토링된 네이버 뉴스 API 서비스"""
    
    def __init__(self):
        self.search_service = NaverSearchService()
        self._ensure_results_directory()
    
    def _ensure_results_directory(self):
        """결과 저장 디렉토리 확인 및 생성"""
        os.makedirs(settings.CRAWLING_RESULTS_PATH, exist_ok=True)
    
    def search_keywords(
        self, 
        keywords: List[str], 
        max_news_per_keyword: int = 100, 
        sort: str = "date", 
        days: int = 30, 
        start_date: str = None, 
        end_date: str = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """여러 키워드에 대한 뉴스 검색 (메인 인터페이스)"""
        
        # 키워드 검증
        is_valid, valid_keywords, keyword_errors = KeywordValidator.validate_keywords(keywords)
        if not is_valid:
            return [], {"validation_error": "; ".join(keyword_errors)}
        
        # 날짜 범위 설정
        start_date_obj, end_date_obj, date_error = self._setup_date_range(
            days, start_date, end_date
        )
        if date_error:
            return [], {"date_error": date_error}
        
        # 검색 실행
        search_results, search_errors = self.search_service.search_multiple_keywords(
            valid_keywords, max_news_per_keyword, sort
        )
        
        # 데이터 처리
        all_news_items = []
        processing_errors = {}
        
        for keyword, raw_items in search_results.items():
            try:
                processed_items = NewsProcessor.process_news_items(
                    raw_items, keyword, start_date_obj, end_date_obj
                )
                all_news_items.extend(processed_items)
                
            except Exception as e:
                logger.error(f"키워드 '{keyword}' 데이터 처리 오류: {str(e)}")
                processing_errors[keyword] = f"데이터 처리 오류: {str(e)}"
        
        # 중복 제거
        if all_news_items:
            all_news_items = deduplicate_by_url(all_news_items)
            logger.info(f"중복 제거 후 총 뉴스 개수: {len(all_news_items)}")
        
        # 모든 오류 합치기
        all_errors = {**search_errors, **processing_errors}
        
        return all_news_items, all_errors
    
    def _setup_date_range(
        self, 
        days: int, 
        start_date: str = None, 
        end_date: str = None
    ) -> Tuple[Optional[datetime.datetime], Optional[datetime.datetime], Optional[str]]:
        """날짜 범위 설정"""
        
        start_date_obj = None
        end_date_obj = None
        
        if start_date and end_date:
            # 명시적 날짜 범위 사용
            is_valid, error_msg = DateValidator.validate_date_range(start_date, end_date)
            if not is_valid:
                return None, None, error_msg
            
            start_date_obj = DateValidator.parse_date(start_date)
            end_date_obj = DateValidator.parse_date(end_date)
            # 종료 날짜를 하루의 끝으로 설정
            if end_date_obj:
                end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59)
        
        elif start_date:
            # 시작 날짜만 지정된 경우
            start_date_obj = DateValidator.parse_date(start_date)
            if not start_date_obj:
                return None, None, f"잘못된 시작 날짜 형식: {start_date}"
        
        elif end_date:
            # 종료 날짜만 지정된 경우
            end_date_obj = DateValidator.parse_date(end_date)
            if not end_date_obj:
                return None, None, f"잘못된 종료 날짜 형식: {end_date}"
            end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59)
        
        else:
            # 기본: 최근 N일
            start_date_obj, _ = DateValidator.get_date_range_from_days(days)
        
        return start_date_obj, end_date_obj, None
    
    def save_results(
        self, 
        news_items: List[Dict[str, Any]], 
        keywords: List[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """검색 결과를 Excel 파일로 저장"""
        if not news_items:
            logger.warning("저장할 뉴스 아이템이 없습니다")
            return None, None
        
        try:
            # 파일명 생성
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            keywords_str = KeywordValidator.format_keywords_for_filename(keywords)
            
            file_name = f"naver_news_{keywords_str}_{timestamp}.xlsx"
            file_path = os.path.join(settings.CRAWLING_RESULTS_PATH, file_name)
            
            # 파일 저장
            success, download_path = save_to_excel(
                news_items, 
                file_path, 
                copy_to_download=settings.AUTO_COPY_TO_DOWNLOADS,
                download_path=settings.USER_DOWNLOAD_PATH
            )
            
            if success:
                if download_path:
                    logger.info(f"{len(news_items)}개 뉴스를 {file_path}에 저장하고 {download_path}에 복사했습니다")
                else:
                    logger.info(f"{len(news_items)}개 뉴스를 {file_path}에 저장했습니다")
                return file_path, download_path
            else:
                logger.error("결과 저장 실패")
                return None, None
        
        except Exception as e:
            logger.error(f"결과 저장 중 오류: {str(e)}")
            return None, None
    
    def get_search_statistics(self, keywords: List[str]) -> Dict[str, Any]:
        """키워드별 검색 통계 정보 조회"""
        stats = {}
        
        for keyword in keywords:
            total_count = self.search_service.get_total_count(keyword)
            stats[keyword] = {
                "total_available": total_count,
                "keyword": keyword
            }
        
        return stats
