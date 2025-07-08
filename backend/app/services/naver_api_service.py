#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import datetime
import os
import logging
import pandas as pd
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from urllib.parse import quote, urlparse
from typing import List, Dict, Any, Optional, Tuple

from app.utils.file_utils import save_to_excel
from app.utils.deduplication import deduplicate_by_url
from app.core.config import settings

# SSL 경고 비활성화
urllib3.disable_warnings(InsecureRequestWarning)

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
    
    def _extract_main_domain_from_url(self, url: str) -> str:
        """URL에서 메인 도메인 추출 (프로토콜 포함)"""
        try:
            if not url:
                return ""
            
            parsed_url = urlparse(url)
            
            # 프로토콜과 도메인 결합
            if parsed_url.scheme and parsed_url.netloc:
                return f"{parsed_url.scheme}://{parsed_url.netloc}"
            else:
                return ""
                
        except Exception as e:
            logger.error(f"URL에서 메인 도메인 추출 실패: {url}, 오류: {str(e)}")
            return ""
    
    def _extract_domain_from_url(self, url: str) -> str:
        """URL에서 도메인 추출 (신문사명 매핑용)"""
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
            main_domain = self._extract_main_domain_from_url(original_link)  # 메인 도메인 추출
            
            return {
                "keyword": keyword,
                "source": main_domain,  # 메인 도메인
                "title": title,
                "description": description,
                "news_id": news_id,
                "link": item['link'],
                "pubDate": pub_date.strftime("%Y-%m-%d %H:%M:%S"),
                "source_name": source_name,  # 기존 신문사명
                "originallink": original_link  # originallink를 마지막으로 이동
            }
            
        except Exception as e:
            logger.error(f"뉴스 아이템 처리 오류: {str(e)}")
            return None
    
    def search_news(self, keyword: str, max_news: int = 100, sort: str = "date", days: int = 30, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """특정 키워드에 대한 네이버 뉴스 검색 - 개선된 버전"""
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
        consecutive_failures = 0
        max_consecutive_failures = 3  # 연속 실패 허용 횟수
        
        display = min(100, max_news)
        
        for start in range(1, min(1001, max_news + 1), display):
            remaining = max_news - len(all_news)
            if remaining <= 0:
                break
            
            current_display = min(display, remaining)
            url = f"https://openapi.naver.com/v1/search/news.json?query={encoded_query}&display={current_display}&start={start}&sort={sort}"
            
            try:
                # SSL 검증 비활성화로 요청
                res = requests.get(
                    url, 
                    headers=self.headers, 
                    timeout=15,
                    verify=False,  # SSL 검증 비활성화
                    allow_redirects=True
                )
                res.raise_for_status()
                
                response_data = res.json()
                items = response_data.get("items", [])
                
                logger.debug(f"키워드 '{keyword}': start={start}, 요청={current_display}개, 응답={len(items)}개")
                
                if not items:
                    logger.info(f"키워드 '{keyword}': start={start}에서 더 이상 결과 없음")
                    break
                
                consecutive_failures = 0  # 성공하면 실패 카운터 리셋
                
                for idx, item in enumerate(items):
                    # news_id 생성: 전체 인덱스 기준
                    news_id = f"news_{len(all_news) + 1}"
                    
                    processed_item = self._process_news_item(item, keyword, news_id, start_date_obj, end_date_obj)
                    if processed_item:
                        all_news.append(processed_item)
                    elif processed_item is None and 'pubDate' in item:
                        # 날짜 범위를 벗어났으면 검색 종료 (정렬이 날짜순인 경우)
                        if sort == "date":
                            logger.info(f"키워드 '{keyword}': 날짜 범위 초과로 검색 종료")
                            break
                
                # API 응답이 요청한 것보다 적으면 더 이상 결과가 없는 것
                if len(items) < current_display:
                    logger.info(f"키워드 '{keyword}': API 응답 부족 (요청: {current_display}, 응답: {len(items)})")
                    break
                    
                # 목표 개수에 도달했으면 종료
                if len(all_news) >= max_news:
                    logger.info(f"키워드 '{keyword}': 목표 개수 도달 ({len(all_news)}/{max_news})")
                    break
                    
            except requests.exceptions.Timeout:
                consecutive_failures += 1
                logger.warning(f"키워드 '{keyword}': 타임아웃 발생 (start={start}), 재시도 중... ({consecutive_failures}/{max_consecutive_failures})")
                if consecutive_failures >= max_consecutive_failures:
                    logger.error(f"키워드 '{keyword}': 연속 타임아웃으로 검색 중단")
                    break
                continue  # 타임아웃은 재시도
                
            except requests.exceptions.RequestException as e:
                consecutive_failures += 1
                logger.warning(f"키워드 '{keyword}': API 요청 오류 (start={start}): {str(e)} ({consecutive_failures}/{max_consecutive_failures})")
                if consecutive_failures >= max_consecutive_failures:
                    logger.error(f"키워드 '{keyword}': 연속 실패로 검색 중단")
                    break
                continue  # 일반적인 요청 오류도 재시도
                
            except Exception as e:
                logger.error(f"키워드 '{keyword}': 예상치 못한 오류 (start={start}): {str(e)}")
                break  # 예상치 못한 오류는 바로 중단
        
        logger.info(f"키워드 '{keyword}': 총 {len(all_news)}개 뉴스 수집 완료")
        return all_news
    
    def search_keywords(self, keywords: List[str], max_news_per_keyword: int = 100, 
                       sort: str = "date", days: int = 30, start_date: str = None, end_date: str = None) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """여러 키워드에 대한 뉴스 검색 - 개선된 버전"""
        all_news_items = []
        errors = {}
        
        logger.info(f"총 {len(keywords)}개 키워드 검색 시작: {keywords}")
        logger.info(f"키워드당 최대 개수: {max_news_per_keyword}, 정렬: {sort}")
        
        for i, keyword in enumerate(keywords, 1):
            logger.info(f"[{i}/{len(keywords)}] 키워드 '{keyword}' 검색 시작...")
            try:
                news_items = self.search_news(keyword, max_news_per_keyword, sort, days, start_date, end_date)
                logger.info(f"[{i}/{len(keywords)}] 키워드 '{keyword}': {len(news_items)}개 뉴스 수집")
                
                if news_items:
                    all_news_items.extend(news_items)
                else:
                    logger.warning(f"[{i}/{len(keywords)}] 키워드 '{keyword}': 검색 결과 없음")
                    
            except Exception as e:
                logger.error(f"[{i}/{len(keywords)}] 키워드 '{keyword}' 검색 오류: {str(e)}")
                errors[keyword] = str(e)
        
        logger.info(f"전체 검색 완료 - 중복 제거 전 총 {len(all_news_items)}개 뉴스")
        
        if all_news_items:
            # 중복 제거 전 각 키워드별 통계 로깅
            keyword_stats = {}
            for item in all_news_items:
                keyword = item.get('keyword', '마암')
                keyword_stats[keyword] = keyword_stats.get(keyword, 0) + 1
            
            for keyword, count in keyword_stats.items():
                logger.info(f"키워드 '{keyword}': {count}개 뉴스")
            
            # 중복 제거 실행
            original_count = len(all_news_items)
            all_news_items = deduplicate_by_url(all_news_items)
            removed_count = original_count - len(all_news_items)
            
            logger.info(f"중복 제거 완료: {removed_count}개 중복 제거, 최종 {len(all_news_items)}개 뉴스")
            
            # 중복 제거 후 news_id 재생성
            for i, item in enumerate(all_news_items, 1):
                item["news_id"] = f"news_{i}"
        else:
            logger.warning("모든 키워드에서 검색 결과가 없습니다.")
        
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
