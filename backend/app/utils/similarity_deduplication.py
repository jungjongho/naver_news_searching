#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from difflib import SequenceMatcher
from collections import defaultdict
from typing import List, Dict, Any, Tuple, Set
import logging

logger = logging.getLogger(__name__)

class SimilarityDeduplicator:
    """의미적 유사도 기반 뉴스 중복 제거"""
    
    def __init__(self, similarity_threshold: float = 0.7):
        """
        Args:
            similarity_threshold: 유사도 임계값 (0~1, 기본값: 0.7)
        """
        self.similarity_threshold = similarity_threshold
    
    def preprocess_title(self, title: str) -> str:
        """제목 전처리"""
        if not title:
            return ""
        
        # HTML 엔티티 제거
        title = re.sub(r'&quot;|&amp;|&lt;|&gt;', '', title)
        # 특수문자 제거
        title = re.sub(r'["""''']', '', title)
        # 연속된 공백 제거
        title = re.sub(r'\s+', ' ', title)
        return title.strip()
    
    def extract_core_content(self, title: str) -> Dict[str, List[str]]:
        """핵심 내용 추출"""
        # 회사명 추출
        companies = []
        company_patterns = [
            '코스맥스', '코스맥스엔비티', '콜마', 'HK이노엔', '아모레퍼시픽', 
            'LG생활건강', '올리브영', '실리콘투', '큐텐재팬', 'CJ올리브영'
        ]
        for pattern in company_patterns:
            if pattern in title:
                companies.append(pattern)
        
        # 이벤트/행사명 추출
        events = []
        event_patterns = ['HNC', 'CPHI', '박람회', '전시회', '참가', '출시', '론칭']
        for pattern in event_patterns:
            if pattern in title:
                events.append(pattern)
        
        # 연도 추출
        years = re.findall(r'20\d{2}', title)
        
        # 핵심 키워드 추출
        keywords = []
        business_keywords = [
            '이너뷰티', '글로벌', '시장', '공략', '확대', '솔루션', 
            '신제형', '신소재', 'K뷰티', '뷰티', '화장품', '건강기능식품',
            '펫푸드', '마이크로바이옴', '스킨케어', '탈모', '비건'
        ]
        for keyword in business_keywords:
            if keyword in title:
                keywords.append(keyword)
        
        # 지역/국가 추출
        regions = []
        region_patterns = ['中', '중국', '日', '일본', '美', '미국', '북미', '유럽', '중동', '동남아', '콜롬비아']
        for pattern in region_patterns:
            if pattern in title:
                regions.append(pattern)
        
        return {
            'companies': companies,
            'events': events,
            'years': years,
            'keywords': keywords,
            'regions': regions
        }
    
    def calculate_text_similarity(self, title1: str, title2: str) -> float:
        """두 제목의 텍스트 유사도 계산"""
        return SequenceMatcher(None, title1, title2).ratio()
    
    def calculate_semantic_similarity(self, core1: Dict[str, List[str]], core2: Dict[str, List[str]]) -> float:
        """의미적 유사도 계산"""
        # 각 요소별 일치도 계산
        company_overlap = len(set(core1['companies']) & set(core2['companies']))
        event_overlap = len(set(core1['events']) & set(core2['events']))
        year_overlap = len(set(core1['years']) & set(core2['years']))
        keyword_overlap = len(set(core1['keywords']) & set(core2['keywords']))
        region_overlap = len(set(core1['regions']) & set(core2['regions']))
        
        # 전체 키워드 수
        total_companies = max(len(core1['companies']), len(core2['companies']), 1)
        total_events = max(len(core1['events']), len(core2['events']), 1)
        total_keywords = max(len(core1['keywords']), len(core2['keywords']), 1)
        total_regions = max(len(core1['regions']), len(core2['regions']), 1)
        
        # 정규화된 유사도 계산
        company_sim = company_overlap / total_companies
        event_sim = event_overlap / total_events
        keyword_sim = keyword_overlap / total_keywords
        region_sim = region_overlap / total_regions
        year_sim = 1.0 if year_overlap > 0 else 0.0
        
        # 가중 평균 계산 (회사명과 이벤트에 더 높은 가중치)
        semantic_similarity = (
            company_sim * 0.3 +
            event_sim * 0.25 +
            keyword_sim * 0.2 +
            region_sim * 0.15 +
            year_sim * 0.1
        )
        
        return semantic_similarity
    
    def calculate_similarity(self, title1: str, title2: str) -> float:
        """두 제목의 전체 유사도 계산"""
        # 전처리
        processed1 = self.preprocess_title(title1)
        processed2 = self.preprocess_title(title2)
        
        # 텍스트 유사도
        text_similarity = self.calculate_text_similarity(processed1, processed2)
        
        # 의미적 유사도
        core1 = self.extract_core_content(title1)
        core2 = self.extract_core_content(title2)
        semantic_similarity = self.calculate_semantic_similarity(core1, core2)
        
        # 최종 유사도 = 텍스트 유사도(40%) + 의미적 유사도(60%)
        final_similarity = (text_similarity * 0.4) + (semantic_similarity * 0.6)
        
        return final_similarity
    
    def group_similar_articles(self, news_items: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """유사한 기사들을 그룹핑"""
        if not news_items:
            return []
        
        logger.info(f"유사도 기반 그룹핑 시작: {len(news_items)}개 기사")
        
        groups = []
        used_indices = set()
        
        for i, item1 in enumerate(news_items):
            if i in used_indices:
                continue
            
            current_group = [item1]
            used_indices.add(i)
            title1 = item1.get('title', '')
            
            for j, item2 in enumerate(news_items[i+1:], i+1):
                if j in used_indices:
                    continue
                
                title2 = item2.get('title', '')
                similarity = self.calculate_similarity(title1, title2)
                
                if similarity >= self.similarity_threshold:
                    current_group.append(item2)
                    used_indices.add(j)
            
            groups.append(current_group)
        
        logger.info(f"그룹핑 완료: {len(groups)}개 그룹 생성")
        return groups
    
    def select_representative(self, group: List[Dict[str, Any]]) -> Dict[str, Any]:
        """그룹에서 대표 기사 선택"""
        if len(group) == 1:
            return group[0]
        
        # 선택 기준:
        # 1. 제목이 가장 짧고 깔끔한 것
        # 2. 가장 최근 기사
        # 3. 신뢰할 만한 언론사
        
        # 우선순위 언론사 목록
        trusted_sources = [
            '연합뉴스', '뉴스1', '헤럴드경제', '이데일리', 
            '아시아경제', '뉴시스', '머니투데이', '파이낸셜뉴스'
        ]
        
        # 1순위: 신뢰할 만한 언론사의 기사
        trusted_articles = [
            article for article in group 
            if article.get('source') in trusted_sources
        ]
        
        if trusted_articles:
            # 신뢰할 만한 언론사 중에서 가장 짧은 제목
            best_article = min(trusted_articles, 
                             key=lambda x: len(x.get('title', '')))
        else:
            # 전체 중에서 가장 짧은 제목
            best_article = min(group, 
                             key=lambda x: len(x.get('title', '')))
        
        return best_article
    
    def deduplicate(self, news_items: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """유사도 기반 중복 제거 메인 함수"""
        if not news_items:
            return [], {"original_count": 0, "unique_count": 0, "removed_count": 0}
        
        logger.info(f"유사도 기반 중복 제거 시작: {len(news_items)}개 기사")
        
        # 그룹핑
        groups = self.group_similar_articles(news_items)
        
        # 대표 기사 선택
        unique_articles = []
        duplicate_groups = []
        
        for group in groups:
            if len(group) == 1:
                unique_articles.append(group[0])
            else:
                representative = self.select_representative(group)
                unique_articles.append(representative)
                
                duplicate_info = {
                    'representative': representative,
                    'duplicates': [article for article in group if article != representative],
                    'total_count': len(group),
                    'similarity_threshold': self.similarity_threshold
                }
                duplicate_groups.append(duplicate_info)
        
        # 통계 정보
        stats = {
            'original_count': len(news_items),
            'unique_count': len(unique_articles),
            'removed_count': len(news_items) - len(unique_articles),
            'duplicate_groups': len(duplicate_groups),
            'similarity_threshold': self.similarity_threshold,
            'duplicate_details': duplicate_groups
        }
        
        logger.info(f"중복 제거 완료: {stats['original_count']} → {stats['unique_count']} "
                   f"({stats['removed_count']}개 제거, {stats['duplicate_groups']}개 그룹)")
        
        return unique_articles, stats


def deduplicate_by_similarity(news_items: List[Dict[str, Any]], 
                            similarity_threshold: float = 0.7) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    유사도 기반 뉴스 중복 제거 함수 (기존 함수와 호환성 유지)
    
    Args:
        news_items: 뉴스 아이템 목록
        similarity_threshold: 유사도 임계값 (0~1, 기본값: 0.7)
        
    Returns:
        Tuple[중복 제거된 뉴스 목록, 통계 정보]
    """
    deduplicator = SimilarityDeduplicator(similarity_threshold)
    return deduplicator.deduplicate(news_items)


# 테스트용 함수
def test_similarity_deduplication():
    """유사도 중복 제거 테스트"""
    test_titles = [
        "코스맥스그룹, 中 HNC 2025 참가…글로벌 이너뷰티 시장 공략 확대",
        "코스맥스그룹, 中 HNC 2025서 스마트 뷰티 솔루션 제시",
        "코스맥스그룹, 中 HNC 2025 참가…이너뷰티 신제형·신소재 공개",
        "코스맥스그룹, 中 HNC 2025 참가… \"글로벌 이너뷰티 시장 공략 확대\"",
        "코스맥스그룹, 中 HNC 참가…글로벌 이너뷰티 시장 공략 확대",
        "코스맥스그룹, 中 HNC 2025 참가",
        "올리브영, 콜롬비아에 'K-뷰티' 쏜다…이재현 '글로벌 기업' 전략 첨병"
    ]
    
    # 테스트 데이터 생성
    test_news = []
    for i, title in enumerate(test_titles):
        test_news.append({
            'news_id': f'news_{i+1}',
            'title': title,
            'link': f'http://example.com/news/{i+1}',
            'pubDate': '2025-06-19 10:00:00',
            'description': f'테스트 기사 {i+1}',
            'source': '테스트신문',
            'keyword': '코스맥스'
        })
    
    # 중복 제거 실행
    unique_news, stats = deduplicate_by_similarity(test_news, similarity_threshold=0.6)
    
    print("=== 유사도 기반 중복 제거 테스트 결과 ===")
    print(f"원본 기사 수: {stats['original_count']}")
    print(f"중복 제거 후: {stats['unique_count']}")
    print(f"제거된 기사 수: {stats['removed_count']}")
    print()
    
    print("=== 최종 기사 목록 ===")
    for i, news in enumerate(unique_news, 1):
        print(f"{i}. {news['title']}")


if __name__ == "__main__":
    test_similarity_deduplication()
