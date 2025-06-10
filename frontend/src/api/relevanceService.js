import apiClient from './client';

// 관련성 평가 API 서비스
const relevanceService = {
  // 관련성 평가 요청
  evaluateNews: async (requestData) => {
    try {
      const response = await apiClient.post('/api/relevance/analyze', requestData);
      return response.data;
    } catch (error) {
      console.error('관련성 평가 중 오류:', error);
      throw error;
    }
  },
  
  // 관련성 분석 중지
  stopAnalysis: async (sessionId) => {
    try {
      const response = await apiClient.post(`/api/relevance/stop/${sessionId}`);
      return response.data;
    } catch (error) {
      console.error('분석 중지 중 오류:', error);
      throw error;
    }
  },
  
  // 분석 상태 확인
  getAnalysisStatus: async (sessionId) => {
    try {
      const response = await apiClient.get(`/api/relevance/status/${sessionId}`);
      return response.data;
    } catch (error) {
      console.error('분석 상태 확인 중 오류:', error);
      throw error;
    }
  }
};

export default relevanceService;
