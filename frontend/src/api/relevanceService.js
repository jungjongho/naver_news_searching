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
  }
};

export default relevanceService;
