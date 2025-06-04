# 네이버 뉴스 검색 프로젝트 Context

## 📅 작업 이력

### 2025-06-04 18:30 - 프로젝트 분석 및 Context 작성
- 프로젝트 전체 구조 분석 완료
- 주요 기능 및 파일 구조 정리
- Context 문서 초기 작성

### 2025-06-04 20:45 - 진행도 추적 기능 구현 완료 ⭐
- **백엔드 진행도 추적 시스템 구축**
  - `progress_service.py` 새로 생성 - 실시간 작업 진행도 추적
  - `relevance_service_optimized.py` 확장 - 진행도 추적 분석 메서드 추가
  - 새로운 API 엔드포인트 추가:
    - `/api/relevance/analyze-with-progress` - 진행도 추적 분석 시작
    - `/api/relevance/progress/{task_id}` - 특정 작업 진행도 조회
    - `/api/relevance/progress` - 모든 작업 진행도 조회

- **프론트엔드 진행도 UI 컴포넌트 구현**
  - `ProgressTracker.js` 새로 생성 - 실시간 진행도 시각화
  - `RelevancePage.js` 대폭 개선 - 3가지 분석 방식 지원
  - `relevanceService.js` 확장 - 진행도 추적 API 함수 추가

- **주요 개선사항**
  - 실시간 진행률 표시 (퍼센트, 진행바)
  - 배치별 처리 상황 모니터링
  - 현재 처리 중인 기사 제목 표시
  - 경과 시간 및 예상 남은 시간 계산
  - 처리 속도 (항목/초) 표시
  - 성공/오류 통계 실시간 업데이트

---

## 🏗️ 프로젝트 구조

### 전체 구조
```
naver_news_searching/
├── backend/           # FastAPI 백엔드 서버
├── frontend/          # React 프론트엔드
├── utils/             # 공통 유틸리티
└── temp_delete/       # 임시 삭제 예정 파일
```

---

## 🔧 백엔드 (FastAPI)

### 핵심 파일
```
backend/
├── run.py                    # 서버 실행 진입점
├── app/
│   ├── main.py              # FastAPI 애플리케이션 설정
│   ├── api/endpoints/       # API 엔드포인트
│   │   ├── crawler.py       # 뉴스 크롤링 API
│   │   ├── relevance.py     # 관련성 분석 API (진행도 추적 포함) ✨
│   │   ├── download.py      # 파일 다운로드 API
│   │   └── prompts.py       # 프롬프트 관리 API
│   ├── services/            # 비즈니스 로직
│   │   ├── naver_api_service.py           # 네이버 API 호출
│   │   ├── relevance_service.py           # 기본 관련성 분석
│   │   ├── relevance_service_optimized.py # 최적화된 관련성 분석 (진행도 추적) ✨
│   │   ├── relevance_service_debug.py     # 디버그용 관련성 분석
│   │   ├── prompt_service.py              # 프롬프트 관리
│   │   └── progress_service.py            # 진행도 추적 서비스 ✨ NEW
│   ├── models/              # 데이터 모델
│   ├── utils/               # 유틸리티 함수
│   └── core/                # 설정 및 공통 기능
├── results/                 # 결과 파일 저장
│   ├── crawling/           # 크롤링 원본 결과
│   └── relevance/          # 관련성 분석 결과
└── requirements.txt        # 의존성 패키지
```

### 주요 기능
1. **뉴스 크롤링**: 네이버 뉴스 API를 통한 키워드 기반 뉴스 수집
2. **관련성 분석**: OpenAI/Anthropic LLM을 활용한 뉴스 관련성 분석
3. **진행도 추적**: 실시간 분석 진행 상황 모니터링 ⭐ NEW
4. **파일 관리**: 결과 파일 저장, 조회, 다운로드
5. **프롬프트 관리**: 분석용 프롬프트 템플릿 관리

### 새로 추가된 진행도 추적 기능
- **ProgressService**: 작업 생성, 상태 업데이트, 통계 계산
- **진행도 정보**: 처리율, 경과시간, 예상 남은시간, 처리속도, 오류통계
- **실시간 업데이트**: 배치별 진행 상황 실시간 업데이트

### 주요 의존성
- FastAPI: 웹 프레임워크
- pandas: 데이터 처리
- openai/anthropic: LLM API
- requests: HTTP 클라이언트

---

## 🎨 프론트엔드 (React)

### 핵심 파일
```
frontend/
├── src/
│   ├── App.js               # 메인 애플리케이션
│   ├── pages/               # 페이지 컴포넌트
│   │   ├── HomePage.js      # 홈 페이지
│   │   ├── CrawlerPage.js   # 뉴스 크롤링 페이지
│   │   ├── RelevancePage.js # 관련성 분석 페이지 (3가지 분석방식 지원) ✨
│   │   ├── ResultsPage.js   # 결과 목록 페이지
│   │   ├── PromptsPage.js   # 프롬프트 관리 페이지
│   │   └── NotFoundPage.js  # 404 페이지
│   ├── components/          # 재사용 컴포넌트
│   │   └── common/
│   │       └── ProgressTracker.js # 진행도 추적 컴포넌트 ✨ NEW
│   ├── api/                 # API 서비스
│   │   └── relevanceService.js # 관련성 API 서비스 (진행도 API 추가) ✨
│   ├── utils/               # 유틸리티 함수
│   └── theme.js             # Material-UI 테마
└── package.json             # 의존성 및 스크립트
```

### 주요 기능
1. **키워드 검색**: 직접 입력 또는 카테고리 선택으로 뉴스 검색
2. **결과 분석**: LLM 기반 뉴스 관련성 분석 인터페이스
3. **진행도 모니터링**: 실시간 분석 진행 상황 시각화 ⭐ NEW
4. **파일 관리**: 결과 파일 목록, 미리보기, 다운로드
5. **프롬프트 편집**: 분석용 프롬프트 템플릿 수정

### 새로 추가된 진행도 UI 기능
- **ProgressTracker 컴포넌트**: 시각적 진행률 표시, 실시간 업데이트
- **3가지 분석 방식**: 진행도 추적(추천), 동기, 비동기
- **상세 진행 정보**: 현재 처리 기사, 시간 정보, 처리 속도, 통계

### 주요 의존성
- React: UI 라이브러리
- Material-UI: UI 컴포넌트
- React Router: 페이지 라우팅
- Axios: HTTP 클라이언트
- Chart.js: 데이터 시각화

---

## 🔄 주요 워크플로우

### 1. 뉴스 크롤링 플로우
```
사용자 입력 → CrawlerPage.js → /api/crawler/crawl → naver_api_service.py → results/crawling/
```

### 2. 관련성 분석 플로우 (기존)
```
파일 선택 → RelevancePage.js → /api/relevance/analyze → relevance_service.py → LLM API → results/relevance/
```

### 3. 진행도 추적 분석 플로우 ✨ NEW
```
파일 선택 → RelevancePage.js → /api/relevance/analyze-with-progress → 
progress_service.py (작업 생성) → relevance_service_optimized.py (진행도 업데이트) → 
ProgressTracker.js (실시간 표시) → results/relevance/
```

### 4. 결과 조회 플로우
```
ResultsPage.js → /api/crawler/files → 파일 목록 → 미리보기/다운로드
```

---

## 🎯 코스맥스 맞춤 기능

### 분석 카테고리
1. **자사 언급기사**: '코스맥스' 직접 언급
2. **업계 관련기사**: 화장품/뷰티 업계 동향
3. **건강기능식품·펫푸드**: 관련 시장 정보
4. **기타**: 간접적 참고 가능 기사

### 추천 키워드 카테고리
- **화장품**: 코스맥스, 코스맥스엔비티, 콜마, HK이노엔, 아모레퍼시픽, LG생활건강, 올리브영, 화장품, 뷰티
- **건강기능식품**: 건강기능식품, 펫푸드, 마이크로바이옴, 식품의약품안전처

---

## 🔍 주요 수정 포인트

### 최근 개선사항 (v1.2.0) ✨ 진행도 추적 기능
1. **실시간 진행도 모니터링**
   - 배치별 처리 상황 실시간 표시
   - 현재 처리 중인 기사 제목 표시
   - 경과 시간 및 예상 남은 시간 계산

2. **분석 방식 다양화**
   - 진행도 추적 방식 (추천): 실시간 모니터링 + 자동 완료 이동
   - 동기 방식: 완료까지 대기 후 즉시 결과 확인
   - 비동기 방식: 백그라운드 처리 + 완료 시 알림

3. **성능 및 통계 정보**
   - 처리 속도 (항목/초) 표시
   - 성공/오류 통계 실시간 업데이트
   - 작업 ID 기반 추적 시스템

### 이전 개선사항 (v1.1.0)
1. **크롤링 개수 자유 설정**: 1-1000개 자유 입력 가능
2. **폴더 구조 분리**: crawling/relevance 폴더 분리
3. **파일 관리 개선**: 통합 파일 목록 및 자동 경로 탐지

### 개발 시 주의사항
1. **모듈화**: 기능별로 적절히 분리된 구조 유지
2. **에러 처리**: API 호출 및 파일 처리 시 예외 상황 고려
3. **성능 최적화**: 대용량 파일 처리 시 메모리 효율성 고려
4. **사용자 경험**: 비동기 작업 시 진행 상태 표시 ⭐
5. **진행도 추적**: 장시간 작업 시 사용자에게 명확한 진행 상황 제공

---

## 🎨 진행도 추적 시스템 상세

### 백엔드 진행도 추적 구조
```python
@dataclass
class ProgressInfo:
    task_id: str                    # 고유 작업 ID
    total_items: int               # 총 처리할 항목 수
    processed_items: int           # 처리 완료된 항목 수
    current_status: str            # 현재 상태 메시지
    current_batch: int             # 현재 배치 번호
    total_batches: int             # 총 배치 수
    current_item_title: str        # 현재 처리 중인 기사 제목
    start_time: float              # 시작 시간
    estimated_time_remaining: float # 예상 남은 시간
    items_per_second: float        # 처리 속도
    errors: int                    # 오류 수
    success_items: int             # 성공 수
```

### 프론트엔드 진행도 UI 구성
- **진행률 바**: 전체 진행 상황 시각적 표시
- **배치 정보**: 현재 배치/전체 배치 표시
- **현재 처리 항목**: 실시간 처리 중인 기사 제목
- **시간 정보**: 경과 시간, 예상 완료 시간
- **성능 지표**: 처리 속도, 성공/실패 통계
- **작업 상태**: 시작됨, 처리 중, 완료됨, 실패

---

## 🚀 실행 방법

### 백엔드
```bash
cd backend
pip install -r requirements.txt
python run.py
```

### 프론트엔드
```bash
cd frontend
npm install
npm start
```

---

## 📁 중요 설정 파일

### 환경 변수
- `backend/.env`: 네이버 API 키 설정
- `frontend/.env`: 프론트엔드 환경 설정

### 설정
- `backend/app/core/config.py`: 백엔드 설정
- `frontend/src/theme.js`: UI 테마 설정

---

## 🔧 향후 개발 가이드

### 새 기능 추가 시
1. **백엔드**: `app/api/endpoints/`에 라우터 추가, `app/services/`에 비즈니스 로직 구현
2. **프론트엔드**: `src/pages/`에 페이지 추가, `src/components/`에 컴포넌트 구현
3. **API 연동**: `src/api/`에 API 서비스 함수 추가

### 기존 기능 수정 시
1. **크롤링 관련**: `naver_api_service.py`, `CrawlerPage.js` 수정
2. **분석 관련**: `relevance_service.py`, `RelevancePage.js` 수정
3. **진행도 추적**: `progress_service.py`, `ProgressTracker.js` 수정 ⭐
4. **파일 관리**: `crawler.py` (API), `ResultsPage.js` 수정

### 진행도 추적 시스템 확장 가이드
1. **새로운 진행도 필드 추가**: `ProgressInfo` 클래스 확장
2. **UI 컴포넌트 개선**: `ProgressTracker.js`에 새로운 시각화 요소 추가
3. **다른 작업에 적용**: 크롤링 등 다른 장시간 작업에도 진행도 추적 적용 가능

---

## 🎯 권장 사용 방법

### 관련성 분석 시
1. **소량 데이터 (50개 이하)**: 동기 방식 추천
2. **중간 데이터 (50-200개)**: 진행도 추적 방식 추천 ⭐
3. **대량 데이터 (200개 이상)**: 진행도 추적 방식 필수 ⭐

### 진행도 모니터링 활용
- 예상 완료 시간을 통한 작업 계획 수립
- 처리 속도를 통한 성능 모니터링
- 오류 통계를 통한 문제 조기 발견

---

*최종 업데이트: 2025-06-04 20:45 - 진행도 추적 기능 구현 완료* ⭐