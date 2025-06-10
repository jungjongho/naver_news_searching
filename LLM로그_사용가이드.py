#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LLM 로그 기능 사용 가이드
"""

print("=== LLM API 로그 기능 추가 완료 ===")
print()

print("🔧 **추가된 기능:**")
print("1. ✅ LLM API 호출시 프롬프트와 응답을 llm_log.txt에 자동 기록")
print("2. ✅ 타임스탬프와 함께 상세한 로그 정보 저장")
print("3. ✅ 실시간 로그 모니터링 도구 제공")
print()

print("📁 **로그 파일 위치:**")
print("/Users/jongho.jung/Desktop/jongho_project/PoC/naver_news_searching/backend/llm_log.txt")
print()

print("🔍 **로그에 기록되는 정보:**")
print("- 호출 시간")
print("- 사용된 모델명")
print("- 전체 프롬프트 내용")
print("- LLM의 전체 응답 내용")
print("- 응답 길이")
print("- 오류 발생시 오류 내용")
print()

print("🚀 **사용 방법:**")
print()

print("**1단계: 로그 모니터링 시작**")
print("새 터미널에서:")
print("cd /Users/jongho.jung/Desktop/jongho_project/PoC/naver_news_searching")
print("python llm_log_monitor.py monitor")
print()

print("**2단계: 백엔드 서버 시작**")
print("다른 터미널에서:")
print("cd /Users/jongho.jung/Desktop/jongho_project/PoC/naver_news_searching/backend")
print("python run.py")
print()

print("**3단계: 관련성 평가 실행**")
print("프론트엔드에서 관련성 평가를 실행하면:")
print("- 터미널 1: 실시간으로 LLM 호출 과정이 표시됨")
print("- 정확히 어떤 프롬프트를 보내고 어떤 응답을 받는지 확인 가능")
print()

print("🔍 **문제 진단 방법:**")
print()

print("**케이스 1: 프롬프트 문제**")
print("- 로그에서 프롬프트 내용 확인")
print("- JSON 형식 요구사항이 명확한지 확인")
print("- 카테고리 분류 기준이 정확한지 확인")
print()

print("**케이스 2: LLM 응답 문제**")
print("- 로그에서 LLM 응답 내용 확인")
print("- JSON 형식으로 응답하는지 확인")
print("- 모든 필드(Category, Confidence 등)가 포함되었는지 확인")
print()

print("**케이스 3: 파싱 문제**")
print("- LLM 응답은 정상이지만 파싱에서 실패하는 경우")
print("- data_processor.safe_json_parse() 함수 문제일 가능성")
print()

print("💡 **추가 로그 명령어:**")
print()
print("# 로그 파일 초기화")
print("python llm_log_monitor.py clear")
print()
print("# 최근 50줄만 보기")
print("python llm_log_monitor.py show 50")
print()
print("# 최근 100줄 보기")
print("python llm_log_monitor.py show 100")
print()

print("🎯 **로그 확인으로 찾을 수 있는 문제들:**")
print("1. 프롬프트에서 JSON 형식 지시가 명확하지 않음")
print("2. LLM이 JSON이 아닌 일반 텍스트로 응답")
print("3. LLM이 일부 필드를 누락하고 응답")
print("4. LLM이 올바른 JSON을 응답했지만 파싱에서 실패")
print("5. 키 매핑 문제 (Category vs category)")
print()

print("🚀 **지금 바로 테스트:**")
print("1. python llm_log_monitor.py monitor (새 터미널)")
print("2. 백엔드 재시작")
print("3. 관련성 평가 실행")
print("4. 로그에서 실제 프롬프트와 응답 확인!")
print()

print("이제 LLM이 정확히 어떤 응답을 하는지 실시간으로 확인할 수 있습니다!")
