#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
관련성 평가 문제 진단 스크립트
"""

print("=== 네이버 뉴스 관련성 평가 문제 진단 ===")
print()

print("🔍 현재 문제 상황:")
print("- 모든 기사가 '기타' 카테고리로 분류됨")
print("- confidence가 0으로 나옴")  
print("- reason이 '분석 실패 또는 기본값'으로 표시됨")
print()

print("💡 가능한 원인들:")
print("1. ❌ AI API 키가 설정되지 않았거나 유효하지 않음")
print("2. ❌ AI 모델명이 잘못됨 (gpt-4.1-nano는 존재하지 않는 모델)")
print("3. ❌ AI 호출 자체가 실패함 (네트워크 오류, API 제한 등)")
print("4. ❌ JSON 파싱 오류 (AI 응답이 JSON 형식이 아님)")
print()

print("🔧 해결 방법:")
print()

print("1️⃣ **AI 모델명 수정 완료**")
print("   - gpt-4.1-nano → gpt-4o-mini로 자동 매핑")
print("   - 존재하지 않는 모델명들을 유효한 모델로 매핑")
print()

print("2️⃣ **로깅 개선 완료**")
print("   - DEBUG 레벨로 변경하여 상세 로그 확인 가능")
print("   - AI 호출 과정의 모든 단계 로깅 추가")
print()

print("3️⃣ **다음 단계로 해결하기:**")
print()

print("🚀 **즉시 테스트 방법:**")
print("1. 백엔드 서버 재시작:")
print("   cd /Users/jongho.jung/Desktop/jongho_project/PoC/naver_news_searching/backend")
print("   python run.py")
print()

print("2. 프론트엔드에서 관련성 평가 실행:")
print("   - 유효한 OpenAI API 키 입력")
print("   - 모델을 gpt-4o-mini 또는 gpt-3.5-turbo로 선택")
print("   - 작은 파일(10개 이하 기사)로 테스트")
print()

print("3. 터미널에서 로그 확인:")
print("   - 'OpenAI 클라이언트 초기화 완료' 메시지 확인")
print("   - 'OpenAI 분석 시작' 메시지 확인")
print("   - 'AI 응답 수신' 메시지 확인")
print("   - 오류 메시지가 있다면 해당 내용 확인")
print()

print("🔍 **API 키 확인 방법:**")
print("1. OpenAI 웹사이트에서 API 키 생성/확인")
print("2. API 키가 충분한 크레딧을 가지고 있는지 확인")
print("3. API 키에 GPT 모델 사용 권한이 있는지 확인")
print()

print("📋 **예상 결과:**")
print("수정 후 정상 작동시 다음과 같이 나와야 합니다:")
print()
print("LG생활건강 관련 기사:")
print("- category: '업계관련기사'")
print("- confidence: 0.7~0.9")
print("- keywords: ['LG생활건강', 'VDL', '화장품']")
print("- relation: 0.6~0.8")  
print("- reason: '화장품 업계 주요 기업 관련 뉴스'")
print("- importance: '중' 또는 '상'")
print("- recommendation_reason: '업계 동향 파악에 중요'")
print()

print("✅ **수정 완료된 항목들:**")
print("- ✅ 모델명 매핑 (gpt-4.1-nano → gpt-4o-mini)")
print("- ✅ JSON 파싱 로직 개선")
print("- ✅ 키 매핑 (Category → category)")
print("- ✅ 오타 처리 (Impoortance → importance)")
print("- ✅ 로깅 레벨 DEBUG로 변경")
print("- ✅ 모든 필드 기본값 설정")
print()

print("🎯 **이제 해야 할 일:**")
print("1. 백엔드 서버 재시작")
print("2. 유효한 OpenAI API 키로 테스트")
print("3. 로그에서 실제 오류 원인 확인")
print()

print("문제가 지속되면 터미널 로그를 확인하여 구체적인 오류 메시지를 확인해주세요!")
