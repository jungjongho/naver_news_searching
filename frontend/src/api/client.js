import axios from 'axios';

// 개선된 API 클라이언트 설정 (브라우저 환경 최적화)
const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
    'Connection': 'keep-alive',
    'Keep-Alive': 'timeout=300, max=1000'
  },
  timeout: 0, // 타임아웃 비활성화 (WebSocket으로 상태 관리)
  
  // HTTP/1.1 연결 관리 최적화
  maxRedirects: 5,
  maxContentLength: Infinity,
  maxBodyLength: Infinity,
});

// 요청 인터셉터 - 재시도 로직 추가
apiClient.interceptors.request.use(
  (config) => {
    // 🔐 JWT 토큰 자동 추가
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }


    // 긴 요청에 대한 특별 설정
    if (config.url && config.url.includes('/relevance/analyze')) {
      config.timeout = 0; // 관련성 분석은 타임아웃 없음
      config.headers['X-Request-Type'] = 'long-running';
    }
    
    console.log(`🚀 API 요청: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ 요청 설정 오류:', error);
    return Promise.reject(error);
  }
);

// 응답 인터셉터 - 네트워크 오류 재시도
apiClient.interceptors.response.use(
  (response) => {
    console.log(`✅ API 응답: ${response.config.method?.toUpperCase()} ${response.config.url} - ${response.status}`);
    return response;
  },
  async (error) => {
    const config = error.config;

    // 🔐 토큰 만료 처리 (401 Unauthorized)
    if (error.response?.status === 401) {
      console.warn('🔐 토큰이 만료되었습니다. 로그인 페이지로 이동합니다.');
      localStorage.removeItem('token');
      window.location.href = '/login';
      return Promise.reject(error);
    }
    
    // 🚫 권한 없음 처리 (403 Forbidden)
    if (error.response?.status === 403) {
      console.error('🚫 접근 권한이 없습니다.');
      // 권한 없음 알림 표시 (선택사항)
      return Promise.reject(error);
    }
    
    // 재시도 가능한 오류들
    const retryableErrors = [
      'ERR_NETWORK_IO_SUSPENDED',
      'ERR_CONNECTION_RESET',
      'ECONNRESET',
      'ENOTFOUND',
      'ECONNREFUSED',
      'ETIMEDOUT'
    ];
    
    const isRetryableError = retryableErrors.some(code => 
      error.code === code || error.message?.includes(code)
    );
    
     // 재시도 로직 (최대 3번) - 인증 오류는 재시도하지 않음
    if (isRetryableError && 
        config && 
        !config._retry && 
        (config._retryCount || 0) < 3 &&
        error.response?.status !== 401 && 
        error.response?.status !== 403) {
      
      config._retryCount = (config._retryCount || 0) + 1;
      config._retry = true;
      
      console.warn(`🔄 네트워크 오류 재시도 ${config._retryCount}/3: ${error.code || error.message}`);
      
      // 지수 백오프 (2초, 4초, 8초)
      const delay = Math.pow(2, config._retryCount) * 1000;
      await new Promise(resolve => setTimeout(resolve, delay));
      
      return apiClient(config);
    }
    
    // 오류 로깅 개선
    if (error.response) {
      console.error(`❌ API 응답 오류: ${error.response.status} ${error.response.statusText}`, error.response.data);
    } else if (error.request) {
      console.error(`❌ API 응답 없음: ${error.code || 'UNKNOWN'}`, error.message);
    } else {
      console.error(`❌ API 요청 설정 오류:`, error.message);
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;