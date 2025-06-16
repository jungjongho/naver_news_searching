#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""뉴스 데이터 처리 서비스"""

import datetime
from typing import Dict, Any, Optional, List
import logging

from app.utils.constants.api_constants import NAVER_DATE_FORMAT, OUTPUT_DATE_FORMAT
from app.services.data.domain_mapper import domain_mapper

logger = logging.getLogger(__name__)


class NewsProcessor:
    """뉴스 데이터 가공을 담당하는 클래스"""
    
    @staticmethod
    def clean_html_tags(text: str) -> str:
        """HTML 태그 제거"""
        if not text:
            return ""
        
        # 네이버에서 제공하는 굵은 글씨 태그 제거
        return text.replace("<b>", "").replace("</b>", "")
    
    @staticmethod
    def parse_naver_date(date_string: str) -> Optional[datetime.datetime]:
        """네이버 API의 날짜 형식을 datetime 객체로 변환"""
        try:
            return datetime.datetime.strptime(date_string, NAVER_DATE_FORMAT)
        except ValueError as e:
            logger.error(f"날짜 파싱 실패: {date_string}, 오류: {str(e)}")
            return None
    
    @staticmethod
    def format_date_for_output(date_obj: datetime.datetime) -> str:
        """출력용 날짜 형식으로 변환"""
        return date_obj.strftime(OUTPUT_DATE_FORMAT)
    
    @staticmethod
    def is_date_in_range(
        target_date: datetime.datetime,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None
    ) -> bool:
        """날짜가 지정된 범위 내에 있는지 확인"""
        if start_date and target_date < start_date:
            return False
        if end_date and target_date > end_date:
            return False
        return True
    
    @staticmethod
    def process_news_item(
        item: Dict[str, Any], 
        keyword: str,
        news_id: str = None,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """뉴스 아이템 처리"""
        try:
            # 날짜 파싱
            pub_date = NewsProcessor.parse_naver_date(item['pubDate'])
            if not pub_date:
                return None
            
            # 날짜 범위 확인
            if not NewsProcessor.is_date_in_range(pub_date, start_date, end_date):
                return None
            
            # HTML 태그 제거
            title = NewsProcessor.clean_html_tags(item['title'])
            description = NewsProcessor.clean_html_tags(item['description'])
            
            # 원본 링크에서 신문사명 추출
            original_link = item.get('originallink', '')
            source_name = domain_mapper.get_source_from_url(original_link)
            
            return {
                "news_id": news_id,
                "title": title,
                "link": item['link'],
                "pubDate": NewsProcessor.format_date_for_output(pub_date),
                "description": description,
                "source": source_name,
                "originallink": original_link,
                "keyword": keyword
            }
            
        except Exception as e:
            logger.error(f"뉴스 아이템 처리 오류: {str(e)}")
            return None
    
    @staticmethod
    def process_news_items(
        items: List[Dict[str, Any]], 
        keyword: str,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None
    ) -> List[Dict[str, Any]]:
        """뉴스 아이템 목록 처리"""
        processed_items = []
        
        for i, item in enumerate(items, 1):
            # news_id 생성 (news_1, news_2, news_3...)
            news_id = f"news_{i}"
            
            processed_item = NewsProcessor.process_news_item(
                item, keyword, news_id, start_date, end_date
            )
            if processed_item:
                processed_items.append(processed_item)
        
        return processed_items
    
    @staticmethod
    def validate_news_item(item: Dict[str, Any]) -> bool:
        """뉴스 아이템 유효성 검증"""
        required_fields = ['title', 'link', 'pubDate', 'description']
        return all(field in item and item[field] for field in required_fields)
