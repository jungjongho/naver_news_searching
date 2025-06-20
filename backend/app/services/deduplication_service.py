#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GPT 임베딩 기반 뉴스 중복 제거 서비스 (개선된 버전)
고성능 처리를 위한 최적화된 임베딩 기반 중복 탐지
"""

import logging
import asyncio
import json
import time
import os
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN
import pickle

from app.core.config import settings
from app.core.file_manager import file_manager
from app.websocket.manager import manager as websocket_manager
from app.common.exceptions import NewsSearchException

logger = logging.getLogger(__name__)


class DeduplicationService:
    """GPT 임베딩 기반 뉴스 중복 제거 서비스"""
    
    def __init__(self):
        """서비스 초기화"""
        self.openai_client = None
        self.default_embedding_model = "text-embedding-3-small"  # 빠르고 경제적
        self.embedding_cache = {}  # 메모리 캐시
        
    def _get_openai_client(self, api_key: str) -> OpenAI:
        """OpenAI 클라이언트 인스턴스 생성/반환"""
        if not self.openai_client:
            self.openai_client = OpenAI(api_key=api_key, timeout=30.0)
        return self.openai_client
    
    async def deduplicate_news(
        self,
        file_path: str,
        api_key: str,
        similarity_threshold: float = 0.85,
        batch_size: int = 50,
        session_id: Optional[str] = None,
        stop_flag_dict: Optional[Dict[str, bool]] = None,
        embedding_model: str = "text-embedding-3-small"
    ) -> Tuple[str, Dict[str, Any]]:
        """
        GPT 임베딩을 사용한 고성능 뉴스 중복 제거
        
        Args:
            file_path: 처리할 파일 경로
            api_key: OpenAI API 키
            similarity_threshold: 유사도 임계값 (0.85-0.95 권장)
            batch_size: 임베딩 배치 크기
            session_id: 세션 ID
            stop_flag_dict: 중지 플래그
            
        Returns:
            Tuple[결과 파일 경로, 통계 정보]
        """
        start_time = time.time()
        
        try:
            # OpenAI 클라이언트 초기화
            client = self._get_openai_client(api_key)
            self.embedding_model = embedding_model or self.default_embedding_model
            
            # 파일 로드 및 검증
            full_file_path = file_manager.find_file_path(file_path)
            if not full_file_path:
                raise NewsSearchException(f"파일을 찾을 수 없습니다: {file_path}", "FILE_NOT_FOUND")
            
            df = pd.read_excel(full_file_path)
            df = self._normalize_column_names(df)
            total_items = len(df)
            
            logger.info(f"GPT 임베딩 기반 중복 제거 시작: {total_items}개 기사")
            
            # 진행률 알림
            if session_id:
                await websocket_manager.send_progress_update(
                    session_id, 0, total_items, None, None, 
                    "GPT 임베딩을 사용한 중복 제거를 시작합니다..."
                )
            
            # 1. 텍스트 준비 및 임베딩 생성
            await self._send_progress(session_id, 10, total_items, "텍스트 준비 중...")
            texts = self._prepare_texts(df)
            
            await self._send_progress(session_id, 20, total_items, "GPT 임베딩 생성 중...")
            embeddings = await self._get_embeddings_batch(client, texts, batch_size, session_id, total_items)
            
            # 2. 유사도 기반 중복 탐지
            await self._send_progress(session_id, 60, total_items, "중복 기사 탐지 중...")
            duplicate_groups = self._find_duplicates_with_clustering(
                embeddings, texts, df, similarity_threshold
            )
            
            # 3. 결과 생성 및 저장
            await self._send_progress(session_id, 80, total_items, "결과 생성 중...")
            deduplicated_df, stats = self._create_deduplicated_dataset(df, duplicate_groups)
            
            result_file_path = self._save_results(
                deduplicated_df, duplicate_groups, file_path, stats
            )
            
            # 통계 계산
            processing_time = (time.time() - start_time) / 60
            final_stats = {
                **stats,
                'processing_time': round(processing_time, 2),
                'similarity_threshold': similarity_threshold,
                'method': 'GPT 임베딩',
                'embedding_model': self.embedding_model
            }
            
            # 완료 알림
            if session_id:
                await websocket_manager.send_progress_update(
                    session_id, stats['deduplicated_count'], stats['original_count'],
                    None, None, f"중복 제거 완료! {stats['removed_count']}개 기사 제거됨",
                    force_send=True
                )
            
            logger.info(f"GPT 임베딩 중복 제거 완료: {stats['original_count']} → {stats['deduplicated_count']} "
                       f"({processing_time:.2f}분 소요)")
            
            return result_file_path, final_stats
            
        except Exception as e:
            logger.error(f"GPT 임베딩 중복 제거 중 오류: {str(e)}")
            if session_id:
                await websocket_manager.send_error_message(session_id, str(e))
            raise NewsSearchException(f"중복 제거 중 오류가 발생했습니다: {str(e)}", "EMBEDDING_ERROR")
    
    def _normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """컬럼명 정규화"""
        column_mapping = {
            '제목': 'title', 'Title': 'title', 'TITLE': 'title',
            '링크': 'url', 'Link': 'url', 'URL': 'url', 'url': 'url',
            '내용': 'content', 'Content': 'content', 'description': 'content',
            '날짜': 'date', 'Date': 'date', 'date': 'date',
            '출처': 'source', 'Source': 'source', 'source': 'source'
        }
        
        df_renamed = df.rename(columns=column_mapping)
        
        # 필수 컬럼 생성
        if 'title' not in df_renamed.columns:
            df_renamed['title'] = df_renamed.iloc[:, 0] if len(df_renamed.columns) > 0 else f"기본제목_{pd.Series(range(len(df_renamed)))}"
        if 'content' not in df_renamed.columns:
            df_renamed['content'] = df_renamed.get('title', '기본내용')
        if 'url' not in df_renamed.columns:
            df_renamed['url'] = f"http://example.com/news_{pd.Series(range(len(df_renamed)))}"
        if 'date' not in df_renamed.columns:
            df_renamed['date'] = pd.Timestamp.now().strftime('%Y-%m-%d')
            
        return df_renamed
    
    def _prepare_texts(self, df: pd.DataFrame) -> List[str]:
        """임베딩용 텍스트 준비 (제목 + 내용 결합)"""
        texts = []
        for _, row in df.iterrows():
            title = str(row.get('title', '')).strip()
            content = str(row.get('content', '')).strip()
            
            # 제목과 내용을 결합 (제목에 더 가중치)
            combined_text = f"{title}. {title}. {content}"  # 제목 2번 반복으로 가중치 부여
            
            # 텍스트 정제
            combined_text = combined_text.replace('\n', ' ').replace('\t', ' ')
            combined_text = ' '.join(combined_text.split())  # 여러 공백을 하나로
            
            # 너무 긴 텍스트는 자르기 (토큰 제한 고려)
            if len(combined_text) > 1500:
                combined_text = combined_text[:1500] + "..."
            
            texts.append(combined_text)
        
        return texts
    
    async def _get_embeddings_batch(
        self, 
        client: OpenAI, 
        texts: List[str], 
        batch_size: int,
        session_id: Optional[str],
        total_items: int
    ) -> np.ndarray:
        """배치 단위로 임베딩 생성 (비용 최적화)"""
        all_embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            try:
                # 진행률 업데이트
                progress = 20 + (40 * batch_num / total_batches)  # 20%~60% 구간
                if session_id:
                    await self._send_progress(
                        session_id, int(progress), total_items,
                        f"임베딩 생성 중... ({batch_num}/{total_batches} 배치)"
                    )
                
                # OpenAI 임베딩 API 호출
                response = client.embeddings.create(
                    model=self.embedding_model,
                    input=batch_texts,
                    encoding_format="float"
                )
                
                # 임베딩 추출
                batch_embeddings = [emb.embedding for emb in response.data]
                all_embeddings.extend(batch_embeddings)
                
                logger.info(f"배치 {batch_num}/{total_batches} 임베딩 생성 완료")
                
                # API 호출 제한 고려 (약간의 지연)
                if batch_num < total_batches:
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"배치 {batch_num} 임베딩 생성 실패: {str(e)}")
                raise NewsSearchException(f"임베딩 생성 실패: {str(e)}", "EMBEDDING_API_ERROR")
        
        logger.info(f"총 {len(all_embeddings)}개 임베딩 생성 완료")
        return np.array(all_embeddings)
    
    def _find_duplicates_with_clustering(
        self,
        embeddings: np.ndarray,
        texts: List[str],
        df: pd.DataFrame,
        similarity_threshold: float
    ) -> List[Dict[str, Any]]:
        """DBSCAN 클러스터링을 사용한 효율적인 중복 탐지"""
        
        # DBSCAN 매개변수 계산
        # similarity_threshold를 거리로 변환 (1 - cosine_similarity)
        eps = 1 - similarity_threshold
        min_samples = 2  # 최소 2개 기사가 있어야 중복 그룹
        
        logger.info(f"DBSCAN 클러스터링 시작 (eps={eps:.3f}, min_samples={min_samples})")
        
        # DBSCAN 클러스터링 수행
        clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
        cluster_labels = clustering.fit_predict(embeddings)
        
        # 클러스터별 그룹 생성
        duplicate_groups = []
        unique_labels = set(cluster_labels)
        unique_labels.discard(-1)  # 노이즈 제거
        
        for cluster_id in unique_labels:
            cluster_indices = np.where(cluster_labels == cluster_id)[0]
            
            if len(cluster_indices) < 2:  # 1개 기사는 중복이 아님
                continue
            
            # 클러스터 내 유사도 계산
            cluster_embeddings = embeddings[cluster_indices]
            similarity_matrix = cosine_similarity(cluster_embeddings)
            
            # 가장 대표적인 기사 선택 (클러스터 중심에 가장 가까운)
            centroid = np.mean(cluster_embeddings, axis=0)
            centroid_similarities = cosine_similarity([centroid], cluster_embeddings)[0]
            representative_idx = cluster_indices[np.argmax(centroid_similarities)]
            
            # 그룹 정보 생성
            articles = []
            similarity_scores = []
            
            for idx in cluster_indices:
                article_data = {
                    'index': int(idx),
                    'title': str(df.iloc[idx]['title']),
                    'url': str(df.iloc[idx]['url']),
                    'date': str(df.iloc[idx]['date']),
                    'content': str(df.iloc[idx]['content'])[:200] + "..." if len(str(df.iloc[idx]['content'])) > 200 else str(df.iloc[idx]['content'])
                }
                articles.append(article_data)
                
                # 대표 기사와의 유사도
                rep_idx_in_cluster = np.where(cluster_indices == representative_idx)[0][0]
                idx_in_cluster = np.where(cluster_indices == idx)[0][0]
                similarity = similarity_matrix[rep_idx_in_cluster][idx_in_cluster]
                similarity_scores.append(float(similarity))
            
            # 최대 유사도 계산
            max_similarity = float(np.max(similarity_matrix))
            
            duplicate_groups.append({
                'group_id': len(duplicate_groups),
                'representative_title': str(df.iloc[representative_idx]['title']),
                'representative_index': int(representative_idx),
                'articles': articles,
                'similarity_scores': similarity_scores,
                'count': len(articles),
                'max_similarity': max_similarity,
                'cluster_id': int(cluster_id)
            })
            
            logger.info(f"중복 그룹 {len(duplicate_groups)} 발견: {len(articles)}개 기사, "
                       f"최대 유사도: {max_similarity:.3f}")
        
        logger.info(f"총 {len(duplicate_groups)}개 중복 그룹 탐지됨")
        return duplicate_groups
    
    def _create_deduplicated_dataset(
        self, 
        df: pd.DataFrame, 
        duplicate_groups: List[Dict[str, Any]]
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """중복 제거된 데이터셋 생성"""
        indices_to_remove = set()
        
        # 각 그룹에서 대표 기사 제외한 나머지 제거
        for group in duplicate_groups:
            representative_idx = group['representative_index']
            for article in group['articles']:
                if article['index'] != representative_idx:
                    indices_to_remove.add(article['index'])
        
        # 중복 제거된 데이터프레임 생성
        deduplicated_df = df.drop(indices_to_remove).reset_index(drop=True)
        
        # 메타데이터 추가
        deduplicated_df['duplicate_group_id'] = -1
        deduplicated_df['is_representative'] = False
        deduplicated_df['removed_duplicates_count'] = 0
        deduplicated_df['embedding_similarity'] = 0.0
        
        # 통계 정보
        stats = {
            'original_count': len(df),
            'deduplicated_count': len(deduplicated_df),
            'removed_count': len(indices_to_remove),
            'duplicate_groups_count': len(duplicate_groups),
            'reduction_percentage': round((len(indices_to_remove) / len(df)) * 100, 1)
        }
        
        return deduplicated_df, stats
    
    def _save_results(
        self,
        deduplicated_df: pd.DataFrame,
        duplicate_groups: List[Dict[str, Any]],
        original_file_path: str,
        stats: Dict[str, Any]
    ) -> str:
        """결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(os.path.basename(original_file_path))[0]
        
        result_filename = f"{base_name}_embedding_deduplicated_{timestamp}.xlsx"
        result_file_path = os.path.join(settings.DEDUPLICATION_RESULTS_PATH, result_filename)
        
        os.makedirs(settings.DEDUPLICATION_RESULTS_PATH, exist_ok=True)
        
        # Excel 파일로 저장
        with pd.ExcelWriter(result_file_path, engine='openpyxl') as writer:
            # 중복 제거된 기사들
            deduplicated_df.to_excel(writer, sheet_name='임베딩_중복제거결과', index=False)
            
            # 중복 그룹 상세 정보
            if duplicate_groups:
                groups_data = []
                for group in duplicate_groups:
                    for i, article in enumerate(group['articles']):
                        groups_data.append({
                            '그룹ID': group['group_id'],
                            '클러스터ID': group.get('cluster_id', -1),
                            '대표기사여부': article['index'] == group['representative_index'],
                            '제목': article['title'],
                            'URL': article['url'],
                            '날짜': article['date'],
                            '내용미리보기': article['content'],
                            '임베딩유사도': round(group['similarity_scores'][i], 4),
                            '그룹최대유사도': round(group['max_similarity'], 4)
                        })
                
                groups_df = pd.DataFrame(groups_data)
                groups_df.to_excel(writer, sheet_name='임베딩_중복그룹상세', index=False)
            
            # 통계 정보
            stats_data = [
                ['항목', '값'],
                ['처리 방식', 'GPT 임베딩 기반'],
                ['임베딩 모델', self.embedding_model],
                ['원본 기사 수', stats['original_count']],
                ['중복 제거 후 기사 수', stats['deduplicated_count']],
                ['제거된 중복 기사 수', stats['removed_count']],
                ['중복 그룹 수', stats['duplicate_groups_count']],
                ['중복 제거율', f"{stats['reduction_percentage']}%"],
                ['처리 시간', f"{stats.get('processing_time', 0)}분"]
            ]
            
            stats_df = pd.DataFrame(stats_data[1:], columns=stats_data[0])
            stats_df.to_excel(writer, sheet_name='임베딩_통계정보', index=False)
        
        logger.info(f"임베딩 중복 제거 결과 저장: {result_file_path}")
        return result_file_path
    
    async def _send_progress(self, session_id: str, progress: int, total: int, message: str):
        """진행률 전송"""
        if session_id:
            await websocket_manager.send_progress_update(
                session_id, progress, total, None, None, message, force_send=True
            )


# 전역 서비스 인스턴스
deduplication_service = DeduplicationService()