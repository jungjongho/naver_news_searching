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

def get_csv_files(directory: str) -> List[Dict[str, Any]]:
    """
    디렉토리 내의 모든 CSV 파일 정보 가져오기
    
    Args:
        directory: 대상 디렉토리
        
    Returns:
        파일 정보 목록 (경로, 크기, 날짜 등)
    """
    file_list = []
    
    try:
        # CSV 및 Excel 파일 목록 가져오기
        csv_pattern = os.path.join(directory, "*.csv")
        excel_pattern = os.path.join(directory, "*.xlsx")
        
        # 패턴에 맞는 모든 파일 경로
        all_files = glob.glob(csv_pattern) + glob.glob(excel_pattern)
        
        for file_path in all_files:
            # 파일 정보 가져오기
            file_stats = os.stat(file_path)
            
            # 상대 경로 변환
            rel_path = os.path.relpath(file_path, directory)
            
            # 파일 확장자
            _, ext = os.path.splitext(file_path)
            
            # 파일 정보 추가
            file_list.append({
                'name': os.path.basename(file_path),
                'path': rel_path,
                'size': file_stats.st_size,
                'created': datetime.fromtimestamp(file_stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                'modified': datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'type': ext[1:].upper()  # 확장자 (앞의 점 제외)
            })
        
        # 수정 날짜 기준 내림차순 정렬
        file_list.sort(key=lambda x: x['modified'], reverse=True)
        
    except Exception as e:
        logger.error(f"Error getting file list: {str(e)}")
    
    return file_list

def get_csv_preview(file_path: str, max_rows: int = 5) -> Dict[str, Any]:
    """
    CSV 파일 미리보기 가져오기
    
    Args:
        file_path: 파일 경로
        max_rows: 최대 행 수
        
    Returns:
        미리보기 데이터
    """
    try:
        # 파일 확장자 확인
        _, ext = os.path.splitext(file_path)
        
        # Excel 또는 CSV 파일 읽기
        if ext.lower() == '.xlsx':
            df = pd.read_excel(file_path, engine='openpyxl')
        else:  # .csv
            df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        # 데이터 변환
        columns = df.columns.tolist()
        data = df.head(max_rows).to_dict('records')
        
        return {
            'columns': columns,
            'data': data,
            'total_rows': len(df),
            'preview_rows': min(max_rows, len(df))
        }
    
    except Exception as e:
        logger.error(f"Error getting file preview: {str(e)}")
        return {'error': str(e)}

def get_csv_statistics(file_path: str) -> Dict[str, Any]:
    """
    CSV 파일 통계 정보 가져오기
    
    Args:
        file_path: 파일 경로
        
    Returns:
        통계 정보
    """
    try:
        # 파일 확장자 확인
        _, ext = os.path.splitext(file_path)
        
        # Excel 또는 CSV 파일 읽기
        if ext.lower() == '.xlsx':
            df = pd.read_excel(file_path, engine='openpyxl')
        else:  # .csv
            df = pd.read_csv(file_path, encoding='utf-8-sig')
        
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
            stats['keyword_stats'] = [{'keyword': k, 'count': v} for k, v in keyword_counts.items()]
        
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
                stats['date_stats'] = [{'date': k.strftime('%Y-%m-%d'), 'count': v} for k, v in date_counts.items()]
            except:
                # 날짜 변환 실패 시 통계 생략
                stats['date_stats'] = []
        
        return stats
    
    except Exception as e:
        logger.error(f"Error getting file statistics: {str(e)}")
        return {'error': str(e)}
