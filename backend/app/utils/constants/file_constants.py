#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""파일 관련 상수 정의"""

# 파일 확장자
EXCEL_EXTENSION = ".xlsx"
CSV_EXTENSION = ".csv"

# 파일명 패턴
NEWS_FILE_PREFIX = "naver_news"
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

# 파일명 제한
MAX_FILENAME_LENGTH = 100
FILENAME_TRUNCATE_SUFFIX = "..."

# 파일 구조 관련
DOMAIN_MAPPING_FILE = "domain_to_source.csv"
REQUIRED_CSV_COLUMNS = ["domain", "source"]

# Excel 관련
DEFAULT_SHEET_NAME = "뉴스목록"
EXCEL_COLUMNS = [
    "title", "link", "pubDate", "description", 
    "source", "originallink", "keyword"
]
