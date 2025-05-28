# 네이버 뉴스 검색 서비스

네이버 뉴스 API를 활용한 뉴스 검색 및 분석 웹 서비스입니다.

## 프로젝트 구조

- `/backend`: FastAPI 기반 백엔드 서버
- `/frontend`: React 기반 프론트엔드 웹 애플리케이션

## 백엔드 설정 및 실행

1. 파이썬 가상환경 설정

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

3. 환경 설정

`.env.example` 파일을 복사하여 `.env` 파일을 생성하고 네이버 API 키 등 필요한 설정을 입력합니다.

```bash
cp .env.example .env
# .env 파일을 편집하여 NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET 값을 입력합니다.
```

4. 서버 실행

```bash
python run.py
```

## 프론트엔드 설정 및 실행

1. 필요한 패키지 설치

```bash
cd frontend
npm install
```

2. 환경 설정

`.env.example` 파일을 복사하여 `.env` 파일을 생성하고 API 서버 URL을 설정합니다.

```bash
cp .env.example .env
# 기본값인 http://localhost:8000을 사용하거나 백엔드 서버 URL에 맞게 수정합니다.
```

3. 개발 서버 실행

```bash
npm start
```

## API 문서

백엔드 서버가 실행되면 다음 URL에서 API 문서를 확인할 수 있습니다:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 주요 기능

1. **뉴스 검색**: 키워드 기반 네이버 뉴스 검색
2. **결과 저장**: CSV 또는 Excel 파일로 검색 결과 저장
3. **관련성 분석**: 뉴스 기사의 관련성 분석
4. **통계 정보**: 수집된 뉴스 데이터의 통계 정보 제공

## 네이버 API 키 발급 방법

1. [네이버 개발자 센터](https://developers.naver.com/)에 접속합니다.
2. "로그인" 후 "애플리케이션 등록"을 선택합니다.
3. 애플리케이션 이름과 사용 API를 설정합니다 (여기서는 "검색" API를 선택).
4. 애플리케이션 등록 후 발급된 "Client ID"와 "Client Secret"을 `.env` 파일에 입력합니다.
