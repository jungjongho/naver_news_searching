#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
통합 파일 처리 서비스
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from app.core.config import settings
from app.common.exceptions import FileNotFoundError, FileProcessingError

logger = logging.getLogger(__name__)


class FileService:
    """통합 파일 처리 서비스"""
    
    def __init__(self):
        self._ensure_directories()
    
    def _ensure_directories(self):
        """필요한 디렉토리 생성"""
        directories = [
            settings.RESULTS_PATH,
            settings.CRAWLING_RESULTS_PATH,
            settings.RELEVANCE_RESULTS_PATH
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def find_file(self, file_name: str) -> str:
        """파일 경로 찾기 (우선순위: relevance > deduplication > crawling > results)"""
        search_paths = [
            os.path.join(settings.RELEVANCE_RESULTS_PATH, file_name),
            os.path.join(settings.DEDUPLICATION_RESULTS_PATH, file_name),
            os.path.join(settings.CRAWLING_RESULTS_PATH, file_name),
            os.path.join(settings.RESULTS_PATH, file_name)
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                return path
        
        raise FileNotFoundError(file_name)
    
    def load_news_data(self, file_path: str) -> List[Dict[str, Any]]:
        """뉴스 데이터 로드 (Excel 파일)"""
        try:
            if not file_path.endswith(('.xlsx', '.xls')):
                raise FileProcessingError(f"지원하지 않는 파일 형식: {file_path}. XLSX 파일만 지원합니다.")
            
            # 파일 경로가 상대경로인 경우 찾기
            if not os.path.isabs(file_path):
                file_path = self.find_file(file_path)
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(file_path)
            
            df = pd.read_excel(file_path, engine='openpyxl')
            news_data = df.to_dict('records')
            
            logger.info(f"파일 로드 완료: {file_path}, {len(news_data)}개 기사")
            return news_data
            
        except Exception as e:
            if isinstance(e, (FileNotFoundError, FileProcessingError)):
                raise
            logger.error(f"파일 로드 실패: {file_path}, 오류: {str(e)}")
            raise FileProcessingError(f"파일 로드 중 오류가 발생했습니다: {str(e)}")
    
    def save_excel_data(
        self,
        data: List[Dict[str, Any]],
        file_name: str,
        folder: str = "results"
    ) -> str:
        """Excel 데이터 저장"""
        try:
            # 폴더별 경로 설정
            folder_paths = {
                "results": settings.RESULTS_PATH,
                "crawling": settings.CRAWLING_RESULTS_PATH,
                "relevance": settings.RELEVANCE_RESULTS_PATH
            }
            
            base_path = folder_paths.get(folder, settings.RESULTS_PATH)
            
            # 파일명에 확장자가 없으면 추가
            if not file_name.endswith('.xlsx'):
                file_name = f"{file_name}.xlsx"
            
            file_path = os.path.join(base_path, file_name)
            
            # DataFrame 생성 및 저장
            df = pd.DataFrame(data)
            
            # keywords 컬럼이 리스트인 경우 문자열로 변환
            if 'keywords' in df.columns:
                df['keywords'] = df['keywords'].apply(
                    lambda x: ', '.join(x) if isinstance(x, list) else str(x) if x is not None else ''
                )
            
            df.to_excel(file_path, index=False, engine='openpyxl')
            
            logger.info(f"파일 저장 완료: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"파일 저장 실패: {file_name}, 오류: {str(e)}")
            raise FileProcessingError(f"파일 저장 중 오류가 발생했습니다: {str(e)}")
    
    def get_file_list(self, folder: str = "results") -> List[Dict[str, Any]]:
        """폴더 내 파일 목록 조회"""
        try:
            folder_paths = {
                "results": settings.RESULTS_PATH,
                "crawling": settings.CRAWLING_RESULTS_PATH,
                "relevance": settings.RELEVANCE_RESULTS_PATH
            }
            
            folder_path = folder_paths.get(folder, settings.RESULTS_PATH)
            
            if not os.path.exists(folder_path):
                return []
            
            files = []
            for file_name in os.listdir(folder_path):
                if file_name.endswith(('.xlsx', '.xls', '.csv')):
                    file_path = os.path.join(folder_path, file_name)
                    stat = os.stat(file_path)
                    
                    files.append({
                        "name": file_name,
                        "path": file_path,
                        "size": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    })
            
            # 수정일시 기준 내림차순 정렬
            files.sort(key=lambda x: x["modified_at"], reverse=True)
            return files
            
        except Exception as e:
            logger.error(f"파일 목록 조회 실패: {folder}, 오류: {str(e)}")
            raise FileProcessingError(f"파일 목록 조회 중 오류가 발생했습니다: {str(e)}")
    
    def copy_to_downloads(self, file_path: str) -> Optional[str]:
        """다운로드 폴더로 파일 복사"""
        try:
            if not settings.AUTO_COPY_TO_DOWNLOADS:
                return None
            
            import shutil
            file_name = os.path.basename(file_path)
            download_path = os.path.join(settings.USER_DOWNLOAD_PATH, file_name)
            
            # 중복 파일명 처리
            counter = 1
            original_name, ext = os.path.splitext(file_name)
            while os.path.exists(download_path):
                new_name = f"{original_name}_{counter}{ext}"
                download_path = os.path.join(settings.USER_DOWNLOAD_PATH, new_name)
                counter += 1
            
            shutil.copy2(file_path, download_path)
            logger.info(f"파일이 다운로드 폴더로 복사되었습니다: {download_path}")
            return download_path
            
        except Exception as e:
            logger.warning(f"다운로드 폴더 복사 실패: {str(e)}")
            return None
    
    def generate_timestamped_filename(self, base_name: str, prefix: str = "", suffix: str = "") -> str:
        """타임스탬프가 포함된 파일명 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 확장자 분리
        name_part, ext = os.path.splitext(base_name)
        
        # 파일명 구성
        parts = []
        if prefix:
            parts.append(prefix)
        parts.append(name_part)
        if suffix:
            parts.append(suffix)
        parts.append(timestamp)
        
        return "_".join(parts) + (ext or ".xlsx")


# 전역 인스턴스
file_service = FileService()
