@echo off
chcp 65001 > nul
color 0E
title 네이버 뉴스 스크랩 앱 - 빠른 시작

echo ========================================
echo     네이버 뉴스 스크랩 앱 
echo     빠른 시작 가이드
echo ========================================
echo.

echo 📋 처음 사용하시나요?
echo.
echo 1. Python 설치 (https://www.python.org/downloads/)
echo 2. Node.js 설치 (https://nodejs.org)
echo 3. install_windows.bat 실행 (한 번만)
echo 4. start_app.bat 실행
echo.
echo 📋 이미 설치했다면?
echo.
echo start_app.bat 파일을 더블클릭하세요!
echo.
echo ========================================
echo.

set /p choice="설치하시겠습니까? (y/n): "
if /i "%choice%"=="y" (
    echo 설치를 시작합니다...
    call install_windows.bat
) else (
    echo 앱을 실행합니다...
    call start_app.bat
)

pause
