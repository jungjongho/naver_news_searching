# 🐳 네이버 뉴스 스크랩 앱 - Docker 실행 가이드

## 📋 친구에게 전달하기

### 1단계: Docker Desktop 설치 (친구가 할 일)
- 🔗 https://www.docker.com/products/docker-desktop 방문
- 윈도우용 Docker Desktop 다운로드 및 설치
- 설치 후 재시작

### 2단계: 앱 폴더 받기
- `naver_news_searching` 폴더 전체를 받기
- 원하는 위치에 압축 해제

### 3단계: 앱 실행 (매우 간단!)
1. `naver_news_searching` 폴더로 이동
2. **Shift + 우클릭** → "여기서 PowerShell 창 열기" 또는 "여기서 명령 프롬프트 열기"
3. 다음 명령어 입력:
```bash
docker-compose up
```

### 4단계: 사용하기
- 자동으로 브라우저에서 http://localhost:3000 열기
- 네이버 뉴스 검색 시작!

### 5단계: 종료하기
- PowerShell/CMD 창에서 **Ctrl + C** 누르기
- 또는 다음 명령어:
```bash
docker-compose down
```

## ⚡ 한 줄 요약
```bash
# 실행
docker-compose up

# 종료  
docker-compose down
```

## 🎯 장점
- ✅ Python, Node.js 설치 불필요
- ✅ 환경 설정 걱정 없음
- ✅ 명령어 하나로 모든 것 실행
- ✅ 완전 격리된 환경

## 🛠️ 문제 해결
- **Docker Desktop이 실행 중인지 확인**
- **인터넷 연결 확인** (첫 실행시 이미지 다운로드)
- **방화벽 허용** (Docker Desktop)

---
**💡 더 간단하게:** 폴더에서 우클릭 → PowerShell → `docker-compose up` 입력 → 엔터!
