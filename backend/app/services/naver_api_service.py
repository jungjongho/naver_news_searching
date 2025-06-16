#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import datetime
import os
import logging
import pandas as pd
from urllib.parse import quote, urlparse
from typing import List, Dict, Any, Optional, Tuple

from app.utils.file_utils import save_to_excel
from app.utils.deduplication import deduplicate_by_url
from app.core.config import settings

logger = logging.getLogger(__name__)


class NaverApiService:
    """네이버 뉴스 API 서비스"""
    
    def __init__(self):
        self._validate_api_keys()
        self._setup_headers()
        self._ensure_results_directory()
        self.domain_to_source = self._load_domain_mapping()
    
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
    
    def _ensure_results_directory(self):
        """결과 저장 디렉토리 확인 및 생성"""
        os.makedirs(settings.CRAWLING_RESULTS_PATH, exist_ok=True)
    
    def _load_domain_mapping(self) -> Dict[str, str]:
        """도메인-신문사 매핑 테이블 로드"""
        try:
            csv_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                'domain_to_source.csv'
            )
            
            if not os.path.exists(csv_path):
                logger.warning(f"domain_to_source.csv 파일을 찾을 수 없습니다: {csv_path}")
                return {}
            
            df = pd.read_csv(csv_path, encoding='utf-8')
            
            if 'domain' not in df.columns or 'source' not in df.columns:
                logger.error("CSV 파일에 'domain' 또는 'source' 컬럼이 없습니다.")
                return {}
            
            domain_mapping = df.set_index('domain')['source'].to_dict()
            logger.info(f"도메인-신문사 매핑 테이블 로드 완료: {len(domain_mapping)}개 항목")
            return domain_mapping
            
        except Exception as e:
            logger.error(f"domain_to_source.csv 파일 로드 중 오류 발생: {str(e)}")
            return {}
    
    def _extract_domain_from_url(self, url: str) -> str:
        """URL에서 도메인 추출"""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            if domain.startswith('www.'):
                domain = domain[4:]
            
            domain_parts = domain.split('.')
            return domain_parts[0] if domain_parts else domain
            
        except Exception as e:
            logger.error(f"URL에서 도메인 추출 실패: {url}, 오류: {str(e)}")
            return ""
    
    def _get_source_from_url(self, url: str) -> Optional[str]:
        """URL을 기반으로 신문사명 조회"""
        if not url:
            return None
        
        domain = self._extract_domain_from_url(url)
        return self.domain_to_source.get(domain) if domain else None
    
    def _process_news_item(self, item: Dict[str, Any], keyword: str, news_id: str = None, start_date: datetime.datetime = None, end_date: datetime.datetime = None) -> Optional[Dict[str, Any]]:
        """뉴스 아이템 처리"""
        try:
            pub_date = datetime.datetime.strptime(item['pubDate'], "%a, %d %b %Y %H:%M:%S +0900")
            
            # 날짜 필터링 체크
            if start_date and pub_date < start_date:
                return None
            if end_date and pub_date > end_date:
                return None
                
            title = item['title'].replace("<b>", "").replace("</b>", "")
            description = item['description'].replace("<b>", "").replace("</b>", "")
            original_link = item.get('originallink', '')
            source_name = self._get_source_from_url(original_link)
            
            return {
                "news_id": news_id,
                "title": title,
                "link": item['link'],
                "pubDate": pub_date.strftime("%Y-%m-%d %H:%M:%S"),
                "description": description,
                "source": source_name,
                "originallink": original_link,
                "keyword": keyword
            }
            
        except Exception as e:
            logger.error(f"뉴스 아이템 처리 오류: {str(e)}")
            return None
    
    def search_news(self, keyword: str, max_news: int = 100, sort: str = "date", days: int = 30, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """특정 키워드에 대한 네이버 뉴스 검색"""
        logger.info(f"Searching news for keyword: {keyword}")
        
        # 날짜 범위 설정
        start_date_obj = None
        end_date_obj = None
        
        if start_date:
            try:
                start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                logger.warning(f"잘못된 시작 날짜 형식: {start_date}")
        
        if end_date:
            try:
                end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d")
                # 종료 날짜를 하루의 끝으로 설정 (23:59:59)
                end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59)
            except ValueError:
                logger.warning(f"잘못된 종료 날짜 형식: {end_date}")
        
        # 날짜 범위가 설정되지 않았으면 days 파라미터 사용
        if not start_date_obj and not end_date_obj:
            today = datetime.datetime.now()
            start_date_obj = today - datetime.timedelta(days=days)
        
        encoded_query = quote(keyword)
        all_news = []
        
        display = min(100, max_news)
        
        for start in range(1, min(1001, max_news + 1), display):
            remaining = max_news - len(all_news)
            if remaining <= 0:
                break
            
            current_display = min(display, remaining)
            url = f"https://openapi.naver.com/v1/search/news.json?query={encoded_query}&display={current_display}&start={start}&sort={sort}"
            
            try:
                res = requests.get(url, headers=self.headers)
                res.raise_for_status()
                
                items = res.json().get("items", [])
                if not items:
                    break
                
                for idx, item in enumerate(items):
                    # news_id 생성: 전체 인덱스 기준
                    news_id = f"news_{len(all_news) + 1}"
                    
                    processed_item = self._process_news_item(item, keyword, news_id, start_date_obj, end_date_obj)
                    if processed_item:
                        all_news.append(processed_item)
                    elif processed_item is None and 'pubDate' in item:
                        # 날짜 범위를 벗어났으면 검색 종료 (정렬이 날짜순인 경우)
                        if sort == "date":
                            break
                
                if len(items) < current_display or len(all_news) >= max_news:
                    break
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"API 요청 오류: {str(e)}")
                break
        
        logger.info(f"Found {len(all_news)} news items for keyword: {keyword}")
        return all_news
    
    def search_keywords(self, keywords: List[str], max_news_per_keyword: int = 100, 
                       sort: str = "date", days: int = 30, start_date: str = None, end_date: str = None) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """여러 키워드에 대한 뉴스 검색"""
        all_news_items = []
        errors = {}
        
        for keyword in keywords:
            try:
                news_items = self.search_news(keyword, max_news_per_keyword, sort, days, start_date, end_date)
                all_news_items.extend(news_items)
            except Exception as e:
                logger.error(f"키워드 '{keyword}' 검색 오류: {str(e)}")
                errors[keyword] = str(e)
        
        if all_news_items:
            all_news_items = deduplicate_by_url(all_news_items)
            
            # 중복 제거 후 news_id 재생성
            for i, item in enumerate(all_news_items, 1):
                item["news_id"] = f"news_{i}"
        
        logger.info(f"중복 제거 후 총 뉴스 개수: {len(all_news_items)}")
        return all_news_items, errors
    
    def _format_keywords_for_filename(self, keywords: List[str]) -> str:
        """키워드 목록을 파일명에 적합한 형식으로 변환"""
        if len(keywords) > 3:
            keywords_str = '_'.join(keywords[:3]) + f"_and_{len(keywords)-3}_more"
        else:
            keywords_str = '_'.join(keywords)
        
        # 파일명 특수문자 제거 및 길이 제한
        keywords_str = keywords_str.replace(' ', '_').replace('/', '_').replace('\\', '_')
        return keywords_str[:97] + '...' if len(keywords_str) > 100 else keywords_str
    
    def save_results(self, news_items: List[Dict[str, Any]], keywords: List[str]) -> Tuple[Optional[str], Optional[str]]:
        """검색 결과를 Excel 파일로 저장"""
        if not news_items:
            logger.warning("저장할 뉴스 아이템이 없습니다")
            return None, None
        
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            keywords_str = self._format_keywords_for_filename(keywords)
            
            file_name = f"naver_news_{keywords_str}_{timestamp}.xlsx"
            file_path = os.path.join(settings.CRAWLING_RESULTS_PATH, file_name)
            
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
