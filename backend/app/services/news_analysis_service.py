#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
최적화된 관련성 분석 서비스 - WebSocket 실시간 통신 수정
"""

import json
import time
import logging
import asyncio
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
        # 고정 카테고리 제거 - 동적 필드 지원
        self.default_stats = {
            "total_items": 0,
            "successfully_analyzed": 0,
            "failed_analysis": 0,
            "processing_errors": 0
        }
        # 로깅 설정
        self.verbose_logging = logger.isEnabledFor(logging.DEBUG)
        self.progress_log_interval = 20  # 진행률 로그 간격 증가 (성능 개선)
        self.console_log_interval = 10   # 콘솔 출력 간격 증가
        # WebSocket 관련 로깅 분리
        self.websocket_logger = logging.getLogger(f"{__name__}.websocket")
    
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
            logger.info(f"뉴스 분석 시작: {file_path}, 모델: {model}, 배치처리: {use_batch_processing}, 배치크기: {batch_size}")
            
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
                analyzed_data, stats = await self._analyze_batch_with_realtime_websocket(
                    news_data, ai_client, model, compiled_prompt, session_id, batch_size, stop_flag_dict
                )
            else:
                analyzed_data, stats = await self._analyze_batch_optimized(
                    news_data, ai_client, model, compiled_prompt, session_id, stop_flag_dict
                )
            
            # 5. 결과 저장
            result_path = self._save_analysis_results(analyzed_data, file_path)
            
            logger.info(f"뉴스 분석 완료: {stats['successfully_analyzed']}/{stats['total_items']} 성공")
            
            return result_path, stats
            
        except Exception as e:
            logger.error(f"뉴스 분석 실패: {str(e)}")
            raise
    
    async def _analyze_batch_with_realtime_websocket(
        self,
        news_data: List[Dict[str, Any]],
        ai_client,
        model: str,
        compiled_prompt: Optional[str],
        session_id: Optional[str] = None,
        batch_size: int = 10,
        stop_flag_dict: Dict[str, bool] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """실시간 WebSocket 업데이트가 포함된 배치 분석"""
        
        total_items = len(news_data)
        analyzed_data = []
        
        # 통계 초기화
        stats = {
            "total_items": total_items,
            "successfully_analyzed": 0,
            "failed_analysis": 0,
            "processing_errors": 0,
            "field_statistics": {},
            "batch_size": batch_size
        }
        
        start_time = time.time()
        
        # 분석 시작 알림 (즉시 전송)
        if session_id and manager.is_session_active(session_id):
            await manager.send_progress_update(
                session_id=session_id,
                current=0,
                total=total_items,
                article_title="배치 분석 시작",
                force_send=True
            )
            logger.info(f"배치 분석 시작 메시지 전송: 0/{total_items}, 배치 크기: {batch_size}")
        
        # 배치 단위로 뉴스 데이터 분할
        batches = data_processor.batch_process_news_items(news_data, batch_size)
        logger.info(f"총 {len(batches)}개 배치로 분할됨 (각 배치당 최대 {batch_size}개)")
        
        current_item_index = 0
        
        for batch_idx, batch in enumerate(batches):
            # 중지 플래그 확인
            if stop_flag_dict and session_id and stop_flag_dict.get(session_id, False):
                logger.info(f"사용자 요청에 의해 배치 분석 중지 (배치 {batch_idx + 1}/{len(batches)})")
                
                if session_id and manager.is_session_active(session_id):
                    await manager.send_stop_message(session_id, current_item_index, total_items)
                
                self._finalize_stats(stats, start_time)
                stats["total_items"] = len(analyzed_data)
                stats["stopped_by_user"] = True
                return analyzed_data, stats
            
            try:
                logger.info(f"배치 {batch_idx + 1}/{len(batches)} 처리 시작 ({len(batch)}개 항목)")
                
                # 1. 배치 시작 메시지 (즉시 전송)
                if session_id and manager.is_session_active(session_id):
                    await manager.send_progress_update(
                        session_id=session_id,
                        current=current_item_index,
                        total=total_items,
                        article_title=f"배치 {batch_idx + 1} 시작 - AI 분석 중...",
                        force_send=True
                    )
                    logger.info(f"배치 {batch_idx + 1} 시작 메시지 전송 완료")
                
                # 2. AI 분석 시작 메시지 (즉시 전송)
                if session_id and manager.is_session_active(session_id):
                    await manager.send_progress_update(
                        session_id=session_id,
                        current=current_item_index,
                        total=total_items,
                        article_title=f"배치 {batch_idx + 1} AI 분석 진행 중... ({len(batch)}개 항목)",
                        force_send=True
                    )
                
                # 3. 실제 AI 분석 수행
                batch_results = await self._process_single_batch_with_websocket(
                    batch, ai_client, model, compiled_prompt, batch_idx + 1, len(batches),
                    session_id, total_items, current_item_index
                )
                
                # 4. 결과 병합 및 통계 업데이트
                for i, (news_item, analysis_result) in enumerate(zip(batch, batch_results)):
                    current_item_index += 1
                    
                    # 결과 병합
                    analyzed_item = {**news_item, **analysis_result}
                    analyzed_data.append(analyzed_item)
                    
                    # 통계 업데이트
                    self._update_stats(stats, analysis_result)
                
                # 5. 배치 완료 메시지 (즉시 전송)
                if session_id and manager.is_session_active(session_id):
                    # 첫 번째 결과의 카테고리를 샘플로 사용
                    sample_category = "unknown"
                    if batch_results:
                        first_result = batch_results[0]
                        first_field = next(iter(first_result.keys()), "unknown")
                        sample_category = str(first_result.get(first_field, "unknown"))
                    
                    await manager.send_progress_update(
                        session_id=session_id,
                        current=current_item_index,
                        total=total_items,
                        category=sample_category,
                        article_title=f"배치 {batch_idx + 1} 완료! ({len(batch)}개 항목 분석됨)",
                        force_send=True
                    )
                    logger.info(f"배치 {batch_idx + 1} 완료 메시지 전송 완료: {current_item_index}/{total_items}")
                
                logger.info(f"배치 {batch_idx + 1}/{len(batches)} 처리 완료 - {len(batch)}개 항목 완료")
                
            except Exception as e:
                logger.error(f"배치 {batch_idx + 1} 처리 실패: {str(e)}")
                
                # 배치 실패 시 기본값으로 처리
                for news_item in batch:
                    current_item_index += 1
                    default_result = data_processor._get_default_analysis_result()
                    analyzed_item = {**news_item, **default_result}
                    analyzed_data.append(analyzed_item)
                    self._update_stats(stats, default_result)
                    stats["processing_errors"] += 1
            
            # 배치 간 짧은 간격
            if batch_idx < len(batches) - 1:
                await asyncio.sleep(0.2)  # 200ms 대기
        
        # 최종 통계 계산
        self._finalize_stats(stats, start_time)
        
        # 최종 완료 메시지
        if session_id and manager.is_session_active(session_id):
            await asyncio.sleep(0.5)  # 완료 전 잠시 대기
            success = await manager.send_completion_message(session_id, stats)
            logger.info(f"WebSocket 최종 완료 메시지 전송 결과: {success}")
        
        return analyzed_data, stats
    
    async def _process_single_batch_with_websocket(
        self,
        batch: List[Dict[str, Any]],
        ai_client,
        model: str,
        compiled_prompt: Optional[str],
        batch_idx: int,
        total_batches: int,
        session_id: Optional[str] = None,
        total_items: int = 0,
        start_index: int = 0
    ) -> List[Dict[str, Any]]:
        """WebSocket 업데이트가 포함된 단일 배치 처리"""
        
        try:
            # 배치 프롬프트 생성
            batch_prompt = self._prepare_batch_prompt(batch, compiled_prompt)
            
            logger.info(f"배치 {batch_idx} AI 분석 시작 (항목 수: {len(batch)})")
            
            # AI 분석 요청
            response_text = ai_client.analyze(
                batch_prompt, 
                model=model, 
                batch_size=len(batch),
                max_tokens=min(len(batch) * 2000 + 3000, 40000)
            )
            
            logger.info(f"배치 {batch_idx} AI 응답 수신: {len(response_text)}문자")
            
            # AI 응답 완료 메시지
            if session_id and manager.is_session_active(session_id):
                await manager.send_progress_update(
                    session_id=session_id,
                    current=start_index + len(batch),
                    total=total_items,
                    article_title=f"배치 {batch_idx} AI 응답 완료 - 결과 파싱 중...",
                    force_send=True
                )
            
            # 응답 파싱
            batch_results = self._parse_batch_response(response_text, len(batch))
            
            logger.info(f"배치 {batch_idx} 파싱 완료: {len(batch_results)}개 결과")
            
            return batch_results
            
        except Exception as e:
            logger.error(f"배치 {batch_idx} 처리 실패: {str(e)}")
            
            # 오류 메시지 전송
            if session_id and manager.is_session_active(session_id):
                await manager.send_progress_update(
                    session_id=session_id,
                    current=start_index,
                    total=total_items,
                    article_title=f"배치 {batch_idx} 오류 발생 - 기본값으로 처리",
                    force_send=True
                )
            
            return [data_processor._get_default_analysis_result() for _ in batch]
    
    def _prepare_batch_prompt(self, batch: List[Dict[str, Any]], compiled_prompt: Optional[str]) -> str:
        """배치 분석용 프롬프트 생성"""
        
        if not compiled_prompt:
            raise ValidationError("프롬프트 템플릿이 설정되지 않았습니다.")
        
        batch_prompt = f"""{compiled_prompt}

다음 {len(batch)}개의 뉴스 기사를 각각 분석하여, 각 기사마다 하나씩 총 {len(batch)}개의 JSON 객체로 응답해주세요.
각 JSON 객체는 별도의 줄에 작성하고, 배열 형태가 아닌 개별 JSON 객체들로 응답해주세요.

분석할 뉴스 기사들:
"""
        
        for i, news_item in enumerate(batch, 1):
            title, content = data_processor.extract_text_content(news_item)
            title_truncated = title[:300] if title else ""
            content_truncated = content[:1500] if content else ""
            
            batch_prompt += f"""
{i}. 기사 제목: {title_truncated}
   기사 내용: {content_truncated}
"""
        
        batch_prompt += f"""

응답 형식: {len(batch)}개의 개별 JSON 객체 (각각 별도 줄)
예시:
{{"Category": "자사언급기사", "Confidence": 0.9, ...}}
{{"Category": "업계관련기사", "Confidence": 0.8, ...}}
...
"""
        
        return batch_prompt
    
    def _parse_batch_response(self, response_text: str, expected_count: int) -> List[Dict[str, Any]]:
        """배치 응답 파싱"""
        
        try:
            import re
            
            json_pattern = r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}'
            json_matches = re.findall(json_pattern, response_text, re.DOTALL)
            
            logger.info(f"추출된 JSON 객체 수: {len(json_matches)} (예상: {expected_count})")
            
            validated_results = []
            
            for i, json_str in enumerate(json_matches):
                try:
                    parsed_obj = json.loads(json_str)
                    
                    if isinstance(parsed_obj, dict):
                        validated_item = data_processor.safe_json_parse(json_str)
                        validated_results.append(validated_item)
                    else:
                        validated_results.append(data_processor._get_default_analysis_result())
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON 객체 {i+1} 파싱 실패: {e}")
                    validated_results.append(data_processor._get_default_analysis_result())
            
            return self._adjust_batch_result_count(validated_results, expected_count)
            
        except Exception as e:
            logger.error(f"배치 응답 파싱 실패: {e}")
            return [data_processor._get_default_analysis_result() for _ in range(expected_count)]
    
    def _adjust_batch_result_count(self, results: List[Dict[str, Any]], expected_count: int) -> List[Dict[str, Any]]:
        """결과 개수 조정"""
        
        if len(results) == expected_count:
            return results
        elif len(results) > expected_count:
            logger.warning(f"배치 결과 초과: {len(results)} > {expected_count}")
            return results[:expected_count]
        else:
            logger.warning(f"배치 결과 부족: {len(results)} < {expected_count}")
            while len(results) < expected_count:
                results.append(data_processor._get_default_analysis_result())
            return results
    
    def _update_stats(self, stats: Dict[str, Any], analysis_result: Dict[str, Any]):
        """통계 업데이트"""
        if analysis_result.get("analysis_status") == "failed":
            stats["failed_analysis"] += 1
        else:
            stats["successfully_analyzed"] += 1
        
        for key, value in analysis_result.items():
            if key not in stats["field_statistics"]:
                stats["field_statistics"][key] = {}
            
            value_str = str(value) if value is not None else "None"
            stats["field_statistics"][key][value_str] = stats["field_statistics"][key].get(value_str, 0) + 1
    
    def _finalize_stats(self, stats: Dict[str, Any], start_time: float):
        """최종 통계 계산"""
        stats["analysis_success_rate"] = (stats["successfully_analyzed"] / stats["total_items"] 
                                          if stats["total_items"] > 0 else 0)
        stats["analysis_success_percent"] = round(stats["analysis_success_rate"] * 100, 1)
        stats["processing_time"] = round((time.time() - start_time) / 60, 1)
    
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
    
    async def _analyze_batch_optimized(
        self,
        news_data: List[Dict[str, Any]],
        ai_client,
        model: str,
        compiled_prompt: Optional[str],
        session_id: Optional[str] = None,
        stop_flag_dict: Dict[str, bool] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """최적화된 배치 분석 수행 (단일 처리 방식)"""
        
        total_items = len(news_data)
        analyzed_data = []
        
        # 통계 초기화 (동적 필드)
        stats = {
            "total_items": total_items,
            "successfully_analyzed": 0,
            "failed_analysis": 0,
            "processing_errors": 0,
            "field_statistics": {},
            "batch_size": 1
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
                
                # 현재까지의 결과를 반환 (동적 필드)
                self._finalize_stats(stats, start_time)
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
                
                # WebSocket 진행률 전송 (모든 기사) - 연결 상태 확인
                if session_id and manager.is_session_active(session_id):
                    try:
                        success = await manager.send_progress_update(
                            session_id=session_id,
                            current=current_index - 1,
                            total=total_items,
                            article_title=title[:100]  # 제목 길이 제한
                        )
                        if not success:
                            logger.warning(f"WebSocket 연결 단절 감지: {session_id}")
                            # 연결이 끊어진 경우 WebSocket 메시지 전송 중단
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
                
                # WebSocket 완료 상태 전송 (동적 필드) - 연결 상태 확인
                if session_id and manager.is_session_active(session_id):
                    try:
                        # 첫 번째 분석 필드를 카테고리로 사용
                        first_field = next(iter(analysis_result.keys()), "unknown")
                        category_value = analysis_result.get(first_field, "unknown")
                        
                        # 완료된 기사는 항상 전송 (force_send=True)
                        success = await manager.send_progress_update(
                            session_id=session_id,
                            current=current_index,
                            total=total_items,
                            category=str(category_value),
                            confidence=analysis_result.get('confidence', 0),
                            article_title=title[:100],
                            force_send=True  # 완료된 기사는 항상 전송
                        )
                        if not success:
                            logger.debug(f"WebSocket 연결 단절 감지: {session_id}")
                    except Exception as ws_error:
                        logger.debug(f"WebSocket 완료 메시지 전송 실패: {ws_error}")
                
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
                # 최종 완료 메시지 전송 전에 약간의 지연
                await asyncio.sleep(0.5)
                
                if manager.is_session_active(session_id):
                    success = await manager.send_completion_message(session_id, stats)
                    logger.info(f"WebSocket 최종 완료 메시지 전송 결과: {success}, session_id={session_id}")
                    
                    # 완료 메시지 전송 후 추가 지연
                    await asyncio.sleep(1.0)
                else:
                    logger.warning(f"WebSocket 세션 비활성 - 완료 메시지 전송 실패: {session_id}")
                
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
            
            # 결과 로깅 (동적 필드)
            first_field = next(iter(result.keys()), "unknown")
            logger.info(f"파싱 결과 - 첫 번째 필드: {first_field}, 값: {result.get(first_field, 'N/A')}")
            
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
    
    def _handle_analysis_error(self, error: Exception, current_index: int, 
                              news_item: Dict[str, Any], analyzed_data: List[Dict[str, Any]], 
                              stats: Dict[str, Any]):
        """분석 오류 처리 (동적 필드)"""
        logger.error(f"뉴스 항목 {current_index} 분석 실패: {str(error)}")
        stats["processing_errors"] += 1
        
        # 기본값으로 결과 생성
        default_result = data_processor._get_default_analysis_result()
        analyzed_item = {**news_item, **default_result}
        analyzed_data.append(analyzed_item)
        
        # 오류 통계 업데이트
        self._update_stats(stats, default_result)
    
    def _log_progress(self, current: int, total: int, start_time: float):
        """진행률 로깅"""
        elapsed_time = time.time() - start_time
        processing_rate = current / (elapsed_time / 60) if elapsed_time > 0 else 0
        progress_percent = round((current / total) * 100, 1)
        
        logger.info(f"진행률: {current}/{total} ({progress_percent}%) - "
                   f"처리 속도: {round(processing_rate, 1)}기사/분")
    
    def _log_analysis_result(self, current: int, total: int, analysis_result: Dict[str, Any]):
        """분석 결과 로깅 (동적 필드)"""
        if self.verbose_logging:
            progress_percent = round((current / total) * 100, 1)
            
            # 첫 번째 필드를 카테고리로 사용
            first_field = next(iter(analysis_result.keys()), "unknown")
            category_value = analysis_result.get(first_field, "unknown")
            
            confidence = round(analysis_result.get('confidence', 0) * 100, 1)
            print(f"[분석 완료] {current}/{total} ({progress_percent}%) - "
                  f"카테고리: {category_value} (신뢰도: {confidence}%)")
    
    def _print_final_summary(self, stats: Dict[str, Any], start_time: float):
        """최종 요약 출력 (동적 필드)"""
        processing_time = round((time.time() - start_time) / 60, 1)
        processing_rate = round(stats['total_items'] / processing_time, 1) if processing_time > 0 else 0
        
        print(f"\n=== 분석 완료 ===")
        print(f"총 처리: {stats['total_items']}개")
        print(f"성공 분석: {stats['successfully_analyzed']}개 ({stats.get('analysis_success_percent', 0)}%)")
        print(f"실패 분석: {stats['failed_analysis']}개")
        print(f"오류: {stats['processing_errors']}개")
        print(f"소요 시간: {processing_time}분")
        print(f"처리 속도: {processing_rate}기사/분")
        print(f"배치 크기: {stats.get('batch_size', 1)}개")
        print("=" * 30)


# 전역 인스턴스
news_analysis_service = NewsAnalysisService()
