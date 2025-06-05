#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
공통 응답 유틸리티
"""

from typing import Dict, Any, Optional
from fastapi.responses import JSONResponse
from app.common.exceptions import NewsSearchException


class ResponseFormatter:
    """표준화된 응답 포맷터"""
    
    @staticmethod
    def success(
        message: str,
        data: Optional[Dict[str, Any]] = None,
        status_code: int = 200
    ) -> JSONResponse:
        """성공 응답 생성"""
        response_data = {
            "success": True,
            "message": message
        }
        
        if data:
            response_data.update(data)
            
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    
    @staticmethod
    def error(
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 400
    ) -> JSONResponse:
        """에러 응답 생성"""
        response_data = {
            "success": False,
            "message": message
        }
        
        if error_code:
            response_data["error_code"] = error_code
            
        if details:
            response_data["errors"] = details
            
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    
    @staticmethod
    def from_exception(exception: NewsSearchException, status_code: int = 400) -> JSONResponse:
        """예외로부터 에러 응답 생성"""
        return ResponseFormatter.error(
            message=exception.message,
            error_code=exception.error_code,
            status_code=status_code
        )


def create_progress_response(
    current: int,
    total: int,
    stage: str,
    stats: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """진행상황 응답 생성"""
    response = {
        "current": current,
        "total": total,
        "stage": stage,
        "progress_percent": round((current / total * 100), 1) if total > 0 else 0
    }
    
    if stats:
        response["stats"] = stats
        
    if session_id:
        response["session_id"] = session_id
        
    return response
