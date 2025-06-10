#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
수정된 관련성 분석 서비스 - 배치 JSON 파싱 문제 해결
"""

import json
import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def fixed_parse_batch_response_dynamic(response_text: str, expected_count: int) -> List[Dict[str, Any]]:
    """수정된 배치 응답 파싱 함수"""
    
    try:
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
                            validated_item = validate_and_normalize_item(item)
                            validated_results.append(validated_item)
                            logger.info(f"항목 {i+1} 검증 완료: {validated_item['category']}")
                        else:
                            logger.warning(f"항목 {i+1}이 딕셔너리가 아닙니다: {type(item)}")
                            validated_results.append(get_default_analysis_result())
                    
                    # 결과 개수 조정
                    return adjust_result_count(validated_results, expected_count)
                
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 배열 직접 파싱 실패: {e}")
        
        # 2단계: 개별 JSON 객체 추출 및 파싱
        logger.info("개별 JSON 객체 추출 방식으로 재시도")
        return extract_individual_json_objects(response_text, expected_count)
        
    except Exception as e:
        logger.error(f"배치 응답 파싱 전체 실패: {e}")
        return [get_default_analysis_result() for _ in range(expected_count)]


def extract_individual_json_objects(response_text: str, expected_count: int) -> List[Dict[str, Any]]:
    """개별 JSON 객체 추출 및 파싱"""
    
    try:
        # JSON 객체 패턴으로 추출
        # 중첩된 중괄호도 처리할 수 있는 더 강력한 패턴
        json_pattern = r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}'
        json_matches = re.findall(json_pattern, response_text, re.DOTALL)
        
        logger.info(f"추출된 JSON 객체 수: {len(json_matches)}")
        
        validated_results = []
        for i, json_str in enumerate(json_matches):
            try:
                logger.info(f"JSON 객체 {i+1} 파싱 시도: {json_str[:100]}...")
                
                # JSON 파싱
                parsed_obj = json.loads(json_str)
                
                if isinstance(parsed_obj, dict):
                    # 검증 및 정규화
                    validated_item = validate_and_normalize_item(parsed_obj)
                    validated_results.append(validated_item)
                    logger.info(f"JSON 객체 {i+1} 파싱 성공: {validated_item['category']}")
                else:
                    logger.warning(f"JSON 객체 {i+1}이 딕셔너리가 아닙니다")
                    validated_results.append(get_default_analysis_result())
                    
            except json.JSONDecodeError as e:
                logger.warning(f"JSON 객체 {i+1} 파싱 실패: {e}")
                validated_results.append(get_default_analysis_result())
        
        return adjust_result_count(validated_results, expected_count)
        
    except Exception as e:
        logger.error(f"개별 JSON 객체 추출 실패: {e}")
        return [get_default_analysis_result() for _ in range(expected_count)]


def validate_and_normalize_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """분석 결과 항목 검증 및 정규화"""
    
    # 기본값으로 시작
    validated = get_default_analysis_result()
    
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


def adjust_result_count(results: List[Dict[str, Any]], expected_count: int) -> List[Dict[str, Any]]:
    """결과 개수를 예상 개수에 맞게 조정"""
    
    if len(results) == expected_count:
        logger.info(f"결과 개수 일치: {len(results)}개")
        return results
    elif len(results) > expected_count:
        logger.warning(f"결과 초과: {len(results)} > {expected_count}, 앞의 {expected_count}개만 사용")
        return results[:expected_count]
    else:
        logger.warning(f"결과 부족: {len(results)} < {expected_count}, 기본값으로 보완")
        while len(results) < expected_count:
            results.append(get_default_analysis_result())
        return results


def get_default_analysis_result() -> Dict[str, Any]:
    """기본 분석 결과 반환"""
    return {
        "category": "기타",
        "confidence": 0.0,
        "keywords": [],
        "relation": 0.0,
        "reason": "분석 실패 또는 기본값",
        "importance": "하",
        "recommendation_reason": "분석이 수행되지 않음"
    }


# 테스트용 함수
def test_parsing_with_actual_response():
    """실제 LLM 응답으로 파싱 테스트"""
    
    actual_response = """[
  {
    "Category": "기타",
    "Confidence": 0.2,
    "Keywords": ["인테리어", "화장대", "가구"],
    "Relation": 0.1,
    "Reason": "기사 내용은 화장대와 인테리어 트렌드에 관한 것으로, 화장품 또는 뷰티 업계와 직접적 관련이 없음.",
    "Importance": "하",
    "Recommendation_reason": "화장품 업계와 관련성이 낮아 추천하지 않음."
  },
  {
    "Category": "업계관련기사",
    "Confidence": 0.8,
    "Keywords": ["폴라초이스", "스킨케어", "화장품"],
    "Relation": 0.8,
    "Reason": "브랜드명과 스킨케어, 화장품 관련 언급이 있어 화장품 업계와 관련된 기사로 판단됨.",
    "Importance": "중",
    "Recommendation_reason": "글로벌 브랜드와 화장품 시장 동향을 다루고 있어 업계 관련성 높음."
  },
  {
    "Category": "업계관련기사",
    "Confidence": 0.7,
    "Keywords": ["K-뷰티", "글로벌", "화장품", "지식재산권"],
    "Relation": 0.7,
    "Reason": "한국 화장품(뷰티) 시장과 글로벌 전략, 지식재산권 보호에 관한 내용으로 업계 관련 기사임.",
    "Importance": "중",
    "Recommendation_reason": "국내 화장품 산업의 글로벌 진출과 전략을 다루고 있어 관련성 높음."
  }
]"""
    
    print("=== 파싱 테스트 시작 ===")
    
    results = fixed_parse_batch_response_dynamic(actual_response, 3)
    
    print(f"파싱 결과 개수: {len(results)}")
    for i, result in enumerate(results):
        print(f"기사 {i+1}: {result['category']} (신뢰도: {result['confidence']})")
        print(f"  키워드: {result['keywords']}")
        print(f"  이유: {result['reason'][:50]}...")
    
    return results


if __name__ == "__main__":
    # 파싱 테스트 실행
    test_results = test_parsing_with_actual_response()
