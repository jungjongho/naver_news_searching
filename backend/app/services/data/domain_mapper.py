#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""도메인-신문사 매핑 서비스"""

import os
import pandas as pd
from urllib.parse import urlparse
from typing import Dict, Optional
import logging

from app.utils.constants.file_constants import DOMAIN_MAPPING_FILE, REQUIRED_CSV_COLUMNS

logger = logging.getLogger(__name__)


class DomainMapper:
    """도메인-신문사 매핑을 담당하는 클래스"""
    
    def __init__(self):
        self.domain_to_source: Dict[str, str] = {}
        self._load_mapping()
    
    def _load_mapping(self) -> None:
        """도메인-신문사 매핑 테이블 로드"""
        try:
            # 프로젝트 루트에서 CSV 파일 찾기
            csv_path = self._find_mapping_file()
            
            if not csv_path or not os.path.exists(csv_path):
                logger.warning(f"도메인 매핑 파일을 찾을 수 없습니다: {csv_path}")
                return
            
            df = pd.read_csv(csv_path, encoding='utf-8')
            
            # 필수 컬럼 확인
            if not all(col in df.columns for col in REQUIRED_CSV_COLUMNS):
                logger.error(f"CSV 파일에 필수 컬럼이 없습니다. 필요: {REQUIRED_CSV_COLUMNS}")
                return
            
            # 매핑 딕셔너리 생성
            self.domain_to_source = df.set_index('domain')['source'].to_dict()
            logger.info(f"도메인-신문사 매핑 테이블 로드 완료: {len(self.domain_to_source)}개 항목")
            
        except Exception as e:
            logger.error(f"도메인 매핑 파일 로드 중 오류: {str(e)}")
            self.domain_to_source = {}
    
    def _find_mapping_file(self) -> Optional[str]:
        """매핑 파일 경로 찾기"""
        # 현재 파일 기준으로 프로젝트 루트 찾기
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 최대 5단계까지 상위 디렉토리 탐색
        for _ in range(5):
            potential_path = os.path.join(current_dir, DOMAIN_MAPPING_FILE)
            if os.path.exists(potential_path):
                return potential_path
            current_dir = os.path.dirname(current_dir)
        
        return None
    
    def extract_domain_from_url(self, url: str) -> str:
        """URL에서 도메인 추출"""
        try:
            if not url:
                return ""
            
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # www. 제거
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # 주 도메인만 추출 (예: news.naver.com -> naver)
            domain_parts = domain.split('.')
            return domain_parts[0] if domain_parts else domain
            
        except Exception as e:
            logger.error(f"URL에서 도메인 추출 실패: {url}, 오류: {str(e)}")
            return ""
    
    def get_source_from_url(self, url: str) -> Optional[str]:
        """URL을 기반으로 신문사명 조회"""
        if not url:
            return None
        
        domain = self.extract_domain_from_url(url)
        if not domain:
            return None
        
        return self.domain_to_source.get(domain)
    
    def add_mapping(self, domain: str, source: str) -> None:
        """새로운 매핑 추가 (런타임에서만 유효)"""
        if domain and source:
            self.domain_to_source[domain] = source
            logger.info(f"새로운 도메인 매핑 추가: {domain} -> {source}")
    
    def get_all_mappings(self) -> Dict[str, str]:
        """모든 매핑 반환"""
        return self.domain_to_source.copy()
    
    def get_mapping_count(self) -> int:
        """매핑 개수 반환"""
        return len(self.domain_to_source)


# 싱글톤 인스턴스
domain_mapper = DomainMapper()
