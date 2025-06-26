@echo off
chcp 65001 > nul
color 0E
title 환경 진단 도구

echo ========================================
echo     시스템 환경 진단 도구
echo ========================================
echo.

echo 💻 시스템 정보:
echo    OS: %OS%
echo    사용자: %USERNAME%
echo    현재 경로: %CD%
echo.

echo 🔍 Python 설치 확인:
echo.

REM Python 명령어들 테스트
set FOUND_PYTHON=0

echo [테스트 1] python 명령어 확인:
python --version 2>nul
if not errorlevel 1 (
    echo ✅ python 명령어 작동함
    set FOUND_PYTHON=1
) else (
    echo ❌ python 명령어 작동하지 않음
)

echo.
echo [테스트 2] py 명령어 확인:
py --version 2>nul
if not errorlevel 1 (
    echo ✅ py 명령어 작동함
    set FOUND_PYTHON=1
) else (
    echo ❌ py 명령어 작동하지 않음
)

echo.
echo [테스트 3] python3 명령어 확인:
python3 --version 2>nul
if not errorlevel 1 (
    echo ✅ python3 명령어 작동함
    set FOUND_PYTHON=1
) else (
    echo ❌ python3 명령어 작동하지 않음
)

echo.
echo [테스트 4] 일반적인 설치 경로 확인:
for %%d in (
    "%USERPROFILE%\AppData\Local\Programs\Python\Python*\python.exe"
    "C:\Python*\python.exe"
    "C:\Program Files\Python*\python.exe"
    "C:\Program Files (x86)\Python*\python.exe"
) do (
    for %%f in ("%%~d") do (
        if exist "%%f" (
            echo ✅ Python 발견: %%f
            "%%f" --version 2>nul
            set FOUND_PYTHON=1
        )
    )
)

echo.
echo 🔍 Node.js 설치 확인:
echo.

set FOUND_NODE=0

echo [테스트 1] node 명령어 확인:
node --version 2>nul
if not errorlevel 1 (
    echo ✅ node 명령어 작동함
    set FOUND_NODE=1
) else (
    echo ❌ node 명령어 작동하지 않음
)

echo.
echo [테스트 2] npm 명령어 확인:
npm --version 2>nul
if not errorlevel 1 (
    echo ✅ npm 명령어 작동함
) else (
    echo ❌ npm 명령어 작동하지 않음
)

echo.
echo [테스트 3] 일반적인 설치 경로 확인:
for %%d in (
    "%PROGRAMFILES%\nodejs\node.exe"
    "%PROGRAMFILES(X86)%\nodejs\node.exe"
    "%USERPROFILE%\AppData\Roaming\npm\node.exe"
) do (
    if exist "%%d" (
        echo ✅ Node.js 발견: %%d
        "%%d" --version 2>nul
        set FOUND_NODE=1
    )
)

echo.
echo 🔍 PATH 환경변수 확인:
echo %PATH%
echo.

echo 📊 진단 결과:
if %FOUND_PYTHON%==1 (
    echo ✅ Python 설치됨
) else (
    echo ❌ Python 설치 필요
    echo    📥 https://www.python.org/downloads/ 에서 설치
    echo    ⚠️  설치 시 "Add Python to PATH" 반드시 체크!
)

if %FOUND_NODE%==1 (
    echo ✅ Node.js 설치됨  
) else (
    echo ❌ Node.js 설치 필요
    echo    📥 https://nodejs.org 에서 설치
)

echo.
if %FOUND_PYTHON%==1 if %FOUND_NODE%==1 (
    echo 🎉 모든 필수 프로그램이 설치되어 있습니다!
    echo    install_windows.bat를 실행하여 앱을 설치하세요.
) else (
    echo ⚠️  필수 프로그램 설치 후 컴퓨터를 재시작하고 다시 시도하세요.
)

echo.
pause
