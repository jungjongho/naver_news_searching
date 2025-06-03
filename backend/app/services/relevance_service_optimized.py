#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import json
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from openai import OpenAI, AsyncOpenAI
import anthropic

logger = logging.getLogger(__name__)

class OptimizedRelevanceService:
    """
    최적화된 뉴스 기사 관련성 평가 서비스
    
    주요 최적화 기법:
    1. 배치 처리 (여러 기사를 한 번에 처리)
    2. 병렬 처리 (동시에 여러 API 호출)
    3. 비동기 처리
    4. 프롬프트 최적화 (토큰 수 감소)
    5. 스마트 딜레이 및 재시도
    6. 캐싱
    """
    
    def __init__(self, max_workers: int = 5, batch_size: int = 3):
        """
        Args:
            max_workers: 동시 실행할 스레드 수
            batch_size: 한 번에 처리할 기사 수 (배치 처리용)
        """
        self.openai_client = None
        self.async_openai_client = None
        self.anthropic_client = None
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.cache = {}  # 간단한 메모리 캐시
        
        # API 호출 통계
        self.api_calls = 0
        self.cache_hits = 0
        self.start_time = None
    
    def _init_openai_client(self, api_key: str):
        """OpenAI 클라이언트 초기화 (동기/비동기)"""
        try:
            self.openai_client = OpenAI(
                api_key=api_key,
                timeout=15.0,  # 타임아웃 단축
                max_retries=2   # 재시도 횟수 감소
            )
            
            # 비동기 클라이언트는 실제 사용 시에만 초기화
            logger.info("OpenAI 클라이언트 초기화 완료")
            return True
        except Exception as e:
            logger.error(f"OpenAI 클라이언트 초기화 실패: {str(e)}")
            return False
    
    def _get_optimized_batch_prompt(self) -> str:
        """배치 처리용 최적화된 프롬프트 (토큰 수 대폭 감소)"""
        return """코스맥스 뉴스 관련성 분석. 각 기사를 다음 기준으로 분류:

1=자사언급: 코스맥스 직접 언급
2=업계관련: 화장품/뷰티 업계 동향, 경쟁사, 기술, 규제
3=건기식펫푸드: 건강기능식품, 펫푸드 관련
4=기타: 관련성 낮음

JSON 배열로 응답:
[{{"id":1,"relevant":true,"category":"자사언급","confidence":0.9,"reason":"간단한이유"}}]

기사들:
{articles}"""
    
    def _get_single_prompt(self) -> str:
        """단일 기사용 간소화된 프롬프트"""
        return """코스맥스 관련성 분석.

분류: 1=자사언급, 2=업계관련, 3=건기식펫푸드, 4=기타

JSON 응답:
{{"relevant":true,"category":"분류","confidence":0.8,"reason":"이유"}}

제목: {title}
내용: {content}"""
    
    def _create_cache_key(self, title: str, content: str) -> str:
        """캐시 키 생성"""
        import hashlib
        content_hash = hashlib.md5(f"{title[:100]}{content[:200]}".encode()).hexdigest()
        return content_hash
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """캐시에서 결과 조회"""
        if cache_key in self.cache:
            self.cache_hits += 1
            return self.cache[cache_key]
        return None
    
    def _save_to_cache(self, cache_key: str, result: Dict[str, Any]):
        """캐시에 결과 저장"""
        self.cache[cache_key] = result
        
        # 캐시 크기 제한 (메모리 관리)
        if len(self.cache) > 1000:
            # 오래된 항목 일부 제거
            keys_to_remove = list(self.cache.keys())[:100]
            for key in keys_to_remove:
                del self.cache[key]
    
    def _prepare_batch_articles(self, news_batch: List[Dict[str, Any]]) -> str:
        """배치용 기사 텍스트 준비"""
        articles = []
        for i, item in enumerate(news_batch, 1):
            title = item.get("title", item.get("제목", ""))[:100]  # 제목 길이 제한
            content = item.get("description", item.get("content", item.get("내용", "")))[:300]  # 내용 길이 제한
            articles.append(f"{i}. 제목:{title} 내용:{content}")
        
        return "\n".join(articles)
    
    def _analyze_batch_threaded(self, news_batch: List[Dict[str, Any]], model: str) -> List[Dict[str, Any]]:
        """스레드 기반 배치 분석"""
        try:
            articles_text = self._prepare_batch_articles(news_batch)
            prompt = self._get_optimized_batch_prompt().format(articles=articles_text)
            
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "JSON 배열로만 응답하세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300 * len(news_batch)  # 배치 크기에 따라 토큰 수 조정
            )
            
            self.api_calls += 1
            result_text = response.choices[0].message.content.strip()
            
            # JSON 파싱
            try:
                results = json.loads(self._clean_json_response(result_text))
                if isinstance(results, list):
                    return results
                else:
                    # 단일 결과인 경우 리스트로 변환
                    return [results]
            except json.JSONDecodeError:
                logger.warning(f"배치 JSON 파싱 실패, 개별 처리로 전환")
                return self._fallback_individual_analysis(news_batch, model)
                
        except Exception as e:
            logger.error(f"배치 분석 오류: {str(e)}")
            return self._fallback_individual_analysis(news_batch, model)
    
    def _fallback_individual_analysis(self, news_batch: List[Dict[str, Any]], model: str) -> List[Dict[str, Any]]:
        """배치 처리 실패 시 개별 분석으로 폴백"""
        results = []
        for item in news_batch:
            try:
                result = self._analyze_single_sync(item, model)
                results.append(result)
            except Exception as e:
                logger.error(f"개별 분석 오류: {str(e)}")
                results.append(self._get_default_result())
        return results
    
    def _analyze_single_sync(self, news_item: Dict[str, Any], model: str) -> Dict[str, Any]:
        """동기 단일 기사 분석"""
        title = news_item.get("title", news_item.get("제목", ""))
        content = news_item.get("description", news_item.get("content", news_item.get("내용", "")))
        
        # 캐시 확인
        cache_key = self._create_cache_key(title, content)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        try:
            prompt = self._get_single_prompt().format(
                title=title[:200],
                content=content[:500]
            )
            
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "JSON으로만 응답하세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            self.api_calls += 1
            result_text = response.choices[0].message.content.strip()
            
            # JSON 파싱 및 정규화
            try:
                result = json.loads(self._clean_json_response(result_text))
                normalized_result = self._normalize_result(result)
                
                # 캐시에 저장
                self._save_to_cache(cache_key, normalized_result)
                
                return normalized_result
                
            except json.JSONDecodeError:
                return self._get_default_result()
                
        except Exception as e:
            logger.error(f"단일 분석 오류: {str(e)}")
            return self._get_default_result()
    
    def _normalize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """분석 결과 정규화"""
        # 카테고리 매핑
        category_mapping = {
            "자사언급": "자사 언급기사",
            "업계관련": "업계 관련기사", 
            "건기식펫푸드": "건강기능식품·펫푸드",
            "기타": "기타"
        }
        
        category = result.get("category", "기타")
        if category in category_mapping:
            category = category_mapping[category]
        
        return {
            "is_relevant": result.get("relevant", False),
            "category": category,
            "relevance_reason": result.get("reason", "분석 완료")[:100],  # 길이 제한
            "confidence": max(0.0, min(1.0, result.get("confidence", 0.5))),
            "keywords": result.get("keywords", [])[:3]  # 최대 3개
        }
    
    def _get_default_result(self) -> Dict[str, Any]:
        """기본 결과 반환"""
        return {
            "is_relevant": False,
            "category": "기타",
            "relevance_reason": "분석 실패",
            "confidence": 0.0,
            "keywords": []
        }
    
    def _clean_json_response(self, text: str) -> str:
        """JSON 응답 정리 (간소화 버전)"""
        # 코드 블록 제거
        if "```" in text:
            parts = text.split("```")
            for part in parts:
                if "{" in part or "[" in part:
                    text = part
                    break
        
        # JSON 객체/배열 추출
        start_chars = ["{", "["]
        end_chars = ["}", "]"]
        
        for start_char, end_char in zip(start_chars, end_chars):
            start_idx = text.find(start_char)
            end_idx = text.rfind(end_char)
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                return text[start_idx:end_idx + 1]
        
        return text.strip()
    
    def analyze_news_batch_optimized(self, news_data: List[Dict[str, Any]], api_key: str, model: str = "gpt-4o-mini") -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """최적화된 뉴스 배치 분석 (스레드 기반)"""
        self.start_time = time.time()
        self.api_calls = 0
        self.cache_hits = 0
        
        logger.info(f"최적화된 뉴스 배치 분석 시작: {len(news_data)}개 기사, 배치 크기: {self.batch_size}")
        
        # OpenAI 클라이언트 초기화
        if not self._init_openai_client(api_key):
            raise ValueError("OpenAI API 키가 유효하지 않습니다.")
        
        analyzed_data = []
        stats = {
            "total_items": len(news_data),
            "relevant_items": 0,
            "categories": {
                "자사 언급기사": 0,
                "업계 관련기사": 0,
                "건강기능식품·펫푸드": 0,
                "기타": 0
            },
            "processing_errors": 0,
            "api_calls": 0,
            "cache_hits": 0,
            "processing_time": 0
        }
        
        # 배치로 나누기
        batches = [news_data[i:i + self.batch_size] for i in range(0, len(news_data), self.batch_size)]
        
        # 스레드풀을 사용한 병렬 처리
        def process_batch(batch_data):
            batch, batch_idx = batch_data
            try:
                # 배치 분석 시도
                if len(batch) > 1:
                    results = self._analyze_batch_threaded(batch, model)
                    
                    # 결과와 원본 데이터 매핑
                    batch_analyzed = []
                    for i, (item, result) in enumerate(zip(batch, results)):
                        if isinstance(result, dict):
                            normalized_result = self._normalize_result(result)
                        else:
                            normalized_result = self._get_default_result()
                        
                        item_analyzed = item.copy()
                        item_analyzed.update(normalized_result)
                        batch_analyzed.append(item_analyzed)
                    
                    return batch_analyzed
                else:
                    # 단일 항목은 개별 처리
                    result = self._analyze_single_sync(batch[0], model)
                    item_analyzed = batch[0].copy()
                    item_analyzed.update(result)
                    return [item_analyzed]
                
            except Exception as e:
                logger.error(f"배치 {batch_idx} 처리 오류: {str(e)}")
                # 오류 발생 시 기본값으로 처리
                batch_analyzed = []
                for item in batch:
                    item_analyzed = item.copy()
                    item_analyzed.update(self._get_default_result())
                    batch_analyzed.append(item_analyzed)
                return batch_analyzed
        
        # ThreadPoolExecutor를 사용한 병렬 처리
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 배치 데이터와 인덱스를 함께 전달
            batch_data = [(batch, i) for i, batch in enumerate(batches)]
            
            # 작업 제출
            future_to_batch = {executor.submit(process_batch, data): data for data in batch_data}
            
            # 결과 수집
            processed_batches = 0
            for future in as_completed(future_to_batch):
                try:
                    batch_results = future.result()
                    analyzed_data.extend(batch_results)
                    
                    processed_batches += 1
                    processed_items = min(processed_batches * self.batch_size, len(news_data))
                    logger.info(f"배치 처리 진행: {processed_items}/{len(news_data)}")
                    
                    # API 호출 간 지연 (rate limiting 방지)
                    time.sleep(0.05)
                    
                except Exception as e:
                    logger.error(f"배치 결과 처리 오류: {str(e)}")
        
        # 결과 정렬 (원본 순서 유지)
        analyzed_data.sort(key=lambda x: news_data.index(next(
            item for item in news_data 
            if item.get("title", item.get("제목", "")) == x.get("title", x.get("제목", ""))
        )))
        
        # 통계 계산
        for item in analyzed_data:
            if item.get("is_relevant", False):
                stats["relevant_items"] += 1
            
            category = item.get("category", "기타")
            if category in stats["categories"]:
                stats["categories"][category] += 1
            else:
                stats["categories"]["기타"] += 1
        
        # 최종 통계
        stats["api_calls"] = self.api_calls
        stats["cache_hits"] = self.cache_hits
        stats["processing_time"] = round(time.time() - self.start_time, 2)
        stats["relevant_ratio"] = stats["relevant_items"] / stats["total_items"] if stats["total_items"] > 0 else 0
        stats["relevant_percent"] = round(stats["relevant_ratio"] * 100, 1)
        stats["avg_time_per_item"] = round(stats["processing_time"] / stats["total_items"], 2) if stats["total_items"] > 0 else 0
        
        logger.info(f"최적화된 분석 완료:")
        logger.info(f"  - 처리 시간: {stats['processing_time']}초")
        logger.info(f"  - 평균 항목당 시간: {stats['avg_time_per_item']}초")
        logger.info(f"  - API 호출: {stats['api_calls']}회")
        logger.info(f"  - 캐시 히트: {stats['cache_hits']}회")
        logger.info(f"  - 관련 기사: {stats['relevant_items']}/{stats['total_items']} ({stats['relevant_percent']}%)")
        
        return analyzed_data, stats
    
    # 기존 메서드들과의 호환성을 위한 래퍼
    def analyze_news_batch(self, news_data: List[Dict[str, Any]], api_key: str, model: str = "gpt-4o-mini") -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """호환성을 위한 래퍼"""
        return self.analyze_news_batch_optimized(news_data, api_key, model)
    
    def load_news_file(self, file_path: str) -> List[Dict[str, Any]]:
        """뉴스 파일 로드 (Excel)"""
        try:
            if file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path, engine='openpyxl')
            else:
                raise ValueError(f"지원하지 않는 파일 형식: {file_path}. XLSX 파일만 지원합니다.")
            
            news_data = df.to_dict('records')
            logger.info(f"파일 로드 완료: {file_path}, {len(news_data)}개 기사")
            return news_data
            
        except Exception as e:
            logger.error(f"파일 로드 실패: {file_path}, 오류: {str(e)}")
            raise
    
    def save_analyzed_results(self, analyzed_data: List[Dict[str, Any]], output_path: str, use_relevance_folder: bool = True) -> bool:
        """분석 결과 저장"""
        try:
            if use_relevance_folder:
                from app.core.config import settings
                file_name = os.path.basename(output_path)
                output_path = os.path.join(settings.RELEVANCE_RESULTS_PATH, file_name)
                os.makedirs(settings.RELEVANCE_RESULTS_PATH, exist_ok=True)
            
            df = pd.DataFrame(analyzed_data)
            
            # 컬럼명 정리
            column_mapping = {
                '제목': 'title',
                '링크': 'link',
                '발행일시': 'pubDate',
                '내용': 'description',
                '출처': 'source',
                '키워드': 'keyword'
            }
            
            df = df.rename(columns=column_mapping)
            
            # 컬럼 순서 정리
            columns_order = ['title', 'link', 'pubDate', 'description', 'source', 'originallink', 'keyword',
                           'is_relevant', 'category', 'relevance_reason', 'confidence', 'keywords']
            
            available_columns = [col for col in columns_order if col in df.columns]
            remaining_columns = [col for col in df.columns if col not in columns_order]
            final_columns = available_columns + remaining_columns
            
            df = df[final_columns]
            
            # XLSX 파일로 저장
            if not output_path.endswith('.xlsx'):
                output_path = output_path.rsplit('.', 1)[0] + '.xlsx' if '.' in output_path else output_path + '.xlsx'
            
            df.to_excel(output_path, index=False, engine='openpyxl')
            logger.info(f"분석 결과 저장 완료: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"분석 결과 저장 실패: {output_path}, 오류: {str(e)}")
            return False

# 기존 클래스와의 호환성을 위한 alias
RelevanceService = OptimizedRelevanceService
