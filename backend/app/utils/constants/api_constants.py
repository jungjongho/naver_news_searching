#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""API 관련 상수 정의"""

# 네이버 API 설정
NAVER_NEWS_API_URL = "https://openapi.naver.com/v1/search/news.json"
MAX_DISPLAY_PER_REQUEST = 100  # 네이버 API 한 번에 최대 요청 가능한 개수
MAX_START_INDEX = 1001  # 네이버 API 최대 시작 인덱스
MAX_NEWS_PER_KEYWORD = 1000  # 키워드당 최대 뉴스 개수

# 정렬 옵션
SORT_OPTIONS = {
    "date": "date",      # 날짜순
    "sim": "sim"         # 정확도순
}

# 날짜 형식
NAVER_DATE_FORMAT = "%a, %d %b %Y %H:%M:%S +0900"
OUTPUT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 기본값
DEFAULT_DAYS = 30
DEFAULT_MAX_NEWS = 100
DEFAULT_SORT = "date"
