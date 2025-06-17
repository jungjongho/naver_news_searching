# 관련성 평가 진행도 업데이트 문제 해결 가이드

## 즉시 확인해야 할 사항

### 1. 브라우저 개발자 도구 확인
```
F12 → Console 탭에서 다음 로그 확인:
- 🚀 WebSocket 연결 준비 시작...
- ✅ WebSocket 연결 성공: [session_id]
- 📊 WebSocket 메시지 수신: progress_update

오류가 있다면:
- ❌ WebSocket 오류: [오류 메시지]
- 🔌 WebSocket 연결 종료: [종료 코드]
```

### 2. 네트워크 탭에서 WebSocket 연결 확인
```
F12 → Network → WS 필터
- WebSocket 연결이 성공적으로 이루어졌는지 확인
- 연결 상태가 'Connection Established'인지 확인
```

### 3. 백엔드 서버 로그 확인
```
백엔드 서버 실행 터미널에서 다음 로그 확인:
- WebSocket 연결 요청: session_id=[id]
- WebSocket 연결 성공: session_id=[id]
- 관련성 분석 시작: [파일명]
- 진행률 전송 성공: [session_id] - [current]/[total]
```

## 가능한 문제와 해결책

### 문제 1: WebSocket 연결 실패
**증상**: 콘솔에 "WebSocket 오류" 또는 "연결 실패" 메시지
**해결**: 
1. 백엔드 서버가 8000 포트에서 실행 중인지 확인
2. 방화벽이 8000 포트를 차단하지 않는지 확인
3. localhost:8000에 직접 접속해서 서버 응답 확인

### 문제 2: 세션 ID 불일치
**증상**: WebSocket은 연결되지만 진행도 업데이트 없음
**해결**:
1. 콘솔에서 생성된 session_id 확인
2. 백엔드 로그에서 동일한 session_id로 요청이 들어오는지 확인

### 문제 3: AI 분석 자체가 시작되지 않음
**증상**: API 요청은 성공하지만 실제 분석이 시작되지 않음
**해결**:
1. API 키가 올바르게 설정되었는지 확인
2. 프롬프트 템플릿이 선택되었는지 확인
3. 백엔드 로그에서 분석 시작 메시지 확인

## 테스트 방법

### 1. 간단한 테스트
1. 크롤링된 파일 1개 선택
2. 관련성 평가 시작
3. 즉시 F12 → Console 확인
4. WebSocket 연결 메시지 확인

### 2. 백엔드 직접 테스트
```bash
# 백엔드 서버 재시작
cd backend
python run.py

# 로그 확인
tail -f 터미널 출력
```

### 3. WebSocket 수동 테스트
브라우저 콘솔에서:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/test-session');
ws.onopen = () => console.log('연결 성공');
ws.onerror = (e) => console.log('연결 실패:', e);
ws.onmessage = (e) => console.log('메시지:', e.data);
```

## 긴급 해결 방법

만약 WebSocket이 계속 작동하지 않는다면:

1. **폴링 방식으로 임시 대체**:
   - 3초마다 /api/relevance/status/{session_id} 호출
   - 진행 상황을 주기적으로 확인

2. **서버 재시작**:
   ```bash
   # 백엔드 서버 완전 재시작
   Ctrl+C (서버 종료)
   python run.py (서버 재시작)
   ```

3. **브라우저 캐시 클리어**:
   - 하드 새로고침: Ctrl+Shift+R
   - 또는 F12 → Application → Storage → Clear storage

## 로그 분석 요청사항

다음 정보를 제공해주세요:
1. 브라우저 콘솔의 WebSocket 관련 로그
2. 백엔드 서버 터미널의 최근 로그
3. Network 탭의 WebSocket 연결 상태
4. 관련성 평가 API 호출 응답 상태
