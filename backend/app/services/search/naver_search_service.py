#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""네이버 뉴스 검색 서비스"""

import requests
from urllib.parse import quote
from typing import List, Dict, Any, Optional, Tuple
import logging

from app.core.config import settings
from app.utils.constants.api_constants import (
    NAVER_NEWS_API_URL, MAX_DISPLAY_PER_REQUEST, MAX_START_INDEX, DEFAULT_SORT
)

logger = logging.getLogger(__name__)


class NaverSearchService:
    """네이버 뉴스 API 검색을 담당하는 클래스"""
    
    def __init__(self):
        self._validate_api_keys()
        self._setup_headers()
    
    def _validate_api_keys(self):
        """API 키 검증"""
        self.client_id = settings.NAVER_CLIENT_ID
        self.client_secret = settings.NAVER_CLIENT_SECRET
        
        if not self.client_id or not self.client_secret:
            logger.error("Naver API keys are not set")
            raise ValueError("NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET이 설정되어 있지 않습니다.")
    
    def _setup_headers(self):
        """API 요청 헤더 설정"""
        self.headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }
    
    def search_single_keyword(
        self, 
        keyword: str, 
        max_news: int = 100, 
        sort: str = DEFAULT_SORT
    ) -> List[Dict[str, Any]]:
        """단일 키워드로 뉴스 검색"""
        logger.info(f"네이버 API 검색 시작: {keyword}")
        
        encoded_query = quote(keyword)
        all_news = []
        
        display = min(MAX_DISPLAY_PER_REQUEST, max_news)
        
        for start in range(1, min(MAX_START_INDEX, max_news + 1), display):
            remaining = max_news - len(all_news)
            if remaining <= 0:
                break
            
            current_display = min(display, remaining)
            url = f"{NAVER_NEWS_API_URL}?query={encoded_query}&display={current_display}&start={start}&sort={sort}"
            
            try:
                res = requests.get(url, headers=self.headers, timeout=10)
                res.raise_for_status()
                
                data = res.json()
                items = data.get("items", [])
                
                if not items:
                    logger.info(f"키워드 '{keyword}'에 대한 추가 결과가 없습니다.")
                    break
                
                all_news.extend(items)
                
                # API 제한에 도달했거나 요청한 만큼 받았으면 종료
                if len(items) < current_display or len(all_news) >= max_news:
                    break
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"API 요청 오류 (키워드: {keyword}): {str(e)}")
                break
            except Exception as e:
                logger.error(f"예상치 못한 오류 (키워드: {keyword}): {str(e)}")
                break
        
        logger.info(f"키워드 '{keyword}'에 대해 {len(all_news)}개 뉴스 수집 완료")
        return all_news
    
    def search_multiple_keywords(
        self, 
        keywords: List[str], 
        max_news_per_keyword: int = 100, 
        sort: str = DEFAULT_SORT
    ) -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, str]]:
        """여러 키워드로 뉴스 검색"""
        results = {}
        errors = {}
        
        for keyword in keywords:
            try:
                news_items = self.search_single_keyword(
                    keyword, max_news_per_keyword, sort
                )
                results[keyword] = news_items
                
            except Exception as e:
                logger.error(f"키워드 '{keyword}' 검색 실패: {str(e)}")
                errors[keyword] = str(e)
                results[keyword] = []
        
        return results, errors
    
    def get_total_count(self, keyword: str) -> Optional[int]:
        """키워드에 대한 전체 뉴스 개수 조회 (첫 번째 요청의 total 값)"""
        try:
            encoded_query = quote(keyword)
            url = f"{NAVER_NEWS_API_URL}?query={encoded_query}&display=1&start=1"
            
            res = requests.get(url, headers=self.headers, timeout=5)
            res.raise_for_status()
            
            data = res.json()
            return data.get("total", 0)
            
        except Exception as e:
            logger.error(f"전체 개수 조회 실패 (키워드: {keyword}): {str(e)}")
            return None
