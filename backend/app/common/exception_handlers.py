#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
전역 예외 핸들러
"""

import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from app.common.exceptions import NewsSearchException

logger = logging.getLogger(__name__)


async def news_search_exception_handler(request: Request, exc: NewsSearchException):
    """NewsSearchException 핸들러"""
    logger.error(f"Business logic error: {exc.message}")
    
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "message": exc.message,
            "error_code": exc.error_code
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 핸들러"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "서버 내부 오류가 발생했습니다.",
            "error_code": "INTERNAL_SERVER_ERROR"
        }
    )
