#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
개선된 관련성 분석 서비스
"""

import json
import time
import logging
from typing import List, Dict, Any, Tuple, Optional
from app.services.ai_client import AIClientFactory
from app.services.file_service import file_service
from app.common.progress import progress_tracker
from app.common.exceptions import AnalysisError, ValidationError

logger = logging.getLogger(__name__)


class NewsAnalysisService:
    """뉴스 관련성 분석 서비스"""
    
    def __init__(self):
        self.default_categories = {
            "자사언급기사": 0,
            "업계관련기사": 0, 
            "건기식펫푸드관련기사": 0,
            "기타": 0
        }
    
    def analyze_news_batch(
        self,
        file_path: str,
        api_key: str,
        model: str = "gpt-4.1-nano",
        prompt_template=None,
        session_id: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """뉴스 배치 분석"""
        
        # 세션 ID 생성
        if not session_id:
            session_id = f"analysis_{int(time.time())}"
        
        try:
            # 1. 파일 로드
            logger.info(f"뉴스 분석 시작: {file_path}, 모델: {model}")
            news_data = file_service.load_news_data(file_path)
            
            if not news_data:
                raise ValidationError("파일에서 뉴스 데이터를 찾을 수 없습니다.")
            
            # 2. AI 클라이언트 생성
            progress_tracker.update_progress(
                session_id, 0, len(news_data), 'AI 클라이언트 초기화', ''
            )
            
            ai_client = AIClientFactory.create_client(model, api_key)
            
            # 3. 프롬프트 준비
            compiled_prompt = None
            if prompt_template:
                compiled_prompt = prompt_template.get_compiled_prompt()
                logger.info(f"사용 프롬프트: {prompt_template.name}")
            
            # 4. 배치 분석 수행
            analyzed_data, stats = self._analyze_batch(
                news_data, ai_client, model, compiled_prompt, session_id
            )
            
            # 5. 결과 저장
            original_name = file_service.generate_timestamped_filename(
                file_path, suffix="analyzed"
            )
            
            result_path = file_service.save_excel_data(
                analyzed_data, original_name, folder="relevance"
            )
            
            # 6. 다운로드 폴더 복사
            download_path = file_service.copy_to_downloads(result_path)
            
            # 7. 진행상황 정리
            progress_tracker.cleanup_session(session_id)
            
            logger.info(f"뉴스 분석 완료: {stats['relevant_items']}/{stats['total_items']} 관련")
            
            return result_path, stats
            
        except Exception as e:
            progress_tracker.update_progress(
                session_id, 0, 0, '분석 중 오류 발생', '', None, None, str(e)
            )
            raise
    
    def _analyze_batch(
        self,
        news_data: List[Dict[str, Any]],
        ai_client,
        model: str,
        compiled_prompt: Optional[str],
        session_id: str
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """실제 배치 분석 수행"""
        
        analyzed_data = []
        stats = {
            "total_items": len(news_data),
            "relevant_items": 0,
            "categories": self.default_categories.copy(),
            "processing_errors": 0
        }
        
        start_time = time.time()
        
        for i, news_item in enumerate(news_data):
            try:
                current_index = i + 1
                title = news_item.get("title", news_item.get("제목", ""))
                content = news_item.get("description", news_item.get("content", news_item.get("내용", "")))
                
                # 진행상황 업데이트
                elapsed_time = time.time() - start_time
                processing_rate = current_index / (elapsed_time / 60) if elapsed_time > 0 else 0
                
                current_stats = {
                    'relevant_items': stats['relevant_items'],
                    'irrelevant_items': current_index - 1 - stats['relevant_items'],
                    'errors': stats['processing_errors'],
                    'processing_rate': round(processing_rate, 1)
                }
                
                progress_tracker.update_progress(
                    session_id,
                    current_index - 1,
                    len(news_data),
                    f'기사 분석 중 ({current_index}/{len(news_data)})',
                    title[:50] if title else f'기사 {current_index}',
                    current_stats
                )
                
                # 분석 수행
                if not title and not content:
                    logger.warning(f"제목과 내용이 모두 비어있는 기사: {i}")
                    analysis_result = self._get_default_result()
                else:
                    analysis_result = self._analyze_single_item(
                        title, content, ai_client, model, compiled_prompt
                    )
                
                # 결과 병합
                news_item_analyzed = news_item.copy()
                news_item_analyzed.update(analysis_result)
                analyzed_data.append(news_item_analyzed)
                
                # 통계 업데이트
                category = analysis_result["category"]
                if category != "기타":
                    stats["relevant_items"] += 1
                
                if category in stats["categories"]:
                    stats["categories"][category] += 1
                else:
                    stats["categories"]["기타"] += 1
                
                # 완료 진행상황 업데이트
                final_stats = {
                    'relevant_items': stats['relevant_items'],
                    'irrelevant_items': current_index - stats['relevant_items'],
                    'errors': stats['processing_errors'],
                    'processing_rate': round(processing_rate, 1)
                }
                
                progress_tracker.update_progress(
                    session_id,
                    current_index,
                    len(news_data),
                    f'기사 분석 중 ({current_index}/{len(news_data)})',
                    '',
                    final_stats,
                    news_item_analyzed
                )
                
                # API 제한 대응
                time.sleep(0.5)
                
            except Exception as e:
                error_msg = f"뉴스 항목 {i} 분석 실패: {str(e)}"
                logger.error(error_msg)
                stats["processing_errors"] += 1
                
                # 기본값으로 결과 생성
                news_item_analyzed = news_item.copy()
                news_item_analyzed.update(self._get_default_result())
                analyzed_data.append(news_item_analyzed)
                stats["categories"]["기타"] += 1
                
                progress_tracker.update_progress(
                    session_id,
                    current_index,
                    len(news_data),
                    '오류 발생',
                    title[:50] if title else f'기사 {current_index}',
                    None,
                    None,
                    str(e)
                )
        
        # 최종 통계 계산
        stats["relevant_ratio"] = stats["relevant_items"] / stats["total_items"] if stats["total_items"] > 0 else 0
        stats["relevant_percent"] = round(stats["relevant_ratio"] * 100, 1)
        
        # 완료 상태 업데이트
        final_stats = {
            'relevant_items': stats['relevant_items'],
            'irrelevant_items': stats['total_items'] - stats['relevant_items'],
            'errors': stats['processing_errors'],
            'processing_rate': round(len(news_data) / ((time.time() - start_time) / 60), 1)
        }
        
        progress_tracker.update_progress(
            session_id,
            len(news_data),
            len(news_data),
            '분석 완료',
            '',
            final_stats
        )
        
        return analyzed_data, stats
    
    def _analyze_single_item(
        self,
        title: str,
        content: str,
        ai_client,
        model: str,
        compiled_prompt: Optional[str]
    ) -> Dict[str, Any]:
        """단일 뉴스 항목 분석"""
        try:
            prompt = self._prepare_prompt(title, content, compiled_prompt)
            response_text = ai_client.analyze(prompt, model=model)
            
            logger.debug(f"AI 응답: {repr(response_text)}")
            return self._parse_json_response(response_text)
            
        except Exception as e:
            logger.error(f"단일 항목 분석 실패: {str(e)}")
            return self._get_default_result()
    
    def _prepare_prompt(self, title: str, content: str, compiled_prompt: Optional[str] = None) -> str:
        """프롬프트 준비"""
        if compiled_prompt:
            if '{title}' in compiled_prompt and '{content}' in compiled_prompt:
                return compiled_prompt.format(title=title[:500], content=content[:2000])
            else:
                return f"""{compiled_prompt}

분석할 뉴스 기사:
제목: {title[:500]}
내용: {content[:2000]}"""
        else:
            return self._get_default_prompt().format(title=title[:500], content=content[:2000])
    
    def _get_default_prompt(self) -> str:
        """기본 프롬프트 반환"""
        return """
당신은 코스맥스의 화장품 업계 전문 분석가입니다. 주어진 뉴스 기사를 분석하여 다음 4개 카테고리로 분류해주세요.

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
내용: {content}
"""
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """JSON 응답 파싱"""
        try:
            # 코드 블록 제거
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                for part in response_text.split("```"):
                    if "{" in part and "}" in part:
                        response_text = part
                        break
            
            # JSON 객체 추출
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                response_text = response_text[start_idx:end_idx + 1]
            
            result = json.loads(response_text.strip())
            
            # 필수 필드 검증 및 기본값 설정
            result.setdefault("category", "기타")
            result.setdefault("confidence", 0.5)
            result.setdefault("keywords", [])
            
            # 카테고리명 정규화
            category_mapping = {
                "자사 언급기사": "자사언급기사",
                "업계 관련기사": "업계관련기사",
                "건기식·펫푸드 관련기사": "건기식펫푸드관련기사",
                "건강기능식품·펫푸드": "건기식펫푸드관련기사",
            }
            
            if result["category"] in category_mapping:
                result["category"] = category_mapping[result["category"]]
            
            # confidence 값 검증
            confidence = result["confidence"]
            if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                result["confidence"] = 0.5
            
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"JSON 파싱 실패, 기본값 반환: {str(e)}")
            return self._get_default_result()
    
    def _get_default_result(self) -> Dict[str, Any]:
        """기본 분석 결과 반환"""
        return {
            "category": "기타",
            "confidence": 0.0,
            "keywords": []
        }


# 전역 인스턴스
news_analysis_service = NewsAnalysisService()
