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
        session_id: str = None,
        batch_size: int = 10,
        use_batch_processing: bool = True,
        stop_flag_dict: Dict[str, bool] = None
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
            
            # 3. 프롬프트 준비 및 필수 검증
            compiled_prompt = None
            if prompt_template:
                compiled_prompt = prompt_template.get_compiled_prompt()
                logger.info(f"사용 프롬프트: {prompt_template.name}")
            
            if not compiled_prompt:
                raise ValidationError("프롬프트 템플릿이 설정되지 않았습니다. 프롬프트 관리 페이지에서 프롬프트 템플릿을 선택해주세요.")
            
            # 4. 배치 분석 수행
            if use_batch_processing:
                analyzed_data, stats = await self._analyze_batch_optimized_v2(
                    news_data, ai_client, model, compiled_prompt, session_id, batch_size, stop_flag_dict
                )
            else:
                analyzed_data, stats = await self._analyze_batch_optimized(
                    news_data, ai_client, model, compiled_prompt, session_id, stop_flag_dict
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
        session_id: Optional[str] = None,
        stop_flag_dict: Dict[str, bool] = None
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
        
        # 분석 시작 알림 - total 개수 미리 전송
        if session_id:
            try:
                await manager.send_progress_update(
                    session_id=session_id,
                    current=0,
                    total=total_items,
                    article_title="분석 시작"
                )
                logger.info(f"분석 시작 메시지 전송: 0/{total_items}")
            except Exception as ws_error:
                logger.warning(f"분석 시작 메시지 전송 실패: {ws_error}")
        
        for i, news_item in enumerate(news_data):
            current_index = i + 1
            
            # 중지 플래그 확인
            if stop_flag_dict and session_id and stop_flag_dict.get(session_id, False):
                logger.info(f"사용자 요청에 의해 분석 중지 ({current_index}/{total_items})")
                
                # 중지 상태를 알리는 WebSocket 메시지 전송
                if session_id:
                    try:
                        await manager.send_stop_message(session_id, current_index - 1, total_items)
                    except Exception as ws_error:
                        logger.warning(f"WebSocket 중지 메시지 전송 실패: {ws_error}")
                
                # 현재까지의 결과를 반환
                stats["relevant_ratio"] = (stats["relevant_items"] / len(analyzed_data) 
                                           if len(analyzed_data) > 0 else 0)
                stats["relevant_percent"] = round(stats["relevant_ratio"] * 100, 1)
                stats["processing_time"] = round((time.time() - start_time) / 60, 1)
                stats["total_items"] = len(analyzed_data)  # 실제 처리된 개수로 업데이트
                stats["stopped_by_user"] = True
                return analyzed_data, stats
            
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
                    try:
                        await manager.send_progress_update(
                            session_id=session_id,
                            current=current_index - 1,
                            total=total_items,
                            article_title=title[:100]  # 제목 길이 제한
                        )
                        if current_index % 1 == 0:  # 모든 기사마다 로그
                            logger.info(f"WebSocket 진행률 전송: {current_index-1}/{total_items}")
                    except Exception as ws_error:
                        logger.warning(f"WebSocket 메시지 전송 실패: {ws_error}")
                
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
                    try:
                        await manager.send_progress_update(
                            session_id=session_id,
                            current=current_index,
                            total=total_items,
                            category=analysis_result['category'],
                            confidence=analysis_result.get('confidence', 0),
                            article_title=title[:100]
                        )
                        if current_index % 1 == 0:  # 모든 기사마다 로그
                            logger.info(f"WebSocket 완료 전송: {current_index}/{total_items} - {analysis_result['category']}")
                    except Exception as ws_error:
                        logger.warning(f"WebSocket 완료 메시지 전송 실패: {ws_error}")
                
                # API 제한 대응 (간소화) - WebSocket 전송 후로 이동
                time.sleep(0.3)  # 0.3초로 단축
                
            except Exception as e:
                self._handle_analysis_error(e, current_index, news_item, analyzed_data, stats)
        
        # 최종 통계 계산
        self._finalize_stats(stats, start_time)
        
        # 완료 메시지
        if self.verbose_logging:
            self._print_final_summary(stats, start_time)
        
        if session_id:
            try:
                await manager.send_completion_message(session_id, stats)
                logger.info(f"WebSocket 최종 완료 메시지 전송: session_id={session_id}")
            except Exception as ws_error:
                logger.error(f"WebSocket 최종 메시지 전송 실패: {ws_error}")
        
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
            
            # 디버깅을 위한 로깅
            logger.info(f"단일 분석 시작: {title[:50]}...")
            if self.verbose_logging:
                logger.debug(f"사용 프롬프트: {prompt[:200]}...")
            
            response_text = ai_client.analyze(prompt, model=model)
            
            # AI 응답 로깅
            logger.info(f"AI 응답 수신: {len(response_text)}문자")
            if self.verbose_logging:
                logger.debug(f"AI 응답 내용: {response_text}")
            
            # 최적화된 JSON 파싱 사용
            result = data_processor.safe_json_parse(response_text)
            
            # 결과 로깅
            logger.info(f"파싱 결과 - 카테고리: {result['category']}, 신뢰도: {result['confidence']}")
            
            return result
            
        except Exception as e:
            logger.error(f"단일 항목 분석 실패 - 제목: {title[:50]}..., 오류: {str(e)}")
            if self.verbose_logging:
                import traceback
                logger.debug(f"전체 오류 스택: {traceback.format_exc()}")
            return data_processor._get_default_analysis_result()
    
    def _prepare_prompt_optimized(self, title: str, content: str, 
                                 compiled_prompt: Optional[str] = None) -> str:
        """최적화된 프롬프트 준비 - 템플릿 필수"""
        if not compiled_prompt:
            raise ValidationError("프롬프트 템플릿이 설정되지 않았습니다. 관련성 평가를 위해 프롬프트 템플릿을 선택해주세요.")
        
        # 텍스트 길이 제한 (성능 향상)
        title_truncated = title[:300] if title else ""
        content_truncated = content[:1500] if content else ""
        
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
    
    def _get_default_prompt(self) -> str:
        """기본 프롬프트 반환"""
        return """당신은 코스맥스의 화장품 업계 전문 분석가입니다. 주어진 뉴스 기사를 분석하여 다음 4개 카테고리로 분류해주세요.

분석 기준:
1. 자사언급기사: '코스맥스', '코스맥스엔비티'가 직접 언급된 기사
2. 업계관련기사: 화장품/뷰티 업계 관련 기사 (아모레퍼시픽, LG생활건강, 올리브영, K뷰티 등)
3. 건기식펫푸드관련기사: 건강기능식품이나 펫푸드 관련 기사
4. 기타: 위 카테고리에 해당하지 않는 기사

다음 JSON 형식으로 응답하세요:
{{
  "Category": "분류명",
  "Confidence": 신뢰도(0.0-1.0),
  "Keywords": ["키워드"],
  "Relation": 관계도(0.0-1.0),
  "Reason": "해당 기사의 관련도를 평가한 이유",
  "Importance": "기사의 중요도(상,중,하)",
  "Recommendation_reason": "추천하는 이유"
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

# 배치 처리 확장 함수들을 NewsAnalysisService에 추가
def _add_batch_processing_methods():
    """배치 처리 메서드들을 NewsAnalysisService 클래스에 동적 추가"""
    
    async def _analyze_batch_optimized_v2(
        self,
        news_data: List[Dict[str, Any]],
        ai_client,
        model: str,
        compiled_prompt: Optional[str],
        session_id: Optional[str] = None,
        batch_size: int = 10,
        stop_flag_dict: Dict[str, bool] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """배치 처리 최적화 분석 수행 (10개씩 처리)"""
        
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
        
        # 분석 시작 알림
        if session_id:
            try:
                await manager.send_progress_update(
                    session_id=session_id,
                    current=0,
                    total=total_items,
                    article_title="배치 분석 시작"
                )
                logger.info(f"배치 분석 시작 메시지 전송: 0/{total_items} (배치 크기: {batch_size})")
            except Exception as ws_error:
                logger.warning(f"분석 시작 메시지 전송 실패: {ws_error}")
        
        # 배치별로 처리
        for batch_start in range(0, total_items, batch_size):
            batch_end = min(batch_start + batch_size, total_items)
            batch_items = news_data[batch_start:batch_end]
            
            # 중지 플래그 확인
            if stop_flag_dict and session_id and stop_flag_dict.get(session_id, False):
                logger.info(f"사용자 요청에 의해 배치 분석 중지 ({batch_start}/{total_items})")
                
                # 중지 상태를 알리는 WebSocket 메시지 전송
                if session_id:
                    try:
                        await manager.send_stop_message(session_id, len(analyzed_data), total_items)
                    except Exception as ws_error:
                        logger.warning(f"WebSocket 중지 메시지 전송 실패: {ws_error}")
                
                # 현재까지의 결과를 반환
                self._finalize_stats(stats, start_time)
                stats["total_items"] = len(analyzed_data)  # 실제 처리된 개수로 업데이트
                stats["stopped_by_user"] = True
                return analyzed_data, stats
            
            try:
                # 배치 분석 수행
                batch_results = await self._analyze_batch_items(
                    batch_items, ai_client, model, compiled_prompt
                )
                
                # 배치 처리에서는 단일 기사도 실제로 단일 분석 함수를 호출하도록 수정
                for i, result in enumerate(batch_results):
                    current_index = batch_start + i + 1
                    
                    # 결과 병합
                    analyzed_item = {**batch_items[i], **result}
                    analyzed_data.append(analyzed_item)
                    
                    # 통계 업데이트
                    self._update_stats(stats, result)
                    
                    # WebSocket 진행률 전송
                    if session_id:
                        try:
                            title, _ = data_processor.extract_text_content(batch_items[i])
                            await manager.send_progress_update(
                                session_id=session_id,
                                current=current_index,
                                total=total_items,
                                category=result['category'],
                                confidence=result.get('confidence', 0),
                                article_title=title[:100]
                            )
                        except Exception as ws_error:
                            logger.warning(f"WebSocket 메시지 전송 실패: {ws_error}")
                
                # 진행률 로깅 (배치 단위)
                current_time = time.time()
                if current_time - last_log_time > 30:  # 30초마다 로깅
                    self._log_progress(batch_end, total_items, start_time)
                    last_log_time = current_time
                
                # 배치 완료 로깅
                if self.verbose_logging:
                    batch_progress = round((batch_end / total_items) * 100, 1)
                    print(f"[배치 완료] {batch_end}/{total_items} ({batch_progress}%) - 배치 크기: {len(batch_items)}")
                
                # API 제한 대응 (배치 단위)
                time.sleep(1.0)  # 배치간 1초 대기
                
            except Exception as e:
                logger.error(f"배치 {batch_start}-{batch_end} 처리 실패: {str(e)}")
                
                # 오류 발생시 기본값으로 처리
                for i, item in enumerate(batch_items):
                    current_index = batch_start + i + 1
                    default_result = data_processor._get_default_analysis_result()
                    analyzed_item = {**item, **default_result}
                    analyzed_data.append(analyzed_item)
                    
                    stats["processing_errors"] += 1
                    stats["categories"]["기타"] += 1
                    
                    # WebSocket 오류 전송
                    if session_id:
                        try:
                            title, _ = data_processor.extract_text_content(item)
                            await manager.send_progress_update(
                                session_id=session_id,
                                current=current_index,
                                total=total_items,
                                category="기타",
                                confidence=0,
                                article_title=f"[오류] {title[:90]}"
                            )
                        except Exception as ws_error:
                            logger.warning(f"WebSocket 오류 메시지 전송 실패: {ws_error}")
        
        # 최종 통계 계산
        self._finalize_stats(stats, start_time)
        
        # 완료 메시지
        if self.verbose_logging:
            self._print_final_summary(stats, start_time)
        
        if session_id:
            try:
                await manager.send_completion_message(session_id, stats)
                logger.info(f"WebSocket 최종 완료 메시지 전송: session_id={session_id}")
            except Exception as ws_error:
                logger.error(f"WebSocket 최종 메시지 전송 실패: {ws_error}")
        
        return analyzed_data, stats
    
    async def _analyze_batch_items(
        self,
        batch_items: List[Dict[str, Any]],
        ai_client,
        model: str,
        compiled_prompt: Optional[str]
    ) -> List[Dict[str, Any]]:
        """배치 아이템들을 한번에 분석 (진짜 배치 처리)"""
        
        try:
            # 배치용 프롬프트 준비
            batch_prompt = self._prepare_batch_prompt(batch_items, compiled_prompt)
            
            logger.info(f"배치 AI 분석 시작: {len(batch_items)}개 아이템")
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"배치 프롬프트: {batch_prompt[:500]}...")
            
            # AI 분석 수행
            response_text = ai_client.analyze(batch_prompt, model=model, batch_size=len(batch_items))
            
            logger.info(f"배치 AI 응답 수신: {len(response_text)}문자")
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"배치 AI 응답: {response_text}")
            
            # JSON 배열 파싱 - 이거이 핵심!
            batch_results = self._parse_batch_response_dynamic(response_text, len(batch_items))
            
            logger.info(f"배치 파싱 완료: {len(batch_results)}개 결과")
            return batch_results
            
        except Exception as e:
            logger.error(f"배치 아이템 분석 실패: {str(e)}")
            import traceback
            logger.debug(f"배치 오류 스택: {traceback.format_exc()}")
            
            # 오류 발생시 기본값 반환
            return [data_processor._get_default_analysis_result() for _ in batch_items]
    
    def _prepare_batch_prompt(
        self, 
        batch_items: List[Dict[str, Any]], 
        compiled_prompt: Optional[str] = None
    ) -> str:
        """배치 처리용 프롬프트 준비 - 템플릿 필수"""
        
        if not compiled_prompt:
            raise ValidationError("프롬프트 템플릿이 설정되지 않았습니다. 관련성 평가를 위해 프롬프트 템플릿을 선택해주세요.")
        
        # 커스텀 프롬프트에서 {title}, {content} 부분을 제거하고 기본 구조만 사용
        base_prompt = compiled_prompt.replace('{title}', '').replace('{content}', '').strip()
        # 마지막에 남은 "뉴스 기사:" 부분 제거
        if base_prompt.endswith('뉴스 기사:'):
            base_prompt = base_prompt[:-6].strip()
        
        # 배치 아이템들을 리스트로 추가
        articles_text = ""
        for i, item in enumerate(batch_items, 1):
            title, content = data_processor.extract_text_content(item)
            title_truncated = title[:200] if title else ""
            content_truncated = content[:800] if content else ""
            
            articles_text += f"""\n\n=== 기사 {i} ===
제목: {title_truncated}
내용: {content_truncated}
"""
        
        return f"""{base_prompt}

분석할 뉴스 기사들:
{articles_text}

응답 형식: 반드시 아래와 같이 JSON 배열로만 응답해주세요:
[
  {{
    "Category": "자사언급기사",
    "Confidence": 0.8,
    "Keywords": ["키워드1", "키워드2"],
    "Relation": 0.9,
    "Reason": "분석 이유",
    "Importance": "상",
    "Recommendation_reason": "추천 이유"
  }},
  {{
    "Category": "업계관련기사",
    "Confidence": 0.7,
    "Keywords": ["키워드3", "키워드4"],
    "Relation": 0.6,
    "Reason": "분석 이유",
    "Importance": "중",
    "Recommendation_reason": "추천 이유"
  }}
]
"""
    
    def _get_default_batch_prompt(self) -> str:
        """배치 처리용 기본 프롬프트 반환"""
        return """당신은 코스맥스의 화장품 업계 전문 분석가입니다. 주어진 여러 뉴스 기사들을 분석하여 각각을 다음 4개 카테고리로 분류해주세요.

분석 기준:
1. 자사언급기사: '코스맥스', '코스맥스엔비티'가 직접 언급된 기사
2. 업계관련기사: 화장품/뷰티 업계 관련 기사 (아모레퍼시픽, LG생활건강, 올리브영, K뷰티 등)
3. 건기식펫푸드관련기사: 건강기능식품이나 펫푸드 관련 기사
4. 기타: 위 카테고리에 해당하지 않는 기사

주의사항:
- 각 기사마다 Category, Confidence, Keywords, Relation, Reason, Importance, Recommendation_reason을 포함해주세요
- 순서대로 분석 결과를 JSON 배열로 반환해주세요
- 다른 설명 없이 JSON 배열만 반환해주세요"""
    
    def _parse_batch_response_dynamic(
        self, 
        response_text: str, 
        expected_count: int
    ) -> List[Dict[str, Any]]:
        """수정된 배치 응답 파싱 - JSON 배열 직접 파싱"""
        
        try:
            import re
            import json
            
            logger.info(f"배치 응답 파싱 시작: {len(response_text)}문자, 예상 개수: {expected_count}")
            
            # 1단계: JSON 배열 전체를 직접 파싱 시도
            try:
                # 응답에서 JSON 배열 부분만 추출
                cleaned_text = response_text.strip()
                
                # 코드 블록 제거
                if "```json" in cleaned_text:
                    start = cleaned_text.find("```json") + 7
                    end = cleaned_text.find("```", start)
                    if end != -1:
                        cleaned_text = cleaned_text[start:end].strip()
                elif "```" in cleaned_text:
                    # 일반 코드 블록에서 JSON 찾기
                    parts = cleaned_text.split("```")
                    for part in parts:
                        part = part.strip()
                        if part.startswith('[') and part.endswith(']'):
                            cleaned_text = part
                            break
                
                # JSON 배열 경계 찾기
                start_idx = cleaned_text.find('[')
                end_idx = cleaned_text.rfind(']')
                
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_array_str = cleaned_text[start_idx:end_idx + 1]
                    logger.info(f"추출된 JSON 배열: {json_array_str[:200]}...")
                    
                    # JSON 배열 직접 파싱
                    parsed_array = json.loads(json_array_str)
                    
                    if isinstance(parsed_array, list):
                        logger.info(f"JSON 배열 파싱 성공: {len(parsed_array)}개 항목")
                        
                        # 각 항목 검증 및 정규화
                        validated_results = []
                        for i, item in enumerate(parsed_array):
                            if isinstance(item, dict):
                                validated_item = self._validate_and_normalize_batch_item(item)
                                validated_results.append(validated_item)
                                logger.info(f"항목 {i+1} 검증 완료: {validated_item['category']}")
                            else:
                                logger.warning(f"항목 {i+1}이 딕셔너리가 아닙니다: {type(item)}")
                                validated_results.append(data_processor._get_default_analysis_result())
                        
                        # 결과 개수 조정
                        return self._adjust_batch_result_count(validated_results, expected_count)
                    
            except json.JSONDecodeError as e:
                logger.warning(f"JSON 배열 직접 파싱 실패: {e}")
            
            # 2단계: 개별 JSON 객체 추출 및 파싱
            logger.info("개별 JSON 객체 추출 방식으로 재시도")
            return self._extract_individual_json_objects(response_text, expected_count)
            
        except Exception as e:
            logger.error(f"배치 응답 파싱 전체 실패: {e}")
            return [data_processor._get_default_analysis_result() for _ in range(expected_count)]
    
    def _validate_and_normalize_batch_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """배치 처리를 위한 개별 항목 검증 및 정규화"""
        
        # 기본값으로 시작
        validated = data_processor._get_default_analysis_result()
        
        # 키 매핑 (대소문자 및 오타 처리)
        key_mapping = {
            'Category': 'category',
            'Confidence': 'confidence',
            'Keywords': 'keywords', 
            'Relation': 'relation',
            'Reason': 'reason',
            'Importance': 'importance',
            'Recommendation_reason': 'recommendation_reason',
            'Impoortance': 'importance',  # 오타 처리
            'Recommnedation_reason': 'recommendation_reason'  # 오타 처리
        }
        
        # 키 정규화
        normalized_item = {}
        for key, value in item.items():
            normalized_key = key_mapping.get(key, key.lower())
            normalized_item[normalized_key] = value
        
        # category 검증
        valid_categories = ['자사언급기사', '업계관련기사', '건기식펫푸드관련기사', '기타']
        if 'category' in normalized_item and normalized_item['category'] in valid_categories:
            validated['category'] = normalized_item['category']
        
        # confidence 검증 (0-1 범위)
        if 'confidence' in normalized_item:
            try:
                confidence = float(normalized_item['confidence'])
                if 0 <= confidence <= 1:
                    validated['confidence'] = confidence
            except (ValueError, TypeError):
                pass
        
        # relation 검증 (0-1 범위)
        if 'relation' in normalized_item:
            try:
                relation = float(normalized_item['relation'])
                if 0 <= relation <= 1:
                    validated['relation'] = relation
            except (ValueError, TypeError):
                pass
        
        # keywords 검증
        if 'keywords' in normalized_item and isinstance(normalized_item['keywords'], list):
            validated['keywords'] = [str(kw) for kw in normalized_item['keywords'][:5]]
        
        # importance 검증
        if 'importance' in normalized_item and normalized_item['importance'] in ['상', '중', '하']:
            validated['importance'] = normalized_item['importance']
        
        # 문자열 필드 검증
        if 'reason' in normalized_item and isinstance(normalized_item['reason'], str):
            validated['reason'] = normalized_item['reason']
        
        if 'recommendation_reason' in normalized_item and isinstance(normalized_item['recommendation_reason'], str):
            validated['recommendation_reason'] = normalized_item['recommendation_reason']
        
        return validated
    
    def _adjust_batch_result_count(self, results: List[Dict[str, Any]], expected_count: int) -> List[Dict[str, Any]]:
        """배치 결과 개수를 예상 개수에 맞게 조정"""
        
        if len(results) == expected_count:
            logger.info(f"결과 개수 일치: {len(results)}개")
            return results
        elif len(results) > expected_count:
            logger.warning(f"결과 초과: {len(results)} > {expected_count}, 앞의 {expected_count}개만 사용")
            return results[:expected_count]
        else:
            logger.warning(f"결과 부족: {len(results)} < {expected_count}, 기본값으로 보완")
            while len(results) < expected_count:
                results.append(data_processor._get_default_analysis_result())
            return results
    
    def _extract_individual_json_objects(self, response_text: str, expected_count: int) -> List[Dict[str, Any]]:
        """개별 JSON 객체 추출 및 파싱 (폴백 메서드)"""
        
        try:
            import re
            
            # JSON 객체 패턴으로 추출 (중첩된 중괄호도 처리)
            json_pattern = r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}'
            json_matches = re.findall(json_pattern, response_text, re.DOTALL)
            
            logger.info(f"추출된 JSON 객체 수: {len(json_matches)}")
            
            validated_results = []
            for i, json_str in enumerate(json_matches):
                try:
                    logger.info(f"JSON 객체 {i+1} 파싱 시도: {json_str[:100]}...")
                    
                    # data_processor.safe_json_parse 사용 (단일 처리와 동일)
                    result = data_processor.safe_json_parse(json_str)
                    validated_results.append(result)
                    logger.info(f"JSON 객체 {i+1} 파싱 성공: {result['category']}")
                    
                except Exception as e:
                    logger.warning(f"JSON 객체 {i+1} 파싱 실패: {e}")
                    validated_results.append(data_processor._get_default_analysis_result())
            
            return self._adjust_batch_result_count(validated_results, expected_count)
            
        except Exception as e:
            logger.error(f"개별 JSON 객체 추출 실패: {e}")
            return [data_processor._get_default_analysis_result() for _ in range(expected_count)]
    
    def _validate_analysis_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """분석 결과 유효성 검사 및 기본값 추가"""
        
        validated = data_processor._get_default_analysis_result()
        
        # 대소문자 변환을 위한 키 매핑
        key_mapping = {
            'Category': 'category',
            'Confidence': 'confidence', 
            'Keywords': 'keywords',
            'Relation': 'relation',
            'Reason': 'reason',
            'Importance': 'importance',
            'Recommendation_reason': 'recommendation_reason',
            'Impoortance': 'importance',  # 오타 처리
            'Recommnedation_reason': 'recommendation_reason'  # 오타 처리
        }
        
        # 키 매핑 적용
        normalized_result = {}
        for key, value in result.items():
            mapped_key = key_mapping.get(key, key.lower())
            normalized_result[mapped_key] = value
        
        # category 검사
        if 'category' in normalized_result and normalized_result['category'] in [
            '자사언급기사', '업계관련기사', '건기식펫푸드관련기사', '기타'
        ]:
            validated['category'] = normalized_result['category']
        
        # confidence 검사
        if 'confidence' in normalized_result and isinstance(normalized_result['confidence'], (int, float)):
            validated['confidence'] = max(0.0, min(1.0, float(normalized_result['confidence'])))
        
        # relation 검사
        if 'relation' in normalized_result and isinstance(normalized_result['relation'], (int, float)):
            validated['relation'] = max(0.0, min(1.0, float(normalized_result['relation'])))
        
        # keywords 검사
        if 'keywords' in normalized_result and isinstance(normalized_result['keywords'], list):
            validated['keywords'] = [str(kw) for kw in normalized_result['keywords'][:5]]  # 최대 5개
        
        # reason 검사
        if 'reason' in normalized_result and isinstance(normalized_result['reason'], str):
            validated['reason'] = normalized_result['reason']
        
        # importance 검사
        if 'importance' in normalized_result and normalized_result['importance'] in ['상', '중', '하']:
            validated['importance'] = normalized_result['importance']
        
        # recommendation_reason 검사
        if 'recommendation_reason' in normalized_result and isinstance(normalized_result['recommendation_reason'], str):
            validated['recommendation_reason'] = normalized_result['recommendation_reason']
        
        return validated
    
    # 메서드들을 클래스에 바인딩
    NewsAnalysisService._analyze_batch_optimized_v2 = _analyze_batch_optimized_v2
    NewsAnalysisService._analyze_batch_items = _analyze_batch_items
    NewsAnalysisService._prepare_batch_prompt = _prepare_batch_prompt
    NewsAnalysisService._parse_batch_response_dynamic = _parse_batch_response_dynamic
    NewsAnalysisService._validate_and_normalize_batch_item = _validate_and_normalize_batch_item
    NewsAnalysisService._adjust_batch_result_count = _adjust_batch_result_count
    NewsAnalysisService._extract_individual_json_objects = _extract_individual_json_objects
    NewsAnalysisService._validate_analysis_result = _validate_analysis_result

# 배치 처리 메서드 추가
_add_batch_processing_methods()
