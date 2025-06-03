#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import json
import time
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from openai import OpenAI
import anthropic

logger = logging.getLogger(__name__)

class RelevanceService:
    """
    뉴스 기사 관련성 평가 서비스 (개선된 버전)
    """
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
    
    def _init_openai_client(self, api_key: str):
        """OpenAI 클라이언트 초기화"""
        try:
            self.openai_client = OpenAI(
                api_key=api_key,
                timeout=30.0
            )
            
            # API 키 유효성 테스트
            models = self.openai_client.models.list()
            logger.info(f"OpenAI 클라이언트 초기화 완료, 사용 가능한 모델 수: {len(models.data)}")
            print(models)
            return True
        except Exception as e:
            logger.error(f"OpenAI 클라이언트 초기화 실패: {str(e)}")
            return False
    
    def _map_model_name(self, model: str) -> str:
        """모델명 매핑"""
        model_mapping = {
            'gpt-4.1-nano': 'gpt-4.1-nano',  # 실제 사용 가능한 모델로 매핑
            'gpt-3.5-turbo': 'gpt-3.5-turbo',
            'gpt-4': 'gpt-4',
            'gpt-4o': 'gpt-4o',
            'gpt-4o-mini': 'gpt-4o-mini',
            'gpt-4-turbo': 'gpt-4-turbo-preview',
            'claude-instant-1': 'claude-instant-1',
            'claude-2': 'claude-2',
        }
        
        mapped_model = model_mapping.get(model, model)
        if mapped_model != model:
            logger.info(f"모델명 매핑: {model} -> {mapped_model}")
        return mapped_model
    
    def _init_anthropic_client(self, api_key: str):
        """Anthropic 클라이언트 초기화"""
        try:
            self.anthropic_client = anthropic.Anthropic(api_key=api_key)
            logger.info("Anthropic 클라이언트 초기화 complete")
            return True
        except Exception as e:
            logger.error(f"Anthropic 클라이언트 초기화 실패: {str(e)}")
            return False
    
    def _get_analysis_prompt(self) -> str:
        """뉴스 관련성 분석을 위한 프롬프트"""
        return """
당신은 코스맥스의 화장품 업계 전문 분석가입니다. 주어진 뉴스 기사를 분석하여 코스맥스 임직원들에게 유용한 비즈니스 인사이트를 제공할 수 있는지 평가해주세요.

분석 기준:
1. 자사 언급기사: '코스맥스'가 직접 언급된 기사
2. 업계 관련기사: 화장품/뷰티 업계의 트렌드, 시장 동향, 규제 변화, 기술 혁신, 소비자 행동 변화 등 사업에 영향을 미치는 기사
3. 건강기능식품·펫푸드: 건강기능식품이나 펫푸드 관련 기사 (코스맥스의 사업 영역)
4. 기타: 위 카테고리에 해당하지 않지만 간접적으로 사업에 참고가 될 수 있는 기사

평가 시 고려사항:
- 코스맥스의 주요 사업 영역 (화장품 ODM/OEM, K-뷰티, 건강기능식품, 펫케어)
- 글로벌 시장 동향 및 경쟁사 정보
- 신기술, 신소재, 지속가능성 관련 이슈
- 규제 변화 및 정책 동향
- 소비자 트렌드 및 브랜드 전략

반드시 다음 JSON 형식으로만 응답해주세요:
{{
  "is_relevant": true or false,
  "category": "자사 언급기사",
  "relevance_reason": "관련성 판단 이유",
  "confidence": float (0~1),
  "keywords": ["키워드1", "키워드2"]
}}

뉴스 기사:
제목: {title}
내용: {content}

"""
    
    def _backup_parse_response(self, response_text: str) -> Dict[str, Any]:
        """백업 응답 파싱 - JSON 파싱 실패 시 키워드 기반으로 분석"""
        try:
            # 기본값
            result = {
                "is_relevant": False,
                "category": "기타",
                "relevance_reason": "백업 파싱 사용",
                "confidence": 0.3,
                "keywords": []
            }
            
            response_lower = response_text.lower()
            
            # is_relevant 추출
            if "true" in response_lower:
                result["is_relevant"] = True
            elif "false" in response_lower:
                result["is_relevant"] = False
            
            # category 추출
            if "자사 언급" in response_text or "자사언급" in response_text:
                result["category"] = "자사 언급기사"
            elif "업계 관련" in response_text or "업계관련" in response_text:
                result["category"] = "업계 관련기사"
            elif "건강기능식품" in response_text or "펫푸드" in response_text:
                result["category"] = "건강기능식품·펫푸드"
            else:
                result["category"] = "기타"
            
            # 간단한 키워드 추출
            keywords = []
            keyword_candidates = ["화장품", "아모레", "LG생건", "코스닥", "매출", "신제품"]
            for keyword in keyword_candidates:
                if keyword in response_text:
                    keywords.append(keyword)
            
            result["keywords"] = keywords[:3]  # 최대 3개
            
            return result
            
        except Exception as e:
            logger.error(f"백업 파싱도 실패: {str(e)}")
            return {
                "is_relevant": False,
                "category": "기타",
                "relevance_reason": "파싱 완전 실패",
                "confidence": 0.0,
                "keywords": []
            }
    
    def _clean_json_response(self, text: str) -> str:
        """AI 응답에서 JSON 부분만 추출하고 정리"""
        try:
            # 1. 코드 블록 제거
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                # 일반 코드 블록도 확인
                parts = text.split("```")
                for part in parts:
                    if "{" in part and "}" in part:
                        text = part
                        break
            
            # 2. 앞뒤 공백 제거
            text = text.strip()
            
            # 3. JSON 객체 찾기
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                text = text[start_idx:end_idx + 1]
            
            # 4. 개행 및 불필요한 공백 정리
            lines = text.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if line:
                    cleaned_lines.append(line)
            
            text = ' '.join(cleaned_lines)
            
            return text
            
        except Exception as e:
            logger.error(f"JSON 정리 중 오류: {str(e)}")
            return text
    
    def _analyze_single_news_openai(self, title: str, content: str, model: str = "gpt-3.5-turbo") -> Dict[str, Any]:
        """OpenAI를 사용한 단일 뉴스 분석"""
        try:
            actual_model = self._map_model_name(model)
            prompt = self._get_analysis_prompt().format(
                title=title[:500],  # 제목 길이 제한
                content=content[:2000]  # 내용 길이 제한
            )
            
            response = self.openai_client.chat.completions.create(
                model=actual_model,
                messages=[
                    {"role": "system", "content": "당신은 화장품 업계 전문 분석가입니다. 반드시 유효한 JSON 형식으로만 응답하세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content.strip()
            logger.debug(f"OpenAI 원본 응답: {repr(result_text)}")
            
            # JSON 정리 및 파싱
            try:
                cleaned_json = self._clean_json_response(result_text)
                logger.debug(f"정리된 JSON: {repr(cleaned_json)}")
                
                result = json.loads(cleaned_json)
                
                # 필수 필드 검증 및 기본값 설정
                result.setdefault("is_relevant", False)
                result.setdefault("category", "기타")
                result.setdefault("relevance_reason", "분석 결과 없음")
                
                # confidence 값 안전성 검증
                confidence = result.get("confidence", 0.5)
                if isinstance(confidence, (int, float)):
                    import math
                    if math.isnan(confidence) or math.isinf(confidence):
                        confidence = 0.5
                    elif confidence < 0:
                        confidence = 0.0
                    elif confidence > 1:
                        confidence = 1.0
                else:
                    confidence = 0.5
                result["confidence"] = confidence
                
                result.setdefault("keywords", [])
                
                logger.debug(f"파싱 성공: {result}")
                return result
                
            except (json.JSONDecodeError, ValueError, IndexError) as e:
                logger.warning(f"JSON 파싱 실패, 백업 파싱 시도: {str(e)}")
                logger.debug(f"실패한 응답: {repr(result_text)}")
                
                # 백업 파싱 시도
                backup_result = self._backup_parse_response(result_text)
                logger.info(f"백업 파싱 결과: {backup_result}")
                return backup_result
                
        except Exception as e:
            logger.error(f"OpenAI 분석 중 오류: {str(e)}")
            return {
                "is_relevant": False,
                "category": "기타", 
                "relevance_reason": f"API 오류: {str(e)[:30]}",
                "confidence": 0.0,
                "keywords": []
            }
    
    def _analyze_single_news_anthropic(self, title: str, content: str, model: str = "claude-instant-1") -> Dict[str, Any]:
        """Anthropic Claude를 사용한 단일 뉴스 분석"""
        try:
            actual_model = self._map_model_name(model)
            prompt = self._get_analysis_prompt().format(title=title, content=content)
            
            response = self.anthropic_client.messages.create(
                model=actual_model,
                max_tokens=500,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            result_text = response.content[0].text.strip()
            
            # JSON 파싱 시도
            try:
                cleaned_json = self._clean_json_response(result_text)
                result = json.loads(cleaned_json)
                
                # 필수 필드 검증 및 기본값 설정
                result.setdefault("is_relevant", False)
                result.setdefault("category", "기타")
                result.setdefault("relevance_reason", "분석 결과 없음")
                
                # confidence 값 안전성 검증
                confidence = result.get("confidence", 0.5)
                if isinstance(confidence, (int, float)):
                    import math
                    if math.isnan(confidence) or math.isinf(confidence):
                        confidence = 0.5
                    elif confidence < 0:
                        confidence = 0.0
                    elif confidence > 1:
                        confidence = 1.0
                else:
                    confidence = 0.5
                result["confidence"] = confidence
                
                result.setdefault("keywords", [])
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 오류: {str(e)}, 응답: {result_text}")
                return self._backup_parse_response(result_text)
                
        except Exception as e:
            logger.error(f"Anthropic 분석 오류: {str(e)}")
            return {
                "is_relevant": False,
                "category": "기타",
                "relevance_reason": f"분석 실패: {str(e)[:30]}",
                "confidence": 0.0,
                "keywords": []
            }
    
    def analyze_news_batch(self, news_data: List[Dict[str, Any]], api_key: str, model: str = "gpt-3.5-turbo") -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """뉴스 배치 분석"""
        logger.info(f"뉴스 배치 분석 시작: {len(news_data)}개 기사, 모델: {model}")
        
        # 모델명 매핑
        actual_model = self._map_model_name(model)
        
        # API 클라이언트 초기화
        if actual_model.startswith("gpt"):
            if not self._init_openai_client(api_key):
                raise ValueError("OpenAI API 키가 유효하지 않습니다.")
            analyze_func = self._analyze_single_news_openai
        elif actual_model.startswith("claude"):
            if not self._init_anthropic_client(api_key):
                raise ValueError("Anthropic API 키가 유효하지 않습니다.")
            analyze_func = self._analyze_single_news_anthropic
        else:
            raise ValueError(f"지원하지 않는 모델: {model}")
        
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
            "backup_parsing_used": 0,
            "api_errors": 0
        }
        
        for i, news_item in enumerate(news_data):
            try:
                logger.info(f"분석 진행: {i+1}/{len(news_data)}")
                
                title = news_item.get("title", news_item.get("제목", ""))
                content = news_item.get("description", news_item.get("content", news_item.get("내용", "")))
                
                if not title and not content:
                    logger.warning(f"제목과 내용이 모두 비어있는 기사 발견: {i}")
                    analysis_result = {
                        "is_relevant": False,
                        "category": "기타",
                        "relevance_reason": "제목과 내용이 비어있음",
                        "confidence": 0.0,
                        "keywords": []
                    }
                else:
                    # 실제 분석 수행
                    analysis_result = analyze_func(title, content, model)
                    
                    # 통계 업데이트
                    if "백업 파싱 사용" in analysis_result.get("relevance_reason", ""):
                        stats["backup_parsing_used"] += 1
                    elif "API 오류" in analysis_result.get("relevance_reason", ""):
                        stats["api_errors"] += 1
                
                # 원본 데이터에 분석 결과 추가
                news_item_analyzed = news_item.copy()
                
                # confidence 값 안전성 검증
                confidence = analysis_result.get("confidence", 0.5)
                if isinstance(confidence, float):
                    import pandas as pd
                    if pd.isna(confidence) or confidence == float('inf') or confidence == float('-inf'):
                        confidence = 0.5
                    elif confidence < 0:
                        confidence = 0.0
                    elif confidence > 1:
                        confidence = 1.0
                else:
                    confidence = 0.5
                
                news_item_analyzed.update({
                    "is_relevant": analysis_result["is_relevant"],
                    "category": analysis_result["category"],
                    "relevance_reason": analysis_result["relevance_reason"],
                    "confidence": confidence,
                    "keywords": analysis_result.get("keywords", [])
                })
                
                analyzed_data.append(news_item_analyzed)
                
                # 통계 업데이트
                if analysis_result["is_relevant"]:
                    stats["relevant_items"] += 1
                
                category = analysis_result["category"]
                if category in stats["categories"]:
                    stats["categories"][category] += 1
                else:
                    stats["categories"]["기타"] += 1
                
                # API 호출 제한을 위한 딜레이
                time.sleep(0.1)  # 100ms 딜레이
                
            except Exception as e:
                logger.error(f"뉴스 항목 {i} 분석 중 오류: {str(e)}")
                stats["processing_errors"] += 1
                
                # 오류 발생한 항목도 기본값으로 추가
                news_item_analyzed = news_item.copy()
                news_item_analyzed.update({
                    "is_relevant": False,
                    "category": "기타",
                    "relevance_reason": f"분석 오류: {str(e)[:30]}",
                    "confidence": 0.0,
                    "keywords": []
                })
                analyzed_data.append(news_item_analyzed)
                stats["categories"]["기타"] += 1
        
        # 최종 통계 계산
        stats["relevant_ratio"] = stats["relevant_items"] / stats["total_items"] if stats["total_items"] > 0 else 0
        stats["relevant_percent"] = round(stats["relevant_ratio"] * 100, 1)
        
        logger.info(f"뉴스 배치 분석 완료:")
        logger.info(f"  - 관련 기사: {stats['relevant_items']}/{stats['total_items']} ({stats['relevant_percent']}%)")
        logger.info(f"  - 백업 파싱 사용: {stats['backup_parsing_used']}개")
        logger.info(f"  - API 오류: {stats['api_errors']}개")
        logger.info(f"  - 처리 오류: {stats['processing_errors']}개")
        
        return analyzed_data, stats
    
    def load_news_file(self, file_path: str) -> List[Dict[str, Any]]:
        """뉴스 파일 로드 (Excel)"""
        try:
            if file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path, engine='openpyxl')
            else:
                raise ValueError(f"지원하지 않는 파일 형식: {file_path}. XLSX 파일만 지원합니다.")
            
            # 데이터프레임을 딕셔너리 리스트로 변환
            news_data = df.to_dict('records')
            
            logger.info(f"파일 로드 완료: {file_path}, {len(news_data)}개 기사")
            return news_data
            
        except Exception as e:
            logger.error(f"파일 로드 실패: {file_path}, 오류: {str(e)}")
            raise
    
    def save_analyzed_results(self, analyzed_data: List[Dict[str, Any]], output_path: str, use_relevance_folder: bool = True) -> bool:
        """분석 결과 저장"""
        try:
            # relevance 폴더를 사용하는 경우 경로 수정
            if use_relevance_folder:
                from app.core.config import settings
                file_name = os.path.basename(output_path)
                output_path = os.path.join(settings.RELEVANCE_RESULTS_PATH, file_name)
                # relevance 폴더 생성 보장
                os.makedirs(settings.RELEVANCE_RESULTS_PATH, exist_ok=True)
            
            df = pd.DataFrame(analyzed_data)
            
            # 기존 한국어 컬럼명을 영어로 매핑 (분석 결과와 호환)
            column_mapping = {
                '제목': 'title',
                '링크': 'link', 
                '발행일시': 'pubDate',
                '내용': 'description',
                '출처': 'source',
                '키워드': 'keyword'
            }
            
            # 컬럼명 변경
            df = df.rename(columns=column_mapping)
            
            # 컬럼 순서 정리
            columns_order = ['title', 'link', 'pubDate', 'description', 'source', 'originallink', 'keyword', 
                           'is_relevant', 'category', 'relevance_reason', 'confidence', 'keywords']
            
            # 존재하는 컬럼만 선택
            available_columns = [col for col in columns_order if col in df.columns]
            remaining_columns = [col for col in df.columns if col not in columns_order]
            final_columns = available_columns + remaining_columns
            
            df = df[final_columns]
            
            # 파일 저장 (XLSX만 지원)
            if output_path.endswith(('.xlsx', '.xls')):
                df.to_excel(output_path, index=False, engine='openpyxl')
            else:
                # 확장자가 .xlsx가 아니면 .xlsx로 변경
                if not output_path.endswith('.xlsx'):
                    output_path = output_path.rsplit('.', 1)[0] + '.xlsx' if '.' in output_path else output_path + '.xlsx'
                df.to_excel(output_path, index=False, engine='openpyxl')
            
            logger.info(f"분석 결과 저장 완료: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"분석 결과 저장 실패: {output_path}, 오류: {str(e)}")
            return False
