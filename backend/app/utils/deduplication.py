#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

def deduplicate_by_url(news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    URL 기반으로 뉴스 아이템 중복 제거
    
    Args:
        news_items: 뉴스 아이템 목록
        
    Returns:
        중복 제거된 뉴스 아이템 목록
    """
    logger.info(f"Deduplicating {len(news_items)} news items by URL")
    
    # URL을 키로 사용하여 중복 제거
    unique_items = {}
    url_field = 'link' if 'link' in news_items[0] else 'url'
    
    for item in news_items:
        url = item.get(url_field, '')
        
        # URL이 있고 이미 처리되지 않은 경우에만 추가
        if url and url not in unique_items:
            unique_items[url] = item
    
    result = list(unique_items.values())
    logger.info(f"Deduplicated to {len(result)} news items")
    return result
