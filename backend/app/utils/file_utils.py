#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
import logging
from datetime import datetime
import glob

logger = logging.getLogger(__name__)


def save_to_excel(data: List[Dict[str, Any]], file_path: str,
                 copy_to_download: bool = False, download_path: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """데이터를 Excel 파일로 저장"""
    try:
        # 디렉토리 확인 및 생성
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # DataFrame 변환 및 컬럼명 한글로 변경
        df = pd.DataFrame(data)
        column_mapping = {
            'title': '제목',
            'link': '링크',
            'pubDate': '발행일시',
            'source_name': '출처',  # source_name을 출처로 매핑
            'description': '내용',
            'keyword': '키워드'
        }
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        # 원하는 컬럼 순서로 재정렬: 키워드, source, 제목, 내용이 가장 앞에 오도록
        desired_order = ['키워드', 'source', '제목', '내용']
        
        # 기존 컬럼 중에서 원하는 순서에 포함되지 않은 컬럼들
        remaining_columns = [col for col in df.columns if col not in desired_order]
        
        # 실제 존재하는 컬럼만 선택하여 순서 구성
        final_order = []
        for col in desired_order:
            if col in df.columns:
                final_order.append(col)
        
        # 나머지 컬럼들 추가
        final_order.extend(remaining_columns)
        
        # 컬럼 순서 재정렬
        df = df[final_order]
        
        # Excel 파일로 저장
        df.to_excel(file_path, index=False, engine='openpyxl')
        
        # 다운로드 폴더에 복사
        download_file_path = None
        if copy_to_download and download_path:
            os.makedirs(download_path, exist_ok=True)
            file_name = os.path.basename(file_path)
            download_file_path = os.path.join(download_path, file_name)
            shutil.copy2(file_path, download_file_path)
            
        return True, download_file_path
    
    except Exception as e:
        logger.error(f"Error saving to Excel: {str(e)}")
        return False, None


def get_excel_files(directory: str = None) -> List[Dict[str, Any]]:
    """디렉토리 내의 모든 Excel 파일 정보 가져오기"""
    from app.core.config import settings
    
    file_list = []
    
    # 디렉토리가 지정되지 않은 경우 모든 결과 폴더를 조회
    if directory is None:
        directories_to_check = [
            (settings.CRAWLING_RESULTS_PATH, "crawling"),
            (settings.RELEVANCE_RESULTS_PATH, "relevance"),
            (settings.RESULTS_PATH, "legacy")
        ]
    else:
        directories_to_check = [(directory, "custom")]
    
    try:
        for dir_path, dir_type in directories_to_check:
            if not os.path.exists(dir_path):
                continue
                
            excel_pattern = os.path.join(dir_path, "*.xlsx")
            all_files = glob.glob(excel_pattern)
            
            for file_path in all_files:
                file_stats = os.stat(file_path)
                rel_path = os.path.relpath(file_path, dir_path)
                file_name = os.path.basename(file_path)
                _, ext = os.path.splitext(file_path)
                
                # 파일 크기를 읽기 쉬운 형식으로 변환
                file_size = file_stats.st_size
                if file_size < 1024:
                    file_size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    file_size_str = f"{file_size / 1024:.1f} KB"
                else:
                    file_size_str = f"{file_size / (1024 * 1024):.1f} MB"
                
                # 관련성 평가 파일 확인
                has_evaluation = '_analyzed' in file_name
                
                # 파일 유형 판단
                if dir_type == "crawling":
                    file_type = "crawling"
                elif dir_type == "relevance":
                    file_type = "relevance"
                elif '_analyzed' in file_name:
                    file_type = "relevance"
                else:
                    file_type = "crawling"
                
                file_list.append({
                    'file_name': file_name,
                    'name': file_name,
                    'path': rel_path,
                    'full_path': file_path,
                    'directory_type': dir_type,
                    'file_type': file_type,
                    'size': file_size,
                    'file_size_str': file_size_str,
                    'created': datetime.fromtimestamp(file_stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                    'modified': datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'type': ext[1:].upper(),
                    'has_evaluation': has_evaluation,
                    'is_evaluated': has_evaluation
                })
        
        # 수정 날짜 기준 내림차순 정렬
        file_list.sort(key=lambda x: x['modified'], reverse=True)
        
    except Exception as e:
        logger.error(f"Error getting file list: {str(e)}")
    
    return file_list


def get_excel_preview(file_path: str, max_rows: int = 5) -> Dict[str, Any]:
    """Excel 파일 미리보기 가져오기"""
    try:
        _, ext = os.path.splitext(file_path)
        
        if ext.lower() != '.xlsx':
            raise ValueError(f"지원하지 않는 파일 형식: {ext}. XLSX 파일만 지원합니다.")
        
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # NaN, inf, -inf 값 처리
        df = df.replace([float('inf'), float('-inf')], None)
        df = df.fillna('')
        
        columns = df.columns.tolist()
        data = df.head(max_rows).to_dict('records')
        
        # 각 레코드의 float 값 검증 및 정리
        cleaned_data = []
        for record in data:
            cleaned_record = {}
            for key, value in record.items():
                if isinstance(value, float):
                    if pd.isna(value) or value == float('inf') or value == float('-inf'):
                        cleaned_record[key] = None
                    else:
                        cleaned_record[key] = value
                else:
                    cleaned_record[key] = value
            cleaned_data.append(cleaned_record)
        
        return {
            'columns': columns,
            'data': cleaned_data,
            'total_rows': len(df),
            'preview_rows': min(max_rows, len(df))
        }
    
    except Exception as e:
        logger.error(f"Error getting file preview: {str(e)}")
        return {'error': str(e)}


def get_excel_statistics(file_path: str) -> Dict[str, Any]:
    """Excel 파일 통계 정보 가져오기"""
    try:
        _, ext = os.path.splitext(file_path)
        
        if ext.lower() != '.xlsx':
            raise ValueError(f"지원하지 않는 파일 형식: {ext}. XLSX 파일만 지원합니다.")
        
        df = pd.read_excel(file_path, engine='openpyxl')
        df = df.replace([float('inf'), float('-inf')], None)
        
        # 기본 통계 정보
        stats = {
            'total_rows': len(df),
            'columns': df.columns.tolist(),
            'file_size': os.path.getsize(file_path),
            'created_date': datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S'),
            'modified_date': datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 키워드 분석
        if 'keyword' in df.columns or '키워드' in df.columns:
            keyword_col = 'keyword' if 'keyword' in df.columns else '키워드'
            keyword_counts = df[keyword_col].value_counts().to_dict()
            
            cleaned_keyword_stats = []
            for k, v in keyword_counts.items():
                if pd.isna(k):
                    k = None
                if isinstance(v, float) and (pd.isna(v) or v == float('inf') or v == float('-inf')):
                    v = 0
                cleaned_keyword_stats.append({'keyword': k, 'count': int(v) if v is not None else 0})
            
            stats['keyword_stats'] = cleaned_keyword_stats
        
        # 날짜 분석
        if 'pubDate' in df.columns or '발행일시' in df.columns:
            date_col = 'pubDate' if 'pubDate' in df.columns else '발행일시'
            
            try:
                if df[date_col].dtype == 'object':
                    df['date'] = pd.to_datetime(df[date_col])
                else:
                    df['date'] = df[date_col]
                
                date_counts = df['date'].dt.date.value_counts().sort_index()
                
                cleaned_date_stats = []
                for k, v in date_counts.items():
                    if pd.isna(k):
                        continue
                    if isinstance(v, float) and (pd.isna(v) or v == float('inf') or v == float('-inf')):
                        v = 0
                    cleaned_date_stats.append({'date': k.strftime('%Y-%m-%d'), 'count': int(v) if v is not None else 0})
                
                stats['date_stats'] = cleaned_date_stats
            except:
                stats['date_stats'] = []
        
        return stats
    
    except Exception as e:
        logger.error(f"Error getting file statistics: {str(e)}")
        return {'error': str(e)}
