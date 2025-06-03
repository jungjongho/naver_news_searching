#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import csv
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
import logging
from datetime import datetime
import glob

logger = logging.getLogger(__name__)

def save_to_csv(data: List[Dict[str, Any]], file_path: str, encoding: str = 'utf-8-sig', 
                copy_to_download: bool = False, download_path: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    데이터를 CSV 파일로 저장
    
    Args:
        data: 저장할 데이터 (딕셔너리 리스트)
        file_path: 저장할 파일 경로
        encoding: 파일 인코딩 (기본값: 'utf-8-sig')
        copy_to_download: 다운로드 폴더에 복사할지 여부
        download_path: 다운로드 폴더 경로
        
    Returns:
        (성공 여부, 다운로드 폴더에 복사된 파일 경로 또는 None)
    """
    try:
        # 디렉토리 확인 및 생성
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # DataFrame 변환
        df = pd.DataFrame(data)
        
        # 컬럼명 한글로 변경
        column_mapping = {
            'title': '제목',
            'link': '링크',
            'pubDate': '발행일시',
            'source': '출처',
            'description': '내용',
            'keyword': '키워드'
        }
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        # CSV 파일로 저장
        df.to_csv(file_path, index=False, encoding=encoding)
        
        # 다운로드 폴더에 복사
        download_file_path = None
        if copy_to_download and download_path:
            # 다운로드 폴더 확인 및 생성
            os.makedirs(download_path, exist_ok=True)
            
            # 파일 이름만 추출
            file_name = os.path.basename(file_path)
            download_file_path = os.path.join(download_path, file_name)
            
            # 파일 복사
            shutil.copy2(file_path, download_file_path)
            
        return True, download_file_path
    
    except Exception as e:
        logger.error(f"Error saving to CSV: {str(e)}")
        return False, None

def save_to_excel(data: List[Dict[str, Any]], file_path: str,
                 copy_to_download: bool = False, download_path: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    데이터를 Excel 파일로 저장
    
    Args:
        data: 저장할 데이터 (딕셔너리 리스트)
        file_path: 저장할 파일 경로
        copy_to_download: 다운로드 폴더에 복사할지 여부
        download_path: 다운로드 폴더 경로
        
    Returns:
        (성공 여부, 다운로드 폴더에 복사된 파일 경로 또는 None)
    """
    try:
        # 디렉토리 확인 및 생성
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # DataFrame 변환
        df = pd.DataFrame(data)
        
        # 컬럼명 한글로 변경
        column_mapping = {
            'title': '제목',
            'link': '링크',
            'pubDate': '발행일시',
            'source': '출처',
            'description': '내용',
            'keyword': '키워드'
        }
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        # Excel 파일로 저장
        df.to_excel(file_path, index=False, engine='openpyxl')
        
        # 다운로드 폴더에 복사
        download_file_path = None
        if copy_to_download and download_path:
            # 다운로드 폴더 확인 및 생성
            os.makedirs(download_path, exist_ok=True)
            
            # 파일 이름만 추출
            file_name = os.path.basename(file_path)
            download_file_path = os.path.join(download_path, file_name)
            
            # 파일 복사
            shutil.copy2(file_path, download_file_path)
            
        return True, download_file_path
    
    except Exception as e:
        logger.error(f"Error saving to Excel: {str(e)}")
        return False, None

def get_excel_files(directory: str = None) -> List[Dict[str, Any]]:
    """
    디렉토리 내의 모든 Excel 파일 정보 가져오기
    
    Args:
        directory: 대상 디렉토리 (기본값: None - 모든 결과 폴더 조회)
        
    Returns:
        파일 정보 목록 (경로, 크기, 날짜 등)
    """
    from app.core.config import settings
    
    file_list = []
    
    # 디렉토리가 지정되지 않은 경우 모든 결과 폴더를 조회
    if directory is None:
        directories_to_check = [
            (settings.CRAWLING_RESULTS_PATH, "crawling"),
            (settings.RELEVANCE_RESULTS_PATH, "relevance"),
            (settings.RESULTS_PATH, "legacy")  # 기존 파일들
        ]
    else:
        directories_to_check = [(directory, "custom")]
    
    try:
        for dir_path, dir_type in directories_to_check:
            if not os.path.exists(dir_path):
                continue
                
            # Excel 파일 목록 가져오기
            excel_pattern = os.path.join(dir_path, "*.xlsx")
            
            # 패턴에 맞는 모든 파일 경로
            all_files = glob.glob(excel_pattern)
            
            for file_path in all_files:
                # 파일 정보 가져오기
                file_stats = os.stat(file_path)
                
                # 상대 경로 변환
                rel_path = os.path.relpath(file_path, dir_path)
                file_name = os.path.basename(file_path)
                
                # 파일 확장자
                _, ext = os.path.splitext(file_path)
                
                # 파일 크기를 읽기 쉬운 형식으로 변환
                file_size = file_stats.st_size
                if file_size < 1024:
                    file_size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    file_size_str = f"{file_size / 1024:.1f} KB"
                else:
                    file_size_str = f"{file_size / (1024 * 1024):.1f} MB"
                
                # 관련성 평가 파일 확인 (파일명에 '_analyzed' 포함시 평가됨으로 간주)
                has_evaluation = '_analyzed' in file_name
                is_evaluated = has_evaluation
                
                # 파일 유형 판단
                if dir_type == "crawling":
                    file_type = "crawling"
                elif dir_type == "relevance":
                    file_type = "relevance"
                elif '_analyzed' in file_name:
                    file_type = "relevance"  # 기존 analyzed 파일들
                else:
                    file_type = "crawling"  # 기존 raw 파일들
                
                # 프론트엔드에서 기대하는 필드명으로 파일 정보 추가
                file_list.append({
                    'file_name': file_name,  # 프론트엔드에서 사용하는 필드명
                    'name': file_name,  # 기존 호환성
                    'path': rel_path,
                    'full_path': file_path,  # 전체 경로 추가
                    'directory_type': dir_type,  # 폴더 유형
                    'file_type': file_type,  # 파일 유형
                    'size': file_size,
                    'file_size_str': file_size_str,  # 프론트엔드에서 사용하는 필드명
                    'created': datetime.fromtimestamp(file_stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                    'modified': datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'type': ext[1:].upper(),  # 확장자 (앞의 점 제외)
                    'has_evaluation': has_evaluation,  # 프론트엔드에서 사용하는 필드명
                    'is_evaluated': is_evaluated  # 프론트엔드에서 사용하는 필드명
                })
        
        # 수정 날짜 기준 내림차순 정렬
        file_list.sort(key=lambda x: x['modified'], reverse=True)
        
    except Exception as e:
        logger.error(f"Error getting file list: {str(e)}")
    
    return file_list

def get_excel_preview(file_path: str, max_rows: int = 5) -> Dict[str, Any]:
    """
    Excel 파일 미리보기 가져오기
    
    Args:
        file_path: 파일 경로
        max_rows: 최대 행 수
        
    Returns:
        미리보기 데이터
    """
    try:
        # 파일 확장자 확인
        _, ext = os.path.splitext(file_path)
        
        # Excel 파일 읽기
        if ext.lower() == '.xlsx':
            df = pd.read_excel(file_path, engine='openpyxl')
        else:
            raise ValueError(f"지원하지 않는 파일 형식: {ext}. XLSX 파일만 지원합니다.")
        
        # NaN, inf, -inf 값 처리
        df = df.replace([float('inf'), float('-inf')], None)
        df = df.fillna('')
        
        # 데이터 변환
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
    """
    Excel 파일 통계 정보 가져오기
    
    Args:
        file_path: 파일 경로
        
    Returns:
        통계 정보
    """
    try:
        # 파일 확장자 확인
        _, ext = os.path.splitext(file_path)
        
        # Excel 파일 읽기
        if ext.lower() == '.xlsx':
            df = pd.read_excel(file_path, engine='openpyxl')
        else:
            raise ValueError(f"지원하지 않는 파일 형식: {ext}. XLSX 파일만 지원합니다.")
        
        # NaN, inf, -inf 값 처리
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
            
            # keyword_counts의 값들을 정리
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
            
            # 날짜 형식 변환
            try:
                if df[date_col].dtype == 'object':
                    df['date'] = pd.to_datetime(df[date_col])
                else:
                    df['date'] = df[date_col]
                
                # 날짜별 기사 수
                date_counts = df['date'].dt.date.value_counts().sort_index()
                
                # date_counts의 값들을 정리
                cleaned_date_stats = []
                for k, v in date_counts.items():
                    if pd.isna(k):
                        continue
                    if isinstance(v, float) and (pd.isna(v) or v == float('inf') or v == float('-inf')):
                        v = 0
                    cleaned_date_stats.append({'date': k.strftime('%Y-%m-%d'), 'count': int(v) if v is not None else 0})
                
                stats['date_stats'] = cleaned_date_stats
            except:
                # 날짜 변환 실패 시 통계 생략
                stats['date_stats'] = []
        
        return stats
    
    except Exception as e:
        logger.error(f"Error getting file statistics: {str(e)}")
        return {'error': str(e)}
