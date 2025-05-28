import apiClient from './client';

// 크롤러 API 서비스
const crawlerService = {
  // 뉴스 크롤링 요청
  crawlNews: async (keywords, maxNewsPerKeyword = 100, sort = 'date', days = 30) => {
    try {
      const response = await apiClient.post('/api/crawler/crawl', {
        keywords,
        max_news_per_keyword: maxNewsPerKeyword,
        sort: sort,
        days: days
      });
      return response.data;
    } catch (error) {
      console.error('뉴스 크롤링 중 오류:', error);
      throw error;
    }
  },

  // 크롤링 결과 파일 목록 조회
  getFiles: async () => {
    try {
      const response = await apiClient.get('/api/crawler/files');
      return response.data.files;
    } catch (error) {
      console.error('파일 목록 조회 중 오류:', error);
      throw error;
    }
  },

  // 파일 내용 미리보기
  getFilePreview: async (fileName, maxRows = 5) => {
    try {
      const response = await apiClient.get(`/api/crawler/files/${fileName}/preview`, {
        params: { max_rows: maxRows },
      });
      return response.data;
    } catch (error) {
      console.error('파일 미리보기 중 오류:', error);
      throw error;
    }
  },

  // 파일 통계 정보 조회
  getFileStatistics: async (fileName) => {
    try {
      const response = await apiClient.get(`/api/crawler/files/${fileName}/statistics`);
      return response.data;
    } catch (error) {
      console.error('파일 통계 조회 중 오류:', error);
      throw error;
    }
  },
  
  // API 키 상태 확인
  checkApiKeyStatus: async () => {
    try {
      const response = await apiClient.get('/api-key-status');
      return response.data;
    } catch (error) {
      console.error('API 키 상태 확인 중 오류:', error);
      throw error;
    }
  }
};

export default crawlerService;
