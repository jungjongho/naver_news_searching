#!/bin/bash

# 네이버 뉴스 스크랩 프로젝트 실행 스크립트

echo "=== 네이버 뉴스 스크랩 프로젝트 시작 ==="

# 현재 디렉토리 확인
PROJECT_ROOT="/Users/jongho.jung/Desktop/jongho_project/PoC/naver_news_searching"

# 백엔드 시작
echo "백엔드 서버 시작 중..."
cd "$PROJECT_ROOT/backend"

# Python 가상환경 활성화 (존재하는 경우)
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "가상환경 활성화됨"
fi

# 백엔드 의존성 확인 및 설치
pip install -r requirements.txt > /dev/null 2>&1

# 백엔드 서버 시작 (백그라운드)
echo "백엔드 서버 시작: http://localhost:8000"
python run.py &
BACKEND_PID=$!

# 프론트엔드 시작
echo "프론트엔드 서버 시작 중..."
cd "$PROJECT_ROOT/frontend"

# Node.js 의존성 설치
if [ ! -d "node_modules" ]; then
    echo "의존성 설치 중..."
    npm install > /dev/null 2>&1
fi

# 프론트엔드 서버 시작 (백그라운드)
echo "프론트엔드 서버 시작: http://localhost:3000"
npm start &
FRONTEND_PID=$!

echo ""
echo "=== 서버 시작 완료 ==="
echo "백엔드: http://localhost:8000"
echo "프론트엔드: http://localhost:3000"
echo "프롬프트 관리 페이지: http://localhost:3000/prompts"
echo ""
echo "서버를 중지하려면 Ctrl+C를 누르세요"

# 트랩을 설정하여 스크립트가 종료될 때 백그라운드 프로세스도 종료
trap "echo '서버 종료 중...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT

# 백그라운드 프로세스가 종료될 때까지 대기
wait