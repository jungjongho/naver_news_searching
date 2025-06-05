#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
공통 예외 클래스 정의
"""

class NewsSearchException(Exception):
    """뉴스 검색 서비스 기본 예외"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class APIKeyError(NewsSearchException):
    """API 키 관련 예외"""
    def __init__(self, message: str = "API 키가 유효하지 않습니다"):
        super().__init__(message, "API_KEY_ERROR")


class FileNotFoundError(NewsSearchException):
    """파일을 찾을 수 없는 예외"""
    def __init__(self, file_path: str):
        message = f"파일을 찾을 수 없습니다: {file_path}"
        super().__init__(message, "FILE_NOT_FOUND")


class FileProcessingError(NewsSearchException):
    """파일 처리 관련 예외"""
    def __init__(self, message: str):
        super().__init__(message, "FILE_PROCESSING_ERROR")


class AnalysisError(NewsSearchException):
    """분석 관련 예외"""
    def __init__(self, message: str):
        super().__init__(message, "ANALYSIS_ERROR")


class CrawlingError(NewsSearchException):
    """크롤링 관련 예외"""
    def __init__(self, message: str):
        super().__init__(message, "CRAWLING_ERROR")


class ValidationError(NewsSearchException):
    """검증 관련 예외"""
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")
