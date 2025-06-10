#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LLM 로그 실시간 모니터링 도구
"""

import os
import time
import threading
from datetime import datetime

def monitor_llm_log():
    """LLM 로그 파일을 실시간으로 모니터링"""
    
    # 백엔드 폴더의 llm_log.txt 파일 경로
    backend_dir = "/Users/jongho.jung/Desktop/jongho_project/PoC/naver_news_searching/backend"
    log_file_path = os.path.join(backend_dir, "llm_log.txt")
    
    print("=== LLM API 로그 실시간 모니터링 ===")
    print(f"로그 파일: {log_file_path}")
    print("Ctrl+C로 종료")
    print("=" * 50)
    
    # 로그 파일이 없으면 생성
    if not os.path.exists(log_file_path):
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(f"# LLM API 로그 시작 - {datetime.now()}\n")
        print("로그 파일을 생성했습니다.")
    
    # 파일의 현재 크기 기록
    last_size = os.path.getsize(log_file_path)
    
    try:
        while True:
            time.sleep(1)  # 1초마다 확인
            
            current_size = os.path.getsize(log_file_path)
            
            # 파일 크기가 변경되면 새로운 내용 출력
            if current_size > last_size:
                with open(log_file_path, "r", encoding="utf-8") as f:
                    f.seek(last_size)  # 마지막 읽은 위치로 이동
                    new_content = f.read()
                    
                    if new_content.strip():
                        print(new_content, end="")
                
                last_size = current_size
    
    except KeyboardInterrupt:
        print("\n\n로그 모니터링을 종료합니다.")

def clear_log():
    """로그 파일 초기화"""
    backend_dir = "/Users/jongho.jung/Desktop/jongho_project/PoC/naver_news_searching/backend"
    log_file_path = os.path.join(backend_dir, "llm_log.txt")
    
    try:
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(f"# LLM API 로그 초기화 - {datetime.now()}\n")
        print(f"로그 파일이 초기화되었습니다: {log_file_path}")
    except Exception as e:
        print(f"로그 파일 초기화 실패: {e}")

def show_recent_logs(lines=50):
    """최근 로그 내용 표시"""
    backend_dir = "/Users/jongho.jung/Desktop/jongho_project/PoC/naver_news_searching/backend"
    log_file_path = os.path.join(backend_dir, "llm_log.txt")
    
    try:
        with open(log_file_path, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
        print(f"=== 최근 {len(recent_lines)}줄의 로그 ===")
        print("".join(recent_lines))
    except FileNotFoundError:
        print("로그 파일이 없습니다.")
    except Exception as e:
        print(f"로그 파일 읽기 실패: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "clear":
            clear_log()
        elif command == "show":
            lines = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            show_recent_logs(lines)
        elif command == "monitor":
            monitor_llm_log()
        else:
            print("사용법:")
            print("  python llm_log_monitor.py monitor   # 실시간 모니터링")
            print("  python llm_log_monitor.py clear     # 로그 파일 초기화")
            print("  python llm_log_monitor.py show [줄수] # 최근 로그 표시")
    else:
        print("=== LLM 로그 모니터링 도구 ===")
        print()
        print("사용법:")
        print("1. 실시간 모니터링:")
        print("   python llm_log_monitor.py monitor")
        print()
        print("2. 로그 파일 초기화:")
        print("   python llm_log_monitor.py clear")
        print()
        print("3. 최근 로그 보기:")
        print("   python llm_log_monitor.py show [줄수]")
        print()
        print("권장 사용법:")
        print("1. 터미널 1: 백엔드 서버 실행")
        print("2. 터미널 2: python llm_log_monitor.py monitor")
        print("3. 터미널 3: 프론트엔드에서 관련성 평가 실행")
        print("4. 터미널 2에서 실시간으로 LLM 호출 과정 확인")
