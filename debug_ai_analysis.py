#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AI 분석 디버깅 스크립트
실제 AI 호출이 제대로 되는지 테스트
"""

import sys
import os
import json

# 백엔드 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from app.services.ai_client import AIClientFactory
    from app.utils.data_processor import data_processor
    
    print("=== AI 분석 디버깅 테스트 ===")
    
    # 테스트용 API 키 입력 (실제 사용시에는 여기에 API 키를 입력하세요)
    api_key = input("OpenAI API 키를 입력하세요: ").strip()
    
    if not api_key:
        print("❌ API 키가 입력되지 않았습니다.")
        exit(1)
    
    # AI 클라이언트 생성
    print("1. AI 클라이언트 생성 중...")
    try:
        ai_client = AIClientFactory.create_client("gpt-4.1-nano", api_key)
        print("✅ AI 클라이언트 생성 성공")
    except Exception as e:
        print(f"❌ AI 클라이언트 생성 실패: {e}")
        exit(1)
    
    # 테스트용 뉴스 기사
    test_title = "LG생활건강 VDL, 일본 도쿄서 팝업행사…'브랜드 저변 확대'"
    test_content = "LG생활건강의 메이크업 브랜드 VDL은 지난달 21∼27일 일본 도쿄 하라주쿠에 있는 화장품 편집숍 앳코스메에서 팝업매장을 운영했다고 10일 밝혔다."
    
    # 프롬프트 생성
    prompt = f"""당신은 코스맥스의 화장품 업계 전문 분석가입니다. 주어진 뉴스 기사를 분석하여 다음 4개 카테고리로 분류해주세요.

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
제목: {test_title}
내용: {test_content}"""

    print("\n2. AI 분석 수행 중...")
    print(f"제목: {test_title}")
    print(f"내용: {test_content[:100]}...")
    
    try:
        # AI 분석 호출
        response = ai_client.analyze(prompt, model="gpt-4.1-nano")
        print("✅ AI 분석 성공")
        print(f"원본 응답: {response}")
        
        # JSON 파싱 테스트
        print("\n3. JSON 파싱 테스트...")
        parsed_result = data_processor.safe_json_parse(response)
        print("✅ JSON 파싱 성공")
        print("파싱된 결과:")
        print(json.dumps(parsed_result, ensure_ascii=False, indent=2))
        
        # 필드 검증
        print("\n4. 필드 검증...")
        required_fields = ['category', 'confidence', 'keywords', 'relation', 'reason', 'importance', 'recommendation_reason']
        for field in required_fields:
            if field in parsed_result:
                print(f"  ✅ {field}: {parsed_result[field]}")
            else:
                print(f"  ❌ {field}: 누락")
        
        # 카테고리 검증
        if parsed_result['category'] == '업계관련기사':
            print("\n✅ 올바른 카테고리 분류! (LG생활건강은 업계관련기사)")
        else:
            print(f"\n⚠️  예상과 다른 카테고리: {parsed_result['category']}")
            
    except Exception as e:
        print(f"❌ AI 분석 실패: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== 디버깅 테스트 완료 ===")
    
except ImportError as e:
    print(f"❌ 모듈 import 오류: {e}")
    print("backend 디렉토리 경로를 확인해주세요.")
except Exception as e:
    print(f"❌ 테스트 실행 오류: {e}")
    import traceback
    traceback.print_exc()
