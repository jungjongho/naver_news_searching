import axios from 'axios';

// 기본 API 클라이언트 설정
const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 300000, // 5분 (크롤링은 시간이 오래 걸릴 수 있음)
});

// 요청 인터셉터 추가
apiClient.interceptors.request.use(
  (config) => {
    // 요청 전에 수행할 작업
    return config;
  },
  (error) => {
    // 요청 오류 처리
    return Promise.reject(error);
  }
);

// 응답 인터셉터 추가
apiClient.interceptors.response.use(
  (response) => {
    // 응답 데이터 처리
    return response;
  },
  (error) => {
    // 응답 오류 처리
    if (error.response) {
      // 서버가 2xx 외의 상태 코드로 응답한 경우
      console.error('API 응답 오류:', error.response.status, error.response.data);
    } else if (error.request) {
      // 요청이 전송되었으나 응답을 받지 못한 경우
      console.error('API 응답 없음:', error.request);
    } else {
      // 요청 설정 중 오류가 발생한 경우
      console.error('API 요청 오류:', error.message);
    }
    return Promise.reject(error);
  }
);

export default apiClient;
