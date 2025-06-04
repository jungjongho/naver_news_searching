#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fastapi import APIRouter, HTTPException, Response
from typing import List, Dict, Any, Optional
import logging
import os
import mimetypes
from urllib.parse import quote

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/download",
    tags=["download"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{file_name}")
async def download_file(file_name: str):
    """
    파일 다운로드
    """
    # 파일 경로 찾기
    file_path = None
    for search_path in [settings.CRAWLING_RESULTS_PATH, settings.RELEVANCE_RESULTS_PATH, settings.RESULTS_PATH]:
        potential_path = os.path.join(search_path, file_name)
        if os.path.exists(potential_path):
            file_path = potential_path
            break
    
    if not file_path:
        raise HTTPException(status_code=404, detail=f"File '{file_name}' not found")
    
    try:
        # 파일 확장자에 따른 MIME 타입 결정
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            # 기본 MIME 타입
            if file_name.endswith('.xlsx'):
                content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            else:
                content_type = 'application/octet-stream'
        
        # 파일 읽기
        with open(file_path, 'rb') as file:
            file_content = file.read()
        
        # 파일 다운로드를 위한 헤더 설정 (한글 파일명 인코딩)
        encoded_filename = quote(file_name, safe='')
        headers = {
            'Content-Disposition': f'attachment; filename*=UTF-8\'\'{encoded_filename}',
            'Content-Type': content_type
        }
        
        return Response(
            content=file_content,
            headers=headers
        )
        
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")
