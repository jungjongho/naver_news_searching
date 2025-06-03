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

# 로깅 설정 개선
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RelevanceService:
    """
    뉴스 기사 관련성 평가 서비스 (디버깅 버전)
    """
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
    
    def _init_openai_client(self, api_key: str):
        """OpenAI 클라이언트 초기화"""
        try:
            logger.info("OpenAI 클라이언트 초기화 시작...")
            
            # 클라이언트 초기화
            self.openai_client = OpenAI(
                api_key=api_key,
                timeout=30.0
            )
            
            # API 키 유효성 테스트
            logger.info("API 키 유효성 테스트 중...")
            models = self.openai_client.models.list()
            logger.info(f"OpenAI 클라이언트 초기화 완료, 사용 가능한 모델 수: {len(models.data)}")
            
            # 사용 가능한 모델 목록 출력 (디버깅용)
            model_names = [model.id for model in models.data if 'gpt' in model.id.lower()]
            logger.info(f"사용 가능한 GPT 모델들: {model_names[:10]}")  # 처음 10개만 출력
            
            return True
        except Exception as e:
            logger.error(f"OpenAI 클라이언트 초기화 실패: {str(e)}")
            logger.error(f"오류 타입: {type(e).__name__}")
            return False
    
    def _map_model_name(self, model: str) -> str:
        """모델명 매핑 (사용자 친화적 모델명을 실제 API 모델명으로 변환)"""
        model_mapping = {
            'gpt-4.1-nano': 'gpt-4o-mini',  # 실제 사용 가능한 모델로 매핑
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
    
    def _get_analysis_prompt(self) -> str:
        """뉴스 관련성 분석을 위한 프롬프트"""
        return """당신은 화장품 업계 전문 분석가입니다. 주어진 뉴스 기사를 분석하여 화장품 업계와의 관련성을 평가해주세요.

분석 기준:
1. 자사 언급기사: 특정 화장품 회사나 브랜드가 직접 언급된 기사
2. 업계 관련기사: 화장품 업계 전반에 영향을 미치는 기사 (규제, 트렌드, 시장 동향 등)
3. 건강기능식품·펫푸드: 건강기능식품이나 펫푸드 관련 기사
4. 기타: 위 카테고리에 해당하지 않는 기사

반드시 다음 JSON 형식으로만 응답해주세요. 다른 텍스트는 포함하지 마세요:
{
  "is_relevant": true,
  "category": "자사 언급기사",
  "relevance_reason": "관련성 판단 이유",
  "confidence": 0.9,
  "keywords": ["키워드1", "키워드2"]
}

뉴스 기사:
제목: {title}
내용: {content}"""
    
    def _analyze_single_news_openai(self, title: str, content: str, model: str = "gpt-3.5-turbo") -> Dict[str, Any]:
        """OpenAI를 사용한 단일 뉴스 분석"""
        try:
            # 모델명 매핑
            actual_model = self._map_model_name(model)
            logger.info(f"분석 시작: 모델={actual_model}")
            
            # 입력 데이터 검증
            if not title.strip() and not content.strip():
                logger.warning("제목과 내용이 모두 비어있음")
                return {
                    "is_relevant": False,
                    "category": "기타",
                    "relevance_reason": "제목과 내용이 비어있음",
                    "confidence": 0.0,
                    "keywords": []
                }
            
            prompt = self._get_analysis_prompt().format(
                title=title[:500],  # 제목 길이 제한
                content=content[:2000]  # 내용 길이 제한
            )
            
            logger.info(f"프롬프트 길이: {len(prompt)} 문자")
            
            # OpenAI API 호출
            response = self.openai_client.chat.completions.create(
                model=actual_model,
                messages=[
                    {"role": "system", "content": "당신은 화장품 업계 전문 분석가입니다. 반드시 JSON 형식으로만 응답하세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"}  # JSON 응답 강제
            )
            
            result_text = response.choices[0].message.content.strip()
            logger.info(f"OpenAI 원본 응답: {result_text}")
            
            # JSON 파싱
            try:
                result = json.loads(result_text)
                logger.info(f"JSON 파싱 성공: {result}")
                
                # 필수 필드 검증 및 기본값 설정
                result.setdefault("is_relevant", False)
                result.setdefault("category", "기타")
                result.setdefault("relevance_reason", "분석 결과 없음")
                result.setdefault("confidence", 0.5)
                result.setdefault("keywords", [])
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 실패: {str(e)}")
                logger.error(f"파싱 실패한 응답: {result_text}")
                return {
                    "is_relevant": False,
                    "category": "기타",
                    "relevance_reason": "JSON 파싱 오류",
                    "confidence": 0.0,
                    "keywords": []
                }
                
        except Exception as e:
            logger.error(f"OpenAI 분석 중 오류 발생: {str(e)}")
            logger.error(f"오류 타입: {type(e).__name__}")
            return {
                "is_relevant": False,
                "category": "기타", 
                "relevance_reason": f"API 오류: {str(e)[:30]}",
                "confidence": 0.0,
                "keywords": []
            }
    
    def test_single_analysis(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """단일 분석 테스트 함수"""
        logger.info("=== 단일 분석 테스트 시작 ===")
        
        # 클라이언트 초기화
        if not self._init_openai_client(api_key):
            logger.error("클라이언트 초기화 실패")
            return False
        
        # 테스트 데이터
        test_title = "아모레퍼시픽, 신제품 출시로 매출 증가"
        test_content = "아모레퍼시픽이 새로운 화장품 라인을 출시하면서 3분기 매출이 전년 대비 15% 증가했다고 발표했다."
        
        logger.info(f"테스트 데이터 - 제목: {test_title}")
        logger.info(f"테스트 데이터 - 내용: {test_content}")
        
        # 분석 실행
        result = self._analyze_single_news_openai(test_title, test_content, model)
        
        logger.info(f"분석 결과: {result}")
        logger.info("=== 단일 분석 테스트 완료 ===")
        
        return result.get("relevance_reason") != "API 오류"

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
            "api_errors": 0,
            "json_errors": 0
        }
        
        for i, news_item in enumerate(news_data):
            try:
                logger.info(f"분석 진행: {i+1}/{len(news_data)}")
                
                title = news_item.get("title", news_item.get("제목", ""))
                content = news_item.get("description", news_item.get("content", news_item.get("내용", "")))
                
                logger.info(f"처리 중인 기사 - 제목: {title[:50]}...")
                
                # 실제 분석 수행
                analysis_result = analyze_func(title, content, model)
                
                # 오류 타입별 통계
                if "API 오류" in analysis_result.get("relevance_reason", ""):
                    stats["api_errors"] += 1
                elif "JSON 파싱 오류" in analysis_result.get("relevance_reason", ""):
                    stats["json_errors"] += 1
                
                # 원본 데이터에 분석 결과 추가
                news_item_analyzed = news_item.copy()
                news_item_analyzed.update({
                    "is_relevant": analysis_result["is_relevant"],
                    "category": analysis_result["category"],
                    "relevance_reason": analysis_result["relevance_reason"],
                    "confidence": analysis_result.get("confidence", 0.5),
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
                time.sleep(0.2)  # 200ms 딜레이
                
            except Exception as e:
                logger.error(f"뉴스 항목 {i} 분석 중 예외 발생: {str(e)}")
                stats["processing_errors"] += 1
                
                # 오류 발생한 항목도 기본값으로 추가
                news_item_analyzed = news_item.copy()
                news_item_analyzed.update({
                    "is_relevant": False,
                    "category": "기타",
                    "relevance_reason": f"처리 오류: {str(e)[:30]}",
                    "confidence": 0.0,
                    "keywords": []
                })
                analyzed_data.append(news_item_analyzed)
                stats["categories"]["기타"] += 1
        
        # 최종 통계 계산
        stats["relevant_ratio"] = stats["relevant_items"] / stats["total_items"] if stats["total_items"] > 0 else 0
        stats["relevant_percent"] = round(stats["relevant_ratio"] * 100, 1)
        
        logger.info(f"뉴스 배치 분석 완료:")
        logger.info(f"  - 총 기사: {stats['total_items']}")
        logger.info(f"  - 관련 기사: {stats['relevant_items']} ({stats['relevant_percent']}%)")
        logger.info(f"  - API 오류: {stats['api_errors']}")
        logger.info(f"  - JSON 파싱 오류: {stats['json_errors']}")
        logger.info(f"  - 기타 처리 오류: {stats['processing_errors']}")
        
        return analyzed_data, stats

# 테스트 실행 함수
def run_test():
    """테스트 실행"""
    # API 키 설정 (환경변수에서 가져오기)
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        return
    
    service = RelevanceService()
    
    # 단일 분석 테스트
    success = service.test_single_analysis(api_key, "gpt-3.5-turbo")
    
    if success:
        print("✅ 단일 분석 테스트 성공!")
    else:
        print("❌ 단일 분석 테스트 실패!")

if __name__ == "__main__":
    run_test()
