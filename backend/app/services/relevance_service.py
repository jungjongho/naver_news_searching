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
    단순화된 뉴스 기사 관련성 평가 서비스
    - 배치 처리 로직 제거
    - 순차적 개별 처리만 지원
    - 복잡한 병렬 처리 제거
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
            return True
        except Exception as e:
            logger.error(f"OpenAI 클라이언트 초기화 실패: {str(e)}")
            return False
    
    def _map_model_name(self, model: str) -> str:
        """모델명 매핑"""
        model_mapping = {
            'gpt-4.1': 'gpt-4.1',
            'gpt-4.1-mini': 'gpt-4.1-mini',
            'gpt-4.1-nano': 'gpt-4.1-nano',  # 2025년 4월 출시된 최신 고속 저비용 모델
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
            logger.info("Anthropic 클라이언트 초기화 완료")
            return True
        except Exception as e:
            logger.error(f"Anthropic 클라이언트 초기화 실패: {str(e)}")
            return False
    
    def _get_analysis_prompt(self, custom_prompt: str = None) -> str:
        """뉴스 관련성 분석을 위한 단순화된 프롬프트"""
        if custom_prompt:
            return custom_prompt
            
        return """
당신은 코스맥스의 화장품 업계 전문 분석가입니다. 주어진 뉴스 기사를 분석하여 코스맥스에 유용한지 평가해주세요.

분석 기준:
1. 자사 언급기사: '코스맥스'가 직접 언급된 기사
2. 업계 관련기사: 화장품/뷰티 업계 관련 기사
3. 건강기능식품·펫푸드: 건강기능식품이나 펫푸드 관련 기사
4. 기타: 위 카테고리에 해당하지 않는 기사

반드시 다음 JSON 형식으로만 응답해주세요:
{{
  "is_relevant": true or false,
  "category": "자사 언급기사",
  "relevance_reason": "관련성 판단 이유",
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
                parts = response_text.split("```")
                for part in parts:
                    if "{" in part and "}" in part:
                        response_text = part
                        break
            
            # 앞뒤 공백 제거
            response_text = response_text.strip()
            
            # JSON 객체 찾기
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                response_text = response_text[start_idx:end_idx + 1]
            
            # JSON 파싱
            result = json.loads(response_text)
            
            # 필수 필드 검증 및 기본값 설정
            result.setdefault("is_relevant", False)
            result.setdefault("category", "기타")
            result.setdefault("relevance_reason", "분석 결과 없음")
            result.setdefault("confidence", 0.5)
            result.setdefault("keywords", [])
            
            # confidence 값 안전성 검증
            confidence = result["confidence"]
            if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                result["confidence"] = 0.5
            
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"JSON 파싱 실패, 기본값 반환: {str(e)}")
            return self._get_default_result()
    
    def _get_default_result(self) -> Dict[str, Any]:
        """기본 결과 반환"""
        return {
            "is_relevant": False,
            "category": "기타",
            "relevance_reason": "분석 실패",
            "confidence": 0.0,
            "keywords": []
        }
    
    def _analyze_single_news_openai(self, title: str, content: str, model: str = "gpt-4.1-nano", custom_prompt: str = None) -> Dict[str, Any]:
        """OpenAI를 사용한 단일 뉴스 분석"""
        try:
            actual_model = self._map_model_name(model)
            prompt = self._get_analysis_prompt(custom_prompt).format(
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
            logger.debug(f"OpenAI 응답: {repr(result_text)}")
            
            return self._parse_json_response(result_text)
                
        except Exception as e:
            logger.error(f"OpenAI 분석 중 오류: {str(e)}")
            return self._get_default_result()
    
    def _analyze_single_news_anthropic(self, title: str, content: str, model: str = "claude-instant-1", custom_prompt: str = None) -> Dict[str, Any]:
        """Anthropic Claude를 사용한 단일 뉴스 분석"""
        try:
            actual_model = self._map_model_name(model)
            prompt = self._get_analysis_prompt(custom_prompt).format(title=title, content=content)
            
            response = self.anthropic_client.messages.create(
                model=actual_model,
                max_tokens=500,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            result_text = response.content[0].text.strip()
            return self._parse_json_response(result_text)
                
        except Exception as e:
            logger.error(f"Anthropic 분석 오류: {str(e)}")
            return self._get_default_result()
    
    def analyze_news_simple(self, news_data: List[Dict[str, Any]], api_key: str, model: str = "gpt-4.1-nano", prompt_template=None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """단순화된 뉴스 분석 - 순차적 개별 처리"""
        logger.info(f"단순화된 뉴스 분석 시작: {len(news_data)}개 기사, 모델: {model}")
        
        # 프롬프트 설정
        custom_prompt = None
        if prompt_template:
            custom_prompt = prompt_template.single_prompt
            logger.info(f"사용 프롬프트: {prompt_template.name}")
        
        # API 클라이언트 초기화
        if model.startswith("gpt"):
            if not self._init_openai_client(api_key):
                raise ValueError("OpenAI API 키가 유효하지 않습니다.")
            analyze_func = self._analyze_single_news_openai
        elif model.startswith("claude"):
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
            "processing_errors": 0
        }
        
        # 순차적 개별 처리
        for i, news_item in enumerate(news_data):
            try:
                logger.info(f"분석 진행: {i+1}/{len(news_data)}")
                
                title = news_item.get("title", news_item.get("제목", ""))
                content = news_item.get("description", news_item.get("content", news_item.get("내용", "")))
                
                if not title and not content:
                    logger.warning(f"제목과 내용이 모두 비어있는 기사 발견: {i}")
                    analysis_result = self._get_default_result()
                else:
                    # 실제 분석 수행
                    analysis_result = analyze_func(title, content, model, custom_prompt)
                
                # 원본 데이터에 분석 결과 추가
                news_item_analyzed = news_item.copy()
                news_item_analyzed.update(analysis_result)
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
                time.sleep(0.5)  # 500ms 딜레이
                
            except Exception as e:
                logger.error(f"뉴스 항목 {i} 분석 중 오류: {str(e)}")
                stats["processing_errors"] += 1
                
                # 오류 발생한 항목도 기본값으로 추가
                news_item_analyzed = news_item.copy()
                news_item_analyzed.update(self._get_default_result())
                analyzed_data.append(news_item_analyzed)
                stats["categories"]["기타"] += 1
        
        # 최종 통계 계산
        stats["relevant_ratio"] = stats["relevant_items"] / stats["total_items"] if stats["total_items"] > 0 else 0
        stats["relevant_percent"] = round(stats["relevant_ratio"] * 100, 1)
        
        logger.info(f"단순화된 뉴스 분석 완료:")
        logger.info(f"  - 관련 기사: {stats['relevant_items']}/{stats['total_items']} ({stats['relevant_percent']}%)")
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
        """분석 결과 저장 - 중복 컬럼 정리"""
        try:
            # relevance 폴더를 사용하는 경우 경로 수정
            if use_relevance_folder:
                from app.core.config import settings
                file_name = os.path.basename(output_path)
                output_path = os.path.join(settings.RELEVANCE_RESULTS_PATH, file_name)
                # relevance 폴더 생성 보장
                os.makedirs(settings.RELEVANCE_RESULTS_PATH, exist_ok=True)
            
            df = pd.DataFrame(analyzed_data)
            
            # 기존 한국어 컬럼명을 영어로 매핑
            column_mapping = {
                '제목': 'title',
                '링크': 'link', 
                '발행일시': 'pubDate',
                '내용': 'description',
                '출처': 'source',
                '키워드': 'search_keyword'  # 검색에 사용된 키워드
            }
            
            # 컬럼명 변경
            df = df.rename(columns=column_mapping)
            
            # 중복/불필요한 컬럼 제거 로직
            columns_to_remove = []
            
            # reason과 relevance_reason 중복 처리
            if 'reason' in df.columns and 'relevance_reason' in df.columns:
                # relevance_reason을 우선으로 하고 reason 제거
                columns_to_remove.append('reason')
            elif 'reason' in df.columns and 'relevance_reason' not in df.columns:
                # reason만 있으면 relevance_reason으로 이름 변경
                df = df.rename(columns={'reason': 'relevance_reason'})
            
            # keyword와 keywords 중복 처리
            if 'keyword' in df.columns and 'keywords' in df.columns:
                # keyword는 검색 키워드, keywords는 추출된 키워드로 구분
                # keyword를 search_keyword로 이름 변경
                df = df.rename(columns={'keyword': 'search_keyword'})
            elif 'keyword' in df.columns and 'keywords' not in df.columns:
                # keyword만 있으면 용도에 따라 처리
                # 리스트 형태면 keywords로, 문자열이면 search_keyword로
                sample_value = df['keyword'].dropna().iloc[0] if len(df['keyword'].dropna()) > 0 else None
                if isinstance(sample_value, list):
                    df = df.rename(columns={'keyword': 'keywords'})
                else:
                    df = df.rename(columns={'keyword': 'search_keyword'})
            
            # 기타 중복 컬럼들 제거
            other_duplicates = {
                'content': 'description',  # content와 description 중복
                'url': 'link',  # url과 link 중복
                'date': 'pubDate',  # date와 pubDate 중복
            }
            
            for old_col, preferred_col in other_duplicates.items():
                if old_col in df.columns and preferred_col in df.columns:
                    columns_to_remove.append(old_col)
                elif old_col in df.columns and preferred_col not in df.columns:
                    df = df.rename(columns={old_col: preferred_col})
            
            # 중복 컬럼들 제거
            df = df.drop(columns=columns_to_remove, errors='ignore')
            
            # 최종 컬럼 순서 정리 (표준 순서)
            standard_columns = [
                'title',           # 제목
                'link',            # 링크
                'pubDate',         # 발행일시
                'description',     # 내용
                'source',          # 출처
                'originallink',    # 원본링크
                'search_keyword',  # 검색에 사용된 키워드
                'is_relevant',     # 관련성 여부
                'category',        # 카테고리
                'relevance_reason', # 관련성 판단 이유
                'confidence',      # 신뢰도
                'keywords'         # LLM이 추출한 키워드들
            ]
            
            # 존재하는 표준 컬럼들만 선택
            available_standard_columns = [col for col in standard_columns if col in df.columns]
            
            # 표준 컬럼에 없는 나머지 컬럼들
            remaining_columns = [col for col in df.columns if col not in standard_columns]
            
            # 최종 컬럼 순서
            final_columns = available_standard_columns + remaining_columns
            
            # 컬럼 순서 적용
            df = df[final_columns]
            
            # keywords 컬럼의 리스트를 문자열로 변환 (Excel 저장을 위해)
            if 'keywords' in df.columns:
                df['keywords'] = df['keywords'].apply(
                    lambda x: ', '.join(x) if isinstance(x, list) else str(x) if x is not None else ''
                )
            
            # 파일 저장 (XLSX만 지원)
            if output_path.endswith(('.xlsx', '.xls')):
                df.to_excel(output_path, index=False, engine='openpyxl')
            else:
                # 확장자가 .xlsx가 아니면 .xlsx로 변경
                if not output_path.endswith('.xlsx'):
                    output_path = output_path.rsplit('.', 1)[0] + '.xlsx' if '.' in output_path else output_path + '.xlsx'
                df.to_excel(output_path, index=False, engine='openpyxl')
            
            logger.info(f"분석 결과 저장 완료: {output_path}")
            logger.info(f"최종 컬럼 구성: {list(df.columns)}")
            return True
            
        except Exception as e:
            logger.error(f"분석 결과 저장 실패: {output_path}, 오류: {str(e)}")
            return False

    def clean_existing_file(self, file_path: str) -> bool:
        """기존 파일의 중복 컬럼 정리"""
        try:
            # 파일 로드
            if file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path, engine='openpyxl')
            else:
                raise ValueError(f"지원하지 않는 파일 형식: {file_path}. XLSX 파일만 지원합니다.")
            
            # 데이터를 딕셔너리 리스트로 변환
            data = df.to_dict('records')
            
            # 기존 save_analyzed_results 메서드를 사용하여 정리
            # 결과를 동일한 파일에 덮어쓰기
            backup_path = file_path.replace('.xlsx', '_backup.xlsx')
            
            # 백업 생성
            df.to_excel(backup_path, index=False, engine='openpyxl')
            logger.info(f"백업 파일 생성: {backup_path}")
            
            # 정리된 데이터로 저장
            success = self.save_analyzed_results(data, file_path, use_relevance_folder=False)
            
            if success:
                logger.info(f"파일 정리 완료: {file_path}")
                return True
            else:
                logger.error(f"파일 정리 실패: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"파일 정리 중 오류: {file_path}, 오류: {str(e)}")
            return False
    
    # 호환성을 위한 기존 메서드명 유지
    def analyze_news_batch(self, news_data: List[Dict[str, Any]], api_key: str, model: str = "gpt-4.1-nano", prompt_template=None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """기존 API 호환성을 위한 래퍼 메서드"""
        return self.analyze_news_simple(news_data, api_key, model, prompt_template)
