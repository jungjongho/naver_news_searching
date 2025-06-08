#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
import logging
from datetime import datetime
import glob
from pathlib import Path

logger = logging.getLogger(__name__)


class FileManager:
    """통합 파일 관리 클래스 - 싱글톤 패턴"""
    
    _instance = None
    _file_cache = {}
    _directory_cache = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            from app.core.config import settings
            self.settings = settings
            self._initialized = True
            logger.info("FileManager 초기화 완료")
    
    def find_file_path(self, file_name: str) -> Optional[str]:
        """캐시를 활용한 효율적인 파일 경로 찾기"""
        # 캐시에서 먼저 확인
        if file_name in self._file_cache:
            cached_path = self._file_cache[file_name]
            if os.path.exists(cached_path):
                return cached_path
            else:
                # 캐시된 파일이 삭제되었으면 캐시에서 제거
                del self._file_cache[file_name]
        
        # 검색 경로 정의
        search_paths = [
            self.settings.CRAWLING_RESULTS_PATH,
            self.settings.RELEVANCE_RESULTS_PATH,
            self.settings.RESULTS_PATH
        ]
        
        for search_path in search_paths:
            if not os.path.exists(search_path):
                continue
                
            potential_path = os.path.join(search_path, file_name)
            if os.path.exists(potential_path):
                # 캐시에 저장
                self._file_cache[file_name] = potential_path
                return potential_path
        
        return None
    
    def get_excel_files_optimized(self, directory: str = None) -> List[Dict[str, Any]]:
        """최적화된 Excel 파일 목록 조회"""
        cache_key = directory or "all_directories"
        
        # 캐시 확인 (5분간 유효)
        if cache_key in self._directory_cache:
            cache_time, cached_files = self._directory_cache[cache_key]
            if (datetime.now() - cache_time).seconds < 300:  # 5분
                return cached_files
        
        file_list = []
        
        if directory is None:
            directories_to_check = [
                (self.settings.CRAWLING_RESULTS_PATH, "crawling"),
                (self.settings.RELEVANCE_RESULTS_PATH, "relevance"),
                (self.settings.RESULTS_PATH, "legacy")
            ]
        else:
            directories_to_check = [(directory, "custom")]
        
        try:
            for dir_path, dir_type in directories_to_check:
                if not os.path.exists(dir_path):
                    continue
                
                # glob 대신 os.listdir 사용 (더 빠름)
                for filename in os.listdir(dir_path):
                    if not filename.lower().endswith('.xlsx'):
                        continue
                    
                    file_path = os.path.join(dir_path, filename)
                    
                    try:
                        file_stats = os.stat(file_path)
                        file_info = self._create_file_info(
                            filename, file_path, dir_path, dir_type, file_stats
                        )
                        file_list.append(file_info)
                    except OSError:
                        continue
            
            # 수정 날짜 기준 내림차순 정렬
            file_list.sort(key=lambda x: x['modified'], reverse=True)
            
            # 캐시에 저장
            self._directory_cache[cache_key] = (datetime.now(), file_list)
            
        except Exception as e:
            logger.error(f"파일 목록 조회 오류: {str(e)}")
        
        return file_list
    
    def _create_file_info(self, filename: str, file_path: str, dir_path: str, 
                         dir_type: str, file_stats) -> Dict[str, Any]:
        """파일 정보 객체 생성"""
        rel_path = os.path.relpath(file_path, dir_path)
        file_size = file_stats.st_size
        
        # 파일 크기 포맷팅 (간소화)
        if file_size < 1024:
            file_size_str = f"{file_size} B"
        elif file_size < 1048576:  # 1024 * 1024
            file_size_str = f"{file_size / 1024:.1f} KB"
        else:
            file_size_str = f"{file_size / 1048576:.1f} MB"
        
        has_evaluation = '_analyzed' in filename
        file_type = self._determine_file_type(dir_type, filename)
        
        return {
            'file_name': filename,
            'name': filename,
            'path': rel_path,
            'full_path': file_path,
            'directory_type': dir_type,
            'file_type': file_type,
            'size': file_size,
            'file_size_str': file_size_str,
            'created': datetime.fromtimestamp(file_stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
            'modified': datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'XLSX',
            'has_evaluation': has_evaluation,
            'is_evaluated': has_evaluation
        }
    
    def _determine_file_type(self, dir_type: str, filename: str) -> str:
        """파일 타입 결정"""
        if dir_type == "crawling":
            return "crawling"
        elif dir_type == "relevance":
            return "relevance"
        elif '_analyzed' in filename:
            return "relevance"
        else:
            return "crawling"
    
    def save_to_excel_optimized(self, data: List[Dict[str, Any]], file_path: str,
                               copy_to_download: bool = False, 
                               download_path: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """최적화된 Excel 저장"""
        try:
            # 디렉토리 생성
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # DataFrame 변환 (간소화된 컬럼 매핑)
            df = pd.DataFrame(data)
            
            # 한 번에 컬럼명 변경
            column_mapping = {
                'title': '제목', 'link': '링크', 'pubDate': '발행일시',
                'source': '출처', 'description': '내용', 'keyword': '키워드'
            }
            
            # 존재하는 컬럼만 변경
            existing_mappings = {k: v for k, v in column_mapping.items() if k in df.columns}
            df.rename(columns=existing_mappings, inplace=True)
            
            # Excel 저장
            df.to_excel(file_path, index=False, engine='openpyxl')
            
            # 다운로드 폴더 복사
            download_file_path = None
            if copy_to_download and download_path:
                download_file_path = self._copy_to_download_optimized(file_path, download_path)
            
            # 캐시 무효화
            self._invalidate_caches()
            
            return True, download_file_path
        
        except Exception as e:
            logger.error(f"Excel 저장 오류: {str(e)}")
            return False, None
    
    def _copy_to_download_optimized(self, file_path: str, download_path: str) -> Optional[str]:
        """최적화된 다운로드 폴더 복사"""
        try:
            os.makedirs(download_path, exist_ok=True)
            file_name = os.path.basename(file_path)
            download_file_path = os.path.join(download_path, file_name)
            shutil.copy2(file_path, download_file_path)
            return download_file_path
        except Exception as e:
            logger.error(f"다운로드 폴더 복사 오류: {str(e)}")
            return None
    
    def _invalidate_caches(self):
        """캐시 무효화"""
        self._directory_cache.clear()
        # 파일 캐시는 유지 (파일 삭제가 아닌 추가이므로)
    
    def clear_all_caches(self):
        """모든 캐시 삭제"""
        self._file_cache.clear()
        self._directory_cache.clear()
        logger.info("모든 파일 캐시가 삭제되었습니다")


# 전역 인스턴스
file_manager = FileManager()
