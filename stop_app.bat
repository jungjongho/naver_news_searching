@echo off
chcp 65001 > nul
color 0C
title 네이버 뉴스 스크랩 앱 종료

echo ========================================
echo     네이버 뉴스 스크랩 앱 종료
echo ========================================
echo.

echo 🛑 앱을 종료하는 중...

REM Python 백엔드 프로세스 종료
echo    Python 백엔드 서버를 종료하는 중...
taskkill /f /im python.exe /fi "WINDOWTITLE eq 백엔드 서버" >nul 2>&1

REM Node.js 프론트엔드 프로세스 종료
echo    React 프론트엔드 서버를 종료하는 중...
taskkill /f /im node.exe /fi "WINDOWTITLE eq 프론트엔드 서버" >nul 2>&1

REM 관련된 모든 프로세스 정리
timeout /t 2 /nobreak >nul
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im node.exe >nul 2>&1

echo.
echo ✅ 앱이 완전히 종료되었습니다.
echo    모든 서버가 정상적으로 종료되었습니다.
echo.
pause
