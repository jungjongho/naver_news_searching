# 백엔드 Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 포트 노출
EXPOSE 8000

# 건강 체크 엔드포인트 추가를 위한 임시 파일
RUN echo 'from fastapi import FastAPI\nfrom fastapi.responses import JSONResponse\n\n@app.get("/health")\nasync def health_check():\n    return JSONResponse({"status": "healthy"})' > health_check.py

# 서버 실행
CMD ["python", "run.py"]
