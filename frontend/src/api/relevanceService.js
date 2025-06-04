import apiClient from './client';

// 관련성 평가 API 서비스
const relevanceService = {
  // 관련성 평가 요청 (비동기 - 백그라운드 처리)
  evaluateNews: async (requestData) => {
    try {
      const response = await apiClient.post('/api/relevance/analyze', requestData);
      return response.data;
    } catch (error) {
      console.error('관련성 평가 중 오류:', error);
      throw error;
    }
  },

  // 관련성 평가 요청 (동기 - 즉시 결과 반환)
  evaluateNewsSync: async (requestData) => {
    try {
      const response = await apiClient.post('/api/relevance/analyze-sync', requestData);
      return response.data;
    } catch (error) {
      console.error('동기 관련성 평가 중 오류:', error);
      throw error;
    }
  },

  // 분석 상태 확인
  checkAnalysisStatus: async (fileName) => {
    try {
      const response = await apiClient.get(`/api/relevance/status/${fileName}`);
      return response.data;
    } catch (error) {
      console.error('분석 상태 확인 중 오류:', error);
      throw error;
    }
  }
};

export default relevanceService;
