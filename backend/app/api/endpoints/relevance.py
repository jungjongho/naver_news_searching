#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
import logging
import os
import pandas as pd

from app.models.schemas import RelevanceRequest, RelevanceResponse
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/relevance",
    tags=["relevance"],
    responses={404: {"description": "Not found"}},
)

@router.post("/analyze", response_model=RelevanceResponse)
async def analyze_relevance(
    request: RelevanceRequest,
    background_tasks: BackgroundTasks
):
    """
    뉴스 기사 관련성 분석 (이 부분은 대체 코드로, 실제 프로젝트에서는 외부 LLM을 사용해 구현 필요)
    """
    logger.info(f"Analyzing relevance for file: {request.file_path}")
    
    try:
        file_path = os.path.join(settings.RESULTS_PATH, request.file_path)
        
        if not os.path.exists(file_path):
            return RelevanceResponse(
                success=False,
                message=f"파일을 찾을 수 없습니다: {request.file_path}",
                errors={"file_error": "File not found"}
            )
        
        # 참고: 실제 구현에서는 여기서 LLM API를 호출하여 관련성 분석을 수행해야 합니다.
        # 현재는 간단한 샘플 구현으로 대체합니다.
        
        # 데이터 로드 (CSV 또는 Excel)
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, encoding='utf-8-sig')
        else:  # .xlsx
            df = pd.read_excel(file_path, engine='openpyxl')
        
        # 모든 뉴스 항목을 관련 있음으로 표시 (샘플 구현)
        total_items = len(df)
        
        # 새 결과 파일 생성
        file_name = os.path.basename(file_path)
        base_name, ext = os.path.splitext(file_name)
        result_file_name = f"{base_name}_analyzed{ext}"
        result_file_path = os.path.join(settings.RESULTS_PATH, result_file_name)
        
        # 관련성 열 추가 (샘플 구현)
        df['is_relevant'] = True
        df['relevance_reason'] = "자동 분석에 의한 관련성 확인"
        df['category'] = "일반"
        
        # 결과 파일 저장
        if ext.lower() == '.csv':
            df.to_csv(result_file_path, index=False, encoding='utf-8-sig')
        else:  # .xlsx
            df.to_excel(result_file_path, index=False, engine='openpyxl')
        
        # 통계 정보
        stats = {
            "total_items": total_items,
            "relevant_items": total_items,
            "relevant_ratio": 1.0,
            "categories": {
                "일반": total_items
            }
        }
        
        return RelevanceResponse(
            success=True,
            message=f"{total_items}개 뉴스 항목의 관련성 분석이 완료되었습니다.",
            file_path=result_file_name,
            stats=stats
        )
    
    except Exception as e:
        logger.error(f"Error analyzing relevance: {str(e)}")
        return RelevanceResponse(
            success=False,
            message=f"관련성 분석 중 오류가 발생했습니다: {str(e)}",
            errors={"analysis_error": str(e)}
        )
