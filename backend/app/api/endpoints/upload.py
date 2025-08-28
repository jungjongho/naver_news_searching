#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
파일 업로드 API 엔드포인트
"""

import logging
import os
import tempfile
import pandas as pd
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from typing import List
from app.dependencies.auth import get_current_active_user
from app.db.models import User
from app.core.config import settings
from app.core.file_manager import file_manager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/upload",
    tags=["upload"],
    responses={404: {"description": "Not found"}},
)

# 허용할 파일 확장자
ALLOWED_EXTENSIONS = {'.xlsx', '.xls', '.csv'}
# 최대 파일 크기 (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

def validate_excel_file(file_path: str) -> dict:
    """
    업로드된 엑셀 파일의 구조 검증
    중복 제거, 관련성 평가에 필요한 열들이 있는지 확인
    """
    try:
        # 파일 읽기
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, encoding='utf-8')
        else:
            df = pd.read_excel(file_path)
        
        # 필수 열 확인
        required_columns = ['title', 'url', 'date', 'content']
        missing_columns = []
        
        for col in required_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        # 추가로 확인할 수 있는 선택적 열들
        optional_columns = ['source', 'keyword', 'is_relevant', 'category']
        available_optional = [col for col in optional_columns if col in df.columns]
        
        return {
            'is_valid': len(missing_columns) == 0,
            'row_count': len(df),
            'columns': list(df.columns),
            'missing_columns': missing_columns,
            'required_columns': required_columns,
            'available_optional_columns': available_optional,
            'sample_data': df.head(3).to_dict('records') if len(df) > 0 else []
        }
        
    except Exception as e:
        return {
            'is_valid': False,
            'error': f'파일 읽기 오류: {str(e)}',
            'row_count': 0,
            'columns': [],
            'missing_columns': required_columns,
            'required_columns': required_columns
        }

@router.post("/excel")
async def upload_excel_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    엑셀 파일 업로드 및 검증
    중복 제거나 관련성 평가에 사용할 파일을 업로드합니다.
    """
    # 파일 확장자 검증
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다. 허용 형식: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # 파일 크기 검증
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"파일 크기가 너무 큽니다. 최대 {MAX_FILE_SIZE // (1024*1024)}MB까지 허용됩니다."
        )
    
    try:
        # 안전한 파일명 생성
        safe_filename = f"uploaded_{current_user.id}_{int(time.time())}_{file.filename}"
        
        # 임시 저장소에 파일 저장
        upload_dir = os.path.join(settings.RESULTS_PATH, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, safe_filename)
        
        # 파일 저장
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # 파일 구조 검증
        validation_result = validate_excel_file(file_path)
        
        if not validation_result['is_valid']:
            # 검증 실패시 파일 삭제
            os.remove(file_path)
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "업로드된 파일의 형식이 올바르지 않습니다.",
                    "validation_result": validation_result
                }
            )
        
        # 성공적으로 업로드됨
        logger.info(f"사용자 {current_user.email}이 파일 업로드: {safe_filename}")
        
        return {
            "success": True,
            "message": "파일이 성공적으로 업로드되었습니다.",
            "file_path": file_path,
            "original_filename": file.filename,
            "safe_filename": safe_filename,
            "validation_result": validation_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # 오류 발생시 파일이 있다면 삭제
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        
        logger.error(f"파일 업로드 중 오류: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"파일 업로드 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/validation-requirements")
async def get_validation_requirements():
    """
    업로드 파일 검증 요구사항 정보 제공
    """
    return {
        "required_columns": [
            {"name": "title", "description": "뉴스 제목", "example": "삼성전자, 새로운 스마트폰 출시"},
            {"name": "url", "description": "뉴스 URL", "example": "https://news.naver.com/..."},
            {"name": "date", "description": "발행 날짜", "example": "2025-01-15"},
            {"name": "content", "description": "뉴스 내용", "example": "삼성전자가 신제품을 발표했다..."}
        ],
        "optional_columns": [
            {"name": "source", "description": "뉴스 출처", "example": "한국경제"},
            {"name": "keyword", "description": "검색 키워드", "example": "삼성전자"},
            {"name": "is_relevant", "description": "관련성 여부", "example": "true"},
            {"name": "category", "description": "카테고리", "example": "자사언급기사"}
        ],
        "file_formats": list(ALLOWED_EXTENSIONS),
        "max_file_size_mb": MAX_FILE_SIZE // (1024*1024),
        "encoding": "UTF-8 권장"
    }