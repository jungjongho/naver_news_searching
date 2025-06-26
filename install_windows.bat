@echo off
chcp 65001 > nul
color 0A
title 네이버 뉴스 스크랩 앱 - 설치

echo ========================================
echo     네이버 뉴스 스크랩 앱 설치
echo ========================================
echo.

REM Python 설치 확인
echo [1/4] Python 설치 확인 중...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되지 않았습니다.
    echo 🔗 https://www.python.org/downloads/ 에서 Python을 다운로드해주세요.
    echo    Python 3.8 이상 버전을 설치해주세요.
    echo.
    pause
    exit /b 1
)
echo ✅ Python 설치 확인됨

REM Node.js 설치 확인
echo [2/4] Node.js 설치 확인 중...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js가 설치되지 않았습니다.
    echo 🔗 https://nodejs.org 에서 Node.js를 다운로드해주세요.
    echo    LTS 버전을 추천합니다.
    echo.
    pause
    exit /b 1
)
echo ✅ Node.js 설치 확인됨

REM Python 가상환경 및 의존성 설치
echo [3/4] Python 백엔드 설정 중...
cd backend
if not exist venv (
    echo 가상환경을 생성하고 있습니다...
    python -m venv venv
)

echo Python 패키지를 설치하고 있습니다...
call venv\Scripts\activate.bat
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Python 패키지 설치에 실패했습니다.
    pause
    exit /b 1
)
call venv\Scripts\deactivate.bat
cd ..
echo ✅ Python 백엔드 설정 완료

REM Node.js 의존성 설치
echo [4/4] React 프론트엔드 설정 중...
cd frontend
echo Node.js 패키지를 설치하고 있습니다...
call npm install
if errorlevel 1 (
    echo ❌ Node.js 패키지 설치에 실패했습니다.
    pause
    exit /b 1
)
cd ..
echo ✅ React 프론트엔드 설정 완료

echo.
echo 🎉 설치가 완료되었습니다!
echo 이제 start_app.bat 파일을 실행해주세요.
echo.
pause
