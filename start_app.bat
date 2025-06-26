@echo off
chcp 65001 > nul
color 0B
title 네이버 뉴스 스크랩 앱 실행 중...

echo ========================================
echo     네이버 뉴스 스크랩 앱 시작
echo ========================================
echo.

REM 이전에 실행 중인 프로세스 종료
echo 🔄 이전 실행 중인 앱을 정리하는 중...
taskkill /f /im python.exe /fi "WINDOWTITLE eq 백엔드 서버" >nul 2>&1
taskkill /f /im node.exe /fi "WINDOWTITLE eq 프론트엔드 서버" >nul 2>&1

REM 백엔드 시작
echo [1/3] 🐍 Python 백엔드 서버를 시작하는 중...
cd backend
start /min cmd /k "title 백엔드 서버 && call venv\Scripts\activate.bat && python run.py"
cd ..

REM 백엔드 시작 대기
echo     백엔드 서버가 준비될 때까지 잠시 기다리는 중...
timeout /t 5 /nobreak >nul

REM 프론트엔드 시작
echo [2/3] ⚛️ React 프론트엔드를 시작하는 중...
cd frontend
start /min cmd /k "title 프론트엔드 서버 && npm start"
cd ..

REM 프론트엔드 시작 대기
echo     프론트엔드가 준비될 때까지 잠시 기다리는 중...
timeout /t 10 /nobreak >nul

REM 브라우저 열기
echo [3/3] 🌐 웹 브라우저를 여는 중...
start http://localhost:3000

echo.
echo 🎉 앱이 실행되었습니다!
echo.
echo 📌 사용법:
echo    - 웹 브라우저에서 http://localhost:3000 에 접속
echo    - 네이버 뉴스 검색 키워드를 입력하여 사용
echo.
echo 📌 종료하려면:
echo    - stop_app.bat 파일을 실행하거나
echo    - 이 창을 닫으세요
echo.
echo 💡 문제가 발생하면 stop_app.bat를 실행한 후 다시 시도해보세요.
echo.
pause
