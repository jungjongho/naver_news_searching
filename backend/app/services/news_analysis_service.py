#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
최적화된 관련성 분석 서비스
- 로깅 최적화
- 배치 처리 개선
- 메모리 사용량 최적화
"""

import json
import time
import logging
from typing import List, Dict, Any, Tuple, Optional
from app.services.ai_client import AIClientFactory
from app.services.file_service import file_service
from app.common.exceptions import AnalysisError, ValidationError
from app.websocket.manager import manager
from app.utils.data_processor import data_processor

logger = logging.getLogger(__name__)


class NewsAnalysisService:
    """최적화된 뉴스 관련성 분석 서비스"""
    
    def __init__(self):
        self.default_categories = {
            "자사언급기사": 0,
            "업계관련기사": 0, 
            "건기식펫푸드관련기사": 0,
            "기타": 0
        }
        # 로깅 설정
        self.verbose_logging = logger.isEnabledFor(logging.DEBUG)
        self.progress_log_interval = 10  # 진행률 로그 간격
        self.console_log_interval = 5    # 콘솔 출력 간격
    
    async def analyze_news_batch(
        self,
        file_path: str,
        api_key: str,
        model: str = "gpt-4.1-nano",
        prompt_template=None,
        session_id: str = None
    ) -> Tuple[str, Dict[str, Any]]:
        """최적화된 뉴스 배치 분석"""
        
        try:
            # 1. 초기화 및 파일 로드
            logger.info(f"뉴스 분석 시작: {file_path}, 모델: {model}")
            if self.verbose_logging:
                print(f"\n=== 관련성 평가 시작 ===")
                print(f"파일: {file_path}")
                print(f"AI 모델: {model}")
            
            news_data = file_service.load_news_data(file_path)
            
            if not news_data:
                raise ValidationError("파일에서 뉴스 데이터를 찾을 수 없습니다.")
            
            total_count = len(news_data)
            logger.info(f"총 {total_count}개 기사 로드 완료")
            
            # 2. AI 클라이언트 생성
            ai_client = AIClientFactory.create_client(model, api_key)
            
            # 3. 프롬프트 준비
            compiled_prompt = None
            if prompt_template:
                compiled_prompt = prompt_template.get_compiled_prompt()
                logger.info(f"사용 프롬프트: {prompt_template.name}")
            
            # 4. 배치 분석 수행
            analyzed_data, stats = await self._analyze_batch_optimized(
                news_data, ai_client, model, compiled_prompt, session_id
            )
            
            # 5. 결과 저장
            result_path = self._save_analysis_results(analyzed_data, file_path)
            
            logger.info(f"뉴스 분석 완료: {stats['relevant_items']}/{stats['total_items']} 관련")
            
            return result_path, stats
            
        except Exception as e:
            logger.error(f"뉴스 분석 실패: {str(e)}")
            raise
    
    async def _analyze_batch_optimized(
        self,
        news_data: List[Dict[str, Any]],
        ai_client,
        model: str,
        compiled_prompt: Optional[str],
        session_id: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """최적화된 배치 분석 수행"""
        
        total_items = len(news_data)
        analyzed_data = []
        
        # 통계 초기화
        stats = {
            "total_items": total_items,
            "relevant_items": 0,
            "categories": self.default_categories.copy(),
            "processing_errors": 0
        }
        
        start_time = time.time()
        last_log_time = start_time
        
        for i, news_item in enumerate(news_data):
            current_index = i + 1
            
            try:
                # 제목과 내용 추출
                title, content = data_processor.extract_text_content(news_item)
                
                # 진행률 로깅 (간격 조절)
                current_time = time.time()
                if (current_index % self.progress_log_interval == 0 or 
                    current_index == total_items or 
                    current_time - last_log_time > 30):  # 30초마다 강제 로그
                    
                    self._log_progress(current_index, total_items, start_time)
                    last_log_time = current_time
                
                # WebSocket 진행률 전송 (모든 기사)
                if session_id:
                    await manager.send_progress_update(
                        session_id=session_id,
                        current=current_index - 1,
                        total=total_items,
                        article_title=title[:100]  # 제목 길이 제한
                    )
                
                # 분석 수행
                if not title and not content:
                    analysis_result = data_processor._get_default_analysis_result()
                else:
                    analysis_result = self._analyze_single_item_optimized(
                        title, content, ai_client, model, compiled_prompt
                    )
                
                # 결과 병합 (메모리 효율적)
                analyzed_item = {**news_item, **analysis_result}
                analyzed_data.append(analyzed_item)
                
                # 통계 업데이트
                self._update_stats(stats, analysis_result)
                
                # 콘솔 출력 (간격 조절)
                if current_index % self.console_log_interval == 0 or current_index == total_items:
                    self._log_analysis_result(current_index, total_items, analysis_result)
                
                # WebSocket 완료 상태 전송
                if session_id:
                    await manager.send_progress_update(
                        session_id=session_id,
                        current=current_index,
                        total=total_items,
                        category=analysis_result['category'],
                        confidence=analysis_result.get('confidence', 0),
                        article_title=title[:100]
                    )
                
                # API 제한 대응 (간소화)
                time.sleep(0.5)
                
            except Exception as e:
                self._handle_analysis_error(e, current_index, news_item, analyzed_data, stats)
        
        # 최종 통계 계산
        self._finalize_stats(stats, start_time)
        
        # 완료 메시지
        if self.verbose_logging:
            self._print_final_summary(stats, start_time)
        
        if session_id:
            await manager.send_completion_message(session_id, stats)
        
        return analyzed_data, stats
    
    def _analyze_single_item_optimized(
        self,
        title: str,
        content: str,
        ai_client,
        model: str,
        compiled_prompt: Optional[str]
    ) -> Dict[str, Any]:
        """최적화된 단일 뉴스 항목 분석"""
        try:
            prompt = self._prepare_prompt_optimized(title, content, compiled_prompt)
            response_text = ai_client.analyze(prompt, model=model)
            
            # 최적화된 JSON 파싱 사용
            return data_processor.safe_json_parse(response_text)
            
        except Exception as e:
            if self.verbose_logging:
                logger.error(f"단일 항목 분석 실패: {str(e)}")
            return data_processor._get_default_analysis_result()
    
    def _prepare_prompt_optimized(self, title: str, content: str, 
                                 compiled_prompt: Optional[str] = None) -> str:
        """최적화된 프롬프트 준비"""
        # 텍스트 길이 제한 (성능 향상)
        title_truncated = title[:300] if title else ""
        content_truncated = content[:1500] if content else ""
        
        if compiled_prompt:
            if '{title}' in compiled_prompt and '{content}' in compiled_prompt:
                return compiled_prompt.format(
                    title=title_truncated, 
                    content=content_truncated
                )
            else:
                return f"""{compiled_prompt}

분석할 뉴스 기사:
제목: {title_truncated}
내용: {content_truncated}"""
        else:
            return self._get_default_prompt().format(
                title=title_truncated, 
                content=content_truncated
            )
    
    def _get_default_prompt(self) -> str:
        """기본 프롬프트 반환"""
        return """당신은 코스맥스의 화장품 업계 전문 분석가입니다. 주어진 뉴스 기사를 분석하여 다음 4개 카테고리로 분류해주세요.

분석 기준:
1. 자사언급기사: '코스맥스', '코스맥스엔비티'가 직접 언급된 기사
2. 업계관련기사: 화장품/뷰티 업계 관련 기사 (아모레퍼시픽, LG생활건강, 올리브영, K뷰티 등)
3. 건기식펫푸드관련기사: 건강기능식품이나 펫푸드 관련 기사
4. 기타: 위 카테고리에 해당하지 않는 기사

반드시 다음 JSON 형식으로만 응답해주세요:
{{
  "category": "자사언급기사",
  "confidence": 0.8,
  "keywords": ["키워드1", "키워드2"]
}}

뉴스 기사:
제목: {title}
내용: {content}"""
    
    def _update_stats(self, stats: Dict[str, Any], analysis_result: Dict[str, Any]):
        """통계 업데이트"""
        category = analysis_result["category"]
        if category != "기타":
            stats["relevant_items"] += 1
        
        if category in stats["categories"]:
            stats["categories"][category] += 1
        else:
            stats["categories"]["기타"] += 1
    
    def _handle_analysis_error(self, error: Exception, current_index: int, 
                              news_item: Dict[str, Any], analyzed_data: List[Dict[str, Any]], 
                              stats: Dict[str, Any]):
        """분석 오류 처리"""
        logger.error(f"뉴스 항목 {current_index} 분석 실패: {str(error)}")
        stats["processing_errors"] += 1
        
        # 기본값으로 결과 생성
        default_result = data_processor._get_default_analysis_result()
        analyzed_item = {**news_item, **default_result}
        analyzed_data.append(analyzed_item)
        stats["categories"]["기타"] += 1
    
    def _log_progress(self, current: int, total: int, start_time: float):
        """진행률 로깅"""
        elapsed_time = time.time() - start_time
        processing_rate = current / (elapsed_time / 60) if elapsed_time > 0 else 0
        progress_percent = round((current / total) * 100, 1)
        
        logger.info(f"진행률: {current}/{total} ({progress_percent}%) - "
                   f"처리 속도: {round(processing_rate, 1)}기사/분")
    
    def _log_analysis_result(self, current: int, total: int, analysis_result: Dict[str, Any]):
        """분석 결과 로깅"""
        if self.verbose_logging:
            progress_percent = round((current / total) * 100, 1)
            confidence = round(analysis_result.get('confidence', 0) * 100, 1)
            print(f"[분석 완료] {current}/{total} ({progress_percent}%) - "
                  f"카테고리: {analysis_result['category']} (신뢰도: {confidence}%)")
    
    def _finalize_stats(self, stats: Dict[str, Any], start_time: float):
        """최종 통계 계산"""
        stats["relevant_ratio"] = (stats["relevant_items"] / stats["total_items"] 
                                  if stats["total_items"] > 0 else 0)
        stats["relevant_percent"] = round(stats["relevant_ratio"] * 100, 1)
        stats["processing_time"] = round((time.time() - start_time) / 60, 1)
    
    def _print_final_summary(self, stats: Dict[str, Any], start_time: float):
        """최종 요약 출력"""
        processing_time = round((time.time() - start_time) / 60, 1)
        processing_rate = round(stats['total_items'] / processing_time, 1) if processing_time > 0 else 0
        
        print(f"\n=== 관련성 평가 완료 ===")
        print(f"총 처리: {stats['total_items']}개")
        print(f"관련 기사: {stats['relevant_items']}개 ({stats['relevant_percent']}%)")
        print(f"오류: {stats['processing_errors']}개")
        print(f"소요 시간: {processing_time}분")
        print(f"처리 속도: {processing_rate}기사/분")
        print("=" * 30)
    
    def _save_analysis_results(self, analyzed_data: List[Dict[str, Any]], 
                              original_file_path: str) -> str:
        """분석 결과 저장"""
        original_name = file_service.generate_timestamped_filename(
            original_file_path, suffix="analyzed"
        )
        
        result_path = file_service.save_excel_data(
            analyzed_data, original_name, folder="relevance"
        )
        
        # 다운로드 폴더 복사
        file_service.copy_to_downloads(result_path)
        
        return result_path


# 전역 인스턴스
news_analysis_service = NewsAnalysisService()
