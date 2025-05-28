import apiClient from './client';

// 관련성 평가 API 서비스
const relevanceService = {
  // 관련성 평가 요청
  evaluateNews: async (filePath, apiKey, model = 'gpt-3.5-turbo') => {
    try {
      const response = await apiClient.post('/api/relevance/analyze', {
        file_path: filePath,
        api_key: apiKey,
        model,
      });
      return response.data;
    } catch (error) {
      console.error('관련성 평가 중 오류:', error);
      throw error;
    }
  }
};

export default relevanceService;
