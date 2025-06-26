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
    _file_cache = {}  # 파일 경로 캐시만 유지
    
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
        logger.info(f"파일 찾기 시작: {file_name}")
        
        # 캐시에서 먼저 확인
        if file_name in self._file_cache:
            cached_path = self._file_cache[file_name]
            if os.path.exists(cached_path):
                logger.info(f"캐시에서 파일 발견: {cached_path}")
                return cached_path
            else:
                # 캐시된 파일이 삭제되었으면 캐시에서 제거
                logger.warning(f"캐시된 파일이 존재하지 않음: {cached_path}")
                del self._file_cache[file_name]
        
        # 검색 경로 정의 (우선순위 조정)
        search_paths = [
            (self.settings.DEDUPLICATION_RESULTS_PATH, "deduplication"),  # 중복제거 결과 우선
            (self.settings.CRAWLING_RESULTS_PATH, "crawling"),
            (self.settings.RELEVANCE_RESULTS_PATH, "relevance"),
            (self.settings.RESULTS_PATH, "legacy")
        ]
        
        for search_path, path_type in search_paths:
            if not os.path.exists(search_path):
                logger.debug(f"경로가 존재하지 않음: {search_path}")
                continue
                
            potential_path = os.path.join(search_path, file_name)
            logger.debug(f"검색 시도 ({path_type}): {potential_path}")
            
            if os.path.exists(potential_path):
                # 캐시에 저장
                self._file_cache[file_name] = potential_path
                logger.info(f"파일 발견 ({path_type}): {potential_path}")
                return potential_path
        
        # 모든 경로에서 찾지 못한 경우 상세 로그
        logger.error(f"파일을 찾을 수 없음: {file_name}")
        logger.error(f"검색한 경로들:")
        for search_path, path_type in search_paths:
            if os.path.exists(search_path):
                files_in_dir = os.listdir(search_path)
                logger.error(f"  {path_type} ({search_path}): {len(files_in_dir)}개 파일")
                # 비슷한 파일명 찾기
                similar_files = [f for f in files_in_dir if file_name.lower() in f.lower() or f.lower() in file_name.lower()]
                if similar_files:
                    logger.error(f"    비슷한 파일들: {similar_files[:5]}")
            else:
                logger.error(f"  {path_type} ({search_path}): 경로 없음")
        
        return None
    
    def get_excel_files_optimized(self, directory: str = None) -> List[Dict[str, Any]]:
        """Excel 파일 목록 조회 - 실시간 업데이트"""
        file_list = []
        
        if directory is None:
            directories_to_check = [
                (self.settings.CRAWLING_RESULTS_PATH, "crawling"),
                (self.settings.DEDUPLICATION_RESULTS_PATH, "deduplication"),
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
        
        # 디렉토리 기반으로 평가 여부 판단 (더 정확함)
        # crawling 디렉토리의 파일은 평가되지 않은 원본 파일
        # deduplication 디렉토리의 파일은 중복 제거된 파일 (평가 가능)
        # relevance 디렉토리의 파일은 이미 평가된 결과 파일
        if dir_type == "crawling":
            has_evaluation = False  # 크롤링 디렉토리 파일은 아직 평가되지 않음
            has_deduplication = False  # 중복 제거되지 않음
        elif dir_type == "deduplication":
            has_evaluation = False  # 중복 제거만 됨, 아직 평가되지 않음
            has_deduplication = True   # 중복 제거됨
        elif dir_type == "relevance":
            has_evaluation = True   # 관련성 디렉토리 파일은 이미 평가됨
            has_deduplication = '_deduplicated' in filename  # 파일명으로 판단
        else:
            # legacy 파일들은 파일명으로 판단
            has_evaluation = '_analyzed' in filename
            has_deduplication = '_deduplicated' in filename
        
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
            'has_deduplication': has_deduplication,
            'is_evaluated': has_evaluation
        }
    
    def _determine_file_type(self, dir_type: str, filename: str) -> str:
        """파일 타입 결정"""
        if dir_type == "crawling":
            return "crawling"
        elif dir_type == "deduplication":
            return "deduplication"
        elif dir_type == "relevance":
            return "relevance"
        elif '_analyzed' in filename:
            return "relevance"
        elif '_deduplicated' in filename:
            return "deduplication"
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
            # 원본 파일 존재 확인
            if not os.path.exists(file_path):
                logger.error(f"원본 파일이 존재하지 않음: {file_path}")
                return None
            
            # 다운로드 폴더 생성
            os.makedirs(download_path, exist_ok=True)
            
            file_name = os.path.basename(file_path)
            download_file_path = os.path.join(download_path, file_name)
            
            # 파일 복사
            shutil.copy2(file_path, download_file_path)
            
            # 복사 결과 확인
            if os.path.exists(download_file_path):
                file_size = os.path.getsize(download_file_path)
                logger.info(f"다운로드 폴더 복사 성공: {download_file_path} ({file_size} bytes)")
                return download_file_path
            else:
                logger.error(f"다운로드 폴더 복사 확인 실패: {download_file_path}")
                return None
                
        except Exception as e:
            logger.error(f"다운로드 폴더 복사 오류: {str(e)}")
            return None
    
    def _invalidate_caches(self):
        """캐시 무효화 - 파일 경로 캐시만 정리"""
        # 디렉토리 캐시는 제거됨
        # 파일 경로 캐시만 유지 (find_file_path용)
        pass  # 더 이상 디렉토리 캐시가 없으므로
    
    def clear_all_caches(self):
        """모든 캐시 삭제"""
        self._file_cache.clear()
        logger.info("파일 경로 캐시가 삭제되었습니다")
    
    def refresh_files(self):
        """파일 목록 새로고침 (파일 경로 캐시 무효화)"""
        self.clear_all_caches()
        logger.info("파일 목록이 새로고침되었습니다")


# 전역 인스턴스
file_manager = FileManager()
