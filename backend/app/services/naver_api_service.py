#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import datetime
from urllib.parse import quote, urlparse
import os
import logging
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple

from app.utils.file_utils import save_to_csv, save_to_excel
from app.utils.deduplication import deduplicate_by_url
from app.core.config import settings

logger = logging.getLogger(__name__)

class NaverApiService:
    """
    네이버 뉴스 API 서비스
    """
    def __init__(self):
        """
        서비스 초기화
        """
        self.client_id = settings.NAVER_CLIENT_ID
        self.client_secret = settings.NAVER_CLIENT_SECRET
        self.headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }
        
        # API 키 검증
        if not self.client_id or not self.client_secret:
            logger.error("Naver API keys are not set")
            raise ValueError("NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET이 설정되어 있지 않습니다.")
        
        # 결과 저장 디렉토리 확인 및 생성
        os.makedirs(settings.CRAWLING_RESULTS_PATH, exist_ok=True)
        
        # domain_to_source 매핑 테이블 로드
        self.domain_to_source = self._load_domain_to_source_mapping()
    
    def _load_domain_to_source_mapping(self) -> Dict[str, str]:
        """
        domain_to_source.csv 파일을 로드하여 도메인-신문사 매핑 테이블을 생성
        
        Returns:
            도메인을 키로, 신문사명을 값으로 하는 딕셔너리
        """
        try:
            # CSV 파일 경로 (backend 폴더의 domain_to_source.csv)
            csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'domain_to_source.csv')
            
            if not os.path.exists(csv_path):
                logger.warning(f"domain_to_source.csv 파일을 찾을 수 없습니다: {csv_path}")
                return {}
            
            # CSV 파일 읽기
            df = pd.read_csv(csv_path, encoding='utf-8')
            
            # domain과 source 컬럼이 있는지 확인
            if 'domain' not in df.columns or 'source' not in df.columns:
                logger.error("CSV 파일에 'domain' 또는 'source' 컬럼이 없습니다.")
                return {}
            
            # 딕셔너리로 변환
            domain_mapping = df.set_index('domain')['source'].to_dict()
            logger.info(f"도메인-신문사 매핑 테이블 로드 완료: {len(domain_mapping)}개 항목")
            
            return domain_mapping
            
        except Exception as e:
            logger.error(f"domain_to_source.csv 파일 로드 중 오류 발생: {str(e)}")
            return {}
    
    def _extract_domain_from_url(self, url: str) -> str:
        """
        URL에서 도메인 추출
        
        Args:
            url: 뉴스 기사 URL
            
        Returns:
            추출된 도메인명 (예: naver.com에서 naver 부분)
        """
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # www. 제거
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # 도메인에서 첫 번째 부분만 추출 (예: news.naver.com -> news)
            domain_parts = domain.split('.')
            if len(domain_parts) > 0:
                return domain_parts[0]
            
            return domain
            
        except Exception as e:
            logger.error(f"URL에서 도메인 추출 실패: {url}, 오류: {str(e)}")
            return ""
    
    def _get_source_from_url(self, url: str) -> Optional[str]:
        """
        URL을 기반으로 신문사명 조회
        
        Args:
            url: 뉴스 기사 URL
            
        Returns:
            신문사명 또는 None (매핑이 없는 경우)
        """
        if not url:
            return None
        
        domain = self._extract_domain_from_url(url)
        
        if not domain:
            return None
        
        # 도메인-신문사 매핑에서 조회
        return self.domain_to_source.get(domain)
    
    def search_news(self, keyword: str, max_news: int = 100, sort: str = "date", days: int = 30) -> List[Dict[str, Any]]:
        """
        특정 키워드에 대한 네이버 뉴스 API 검색
        
        Args:
            keyword: 검색 키워드
            max_news: 최대 뉴스 건수 (기본값: 100)
            sort: 정렬 방식 (date: 최신순, sim: 정확도순)
            days: 최근 몇 일간의 뉴스를 검색할지 (기본값: 30일)
            
        Returns:
            검색한 뉴스 아이템 목록
        """
        logger.info(f"Searching news for keyword: {keyword}, max_news: {max_news}, sort: {sort}, days: {days}")
        
        # 검색 조건 설정
        today = datetime.datetime.now()
        days_ago = today - datetime.timedelta(days=days)
        
        # 인코딩된 키워드
        encoded_query = quote(keyword)
        
        all_news = []
        
        # API 응답에 대한 페이지당 최대 항목 수 (네이버 API는 100이 최대)
        display = min(100, max_news)
        
        # 페이지 번호 시작은 1, 최대 1000건까지 검색 가능
        for start in range(1, min(1001, max_news + 1), display):
            # 남은 가져올 아이템 수 계산
            remaining = max_news - len(all_news)
            if remaining <= 0:
                break
            
            # 페이지당 가져올 아이템 수 조정 (마지막 페이지일 경우)
            current_display = min(display, remaining)
            
            # API URL 구성
            url = f"https://openapi.naver.com/v1/search/news.json?query={encoded_query}&display={current_display}&start={start}&sort={sort}"
            
            try:
                # API 요청
                res = requests.get(url, headers=self.headers)
                res.raise_for_status()  # HTTP 오류 확인
                
                data = res.json()
                items = data.get("items", [])
                
                # 빈 결과면 종료
                if not items:
                    logger.info(f"No more news items found for keyword: {keyword} at start: {start}")
                    break
                
                # 각 뉴스 항목 처리
                for item in items:
                    try:
                        # 날짜 파싱 및 필터링
                        pub_date = datetime.datetime.strptime(item['pubDate'], "%a, %d %b %Y %H:%M:%S +0900")
                        
                        # 지정된 날짜 이내인지 확인
                        if pub_date >= days_ago:
                            # HTML 태그 제거
                            title = item['title'].replace("<b>", "").replace("</b>", "")
                            description = item['description'].replace("<b>", "").replace("</b>", "")
                            
                            # 원본 링크에서 신문사 정보 추출
                            original_link = item.get('originallink', '')
                            source_name = self._get_source_from_url(original_link)
                            
                            # 아이템에 키워드 정보와 신문사 정보 추가
                            item_with_keyword = {
                                "title": title,
                                "link": item['link'],
                                "pubDate": pub_date.strftime("%Y-%m-%d %H:%M:%S"),
                                "description": description,
                                "source": source_name,  # 신문사명 (매핑이 없으면 None)
                                "originallink": original_link,
                                "keyword": keyword
                            }
                            
                            all_news.append(item_with_keyword)
                        else:
                            # 지정된 날짜 이전 뉴스가 나오기 시작하면 종료
                            logger.info(f"Reached news older than {days} days for keyword: {keyword}")
                            break
                            
                    except Exception as e:
                        logger.error(f"Error processing news item: {str(e)}")
                        continue
                
                # 페이지당 아이템 수가 요청한 것보다 적으면 더 이상 결과가 없음
                if len(items) < current_display:
                    logger.info(f"No more pages available for keyword: {keyword}")
                    break
                
                # 최대 뉴스 수 도달 시 종료
                if len(all_news) >= max_news:
                    break
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"API request error for keyword {keyword}: {str(e)}")
                break
            
        logger.info(f"Found {len(all_news)} news items for keyword: {keyword}")
        return all_news
    
    def search_keywords(self, keywords: List[str], max_news_per_keyword: int = 100, sort: str = "date", days: int = 30) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """
        여러 키워드에 대한 뉴스 검색
        
        Args:
            keywords: 검색 키워드 목록
            max_news_per_keyword: 키워드당 최대 뉴스 건수 (기본값: 100)
            sort: 정렬 방식 (date: 최신순, sim: 정확도순)
            days: 최근 몇 일간의 뉴스를 검색할지 (기본값: 30일)
            
        Returns:
            (검색한 뉴스 아이템 목록, 오류 정보)
        """
        all_news_items = []
        errors = {}
        
        for keyword in keywords:
            try:
                news_items = self.search_news(
                    keyword, 
                    max_news=max_news_per_keyword,
                    sort=sort,
                    days=days
                )
                all_news_items.extend(news_items)
            except Exception as e:
                logger.error(f"Error searching keyword '{keyword}': {str(e)}")
                errors[keyword] = str(e)
        
        # URL 기반 중복 제거
        if all_news_items:
            all_news_items = deduplicate_by_url(all_news_items)
        
        logger.info(f"Total news items after deduplication: {len(all_news_items)}")
        return all_news_items, errors
    
    def _format_keywords_for_filename(self, keywords: List[str]) -> str:
        """
        키워드 목록을 파일명에 적합한 형식으로 변환
        
        Args:
            keywords: 키워드 목록
            
        Returns:
            파일명에 사용할 키워드 문자열
        """
        if len(keywords) > 3:
            # 3개 이상이면 처음 3개만 유지하고 나머지는 개수 표시
            keywords_str = '_'.join(keywords[:3]) + f"_and_{len(keywords)-3}_more"
        else:
            # 3개 이하면 모두 포함
            keywords_str = '_'.join(keywords)
        
        # 파일명에 사용할 수 없는 문자 제거
        keywords_str = keywords_str.replace(' ', '_').replace('/', '_').replace('\\', '_')
        
        # 최대 길이 제한
        if len(keywords_str) > 100:
            keywords_str = keywords_str[:97] + '...'
        
        return keywords_str
    
    def save_results(self, news_items: List[Dict[str, Any]], keywords: List[str]) -> Tuple[Optional[str], Optional[str]]:
        """
        검색 결과를 CSV 파일로 저장
        
        Args:
            news_items: 저장할 뉴스 아이템 목록
            keywords: 검색 키워드 목록
            
        Returns:
            (저장된 파일 경로, 다운로드 폴더에 저장된 파일 경로) 또는 오류 시 (None, None)
        """
        if not news_items:
            logger.warning("No news items to save")
            return None, None
        
        try:
            # 파일명 생성 (키워드와 현재 시간 포함)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            keywords_str = self._format_keywords_for_filename(keywords)
            
            file_name = f"naver_news_{keywords_str}_{timestamp}.xlsx"
            file_path = os.path.join(settings.CRAWLING_RESULTS_PATH, file_name)
            
            # Excel 파일로 저장 (다운로드 폴더에도 복사)
            success, download_path = save_to_excel(
                news_items, 
                file_path, 
                copy_to_download=settings.AUTO_COPY_TO_DOWNLOADS,
                download_path=settings.USER_DOWNLOAD_PATH
            )
            
            if success:
                if download_path:
                    logger.info(f"Saved {len(news_items)} news items to {file_path} and copied to {download_path}")
                else:
                    logger.info(f"Saved {len(news_items)} news items to {file_path}")
                return file_path, download_path
            else:
                logger.error("Failed to save results")
                return None, None
        
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            return None, None
