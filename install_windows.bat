@echo off
chcp 65001 > nul
color 0A
title 네이버 뉴스 스크랩 앱 - 설치

echo ========================================
echo     네이버 뉴스 스크랩 앱 설치
echo ========================================
echo.

REM Python 설치 확인 (여러 경로 시도)
echo [1/4] Python 설치 확인 중...
set PYTHON_CMD=
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python
    echo ✅ Python 찾음: python
    goto :node_check
)

py --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=py
    echo ✅ Python 찾음: py
    goto :node_check
)

python3 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python3
    echo ✅ Python 찾음: python3
    goto :node_check
)

REM PATH에서 Python 찾기
for %%i in (python.exe) do (
    if exist "%%~$PATH:i" (
        set PYTHON_CMD=%%~$PATH:i
        echo ✅ Python 찾음: %%~$PATH:i
        goto :node_check
    )
)

REM 일반적인 설치 경로에서 Python 찾기
for %%d in (
    "%USERPROFILE%\AppData\Local\Programs\Python\Python*\python.exe"
    "C:\Python*\python.exe"
    "C:\Program Files\Python*\python.exe"
    "C:\Program Files (x86)\Python*\python.exe"
) do (
    for %%f in ("%%~d") do (
        if exist "%%f" (
            set PYTHON_CMD="%%f"
            echo ✅ Python 찾음: %%f
            goto :node_check
        )
    )
)

echo ❌ Python이 설치되지 않았거나 찾을 수 없습니다.
echo.
echo 📥 Python 설치 방법:
echo    1. https://www.python.org/downloads/ 방문
echo    2. 최신 Python 다운로드 (3.8 이상)
echo    3. 설치 시 "Add Python to PATH" 체크박스 반드시 선택!
echo    4. 설치 후 컴퓨터 재시작
echo.
pause
exit /b 1

:node_check
REM Node.js 설치 확인
echo [2/4] Node.js 설치 확인 중...
set NODE_CMD=
node --version >nul 2>&1
if not errorlevel 1 (
    set NODE_CMD=node
    set NPM_CMD=npm
    echo ✅ Node.js 찾음
    goto :install_backend
)

REM 일반적인 설치 경로에서 Node.js 찾기
for %%d in (
    "%PROGRAMFILES%\nodejs\node.exe"
    "%PROGRAMFILES(X86)%\nodejs\node.exe"
    "%USERPROFILE%\AppData\Roaming\npm\node.exe"
) do (
    if exist "%%d" (
        set NODE_CMD="%%d"
        set NPM_CMD="%%~dpd\npm.cmd"
        echo ✅ Node.js 찾음: %%d
        goto :install_backend
    )
)

echo ❌ Node.js가 설치되지 않았거나 찾을 수 없습니다.
echo.
echo 📥 Node.js 설치 방법:
echo    1. https://nodejs.org 방문
echo    2. LTS 버전 다운로드
echo    3. 설치 후 컴퓨터 재시작
echo.
pause
exit /b 1

:install_backend
REM Python 가상환경 및 의존성 설치
echo [3/4] Python 백엔드 설정 중...
cd backend
if not exist venv (
    echo 가상환경을 생성하고 있습니다...
    %PYTHON_CMD% -m venv venv
    if errorlevel 1 (
        echo ❌ 가상환경 생성에 실패했습니다.
        echo Python이 제대로 설치되었는지 확인해주세요.
        pause
        exit /b 1
    )
)

echo Python 패키지를 설치하고 있습니다...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Python 패키지 설치에 실패했습니다.
        echo 인터넷 연결을 확인하고 다시 시도해주세요.
        pause
        exit /b 1
    )
    call venv\Scripts\deactivate.bat
) else (
    echo ❌ 가상환경 활성화 스크립트를 찾을 수 없습니다.
    pause
    exit /b 1
)
cd ..
echo ✅ Python 백엔드 설정 완료

:install_frontend
REM Node.js 의존성 설치
echo [4/4] React 프론트엔드 설정 중...
cd frontend
echo Node.js 패키지를 설치하고 있습니다...
%NPM_CMD% install
if errorlevel 1 (
    echo ❌ Node.js 패키지 설치에 실패했습니다.
    echo 인터넷 연결을 확인하고 다시 시도해주세요.
    pause
    exit /b 1
)
cd ..
echo ✅ React 프론트엔드 설정 완료

echo.
echo 🎉 설치가 완료되었습니다!
echo 이제 start_app.bat 파일을 실행해주세요.
echo.
echo 사용된 명령어:
echo - Python: %PYTHON_CMD%
echo - Node.js: %NODE_CMD%
echo - NPM: %NPM_CMD%
echo.
pause
