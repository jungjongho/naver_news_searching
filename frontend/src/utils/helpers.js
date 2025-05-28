// 날짜 포맷팅 함수
export const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

// 파일 크기 포맷팅 함수
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 텍스트 줄임 처리 함수
export const truncateText = (text, maxLength) => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
};

// CSV 파일 다운로드 URL 생성 함수
export const getFileDownloadUrl = (filePath) => {
  const baseUrl = process.env.REACT_APP_API_URL || '';
  return `${baseUrl}/results/${encodeURIComponent(filePath)}`;
};

// 키워드 목록에서 중복 제거 함수
export const removeDuplicates = (keywords) => {
  return [...new Set(keywords.map(k => k.trim()))].filter(k => k !== '');
};

// 카테고리 색상 지정 함수
export const getCategoryColor = (category) => {
  const categoryColors = {
    '자사 언급기사': '#1976d2', // 파란색
    '업계 관련기사': '#388e3c', // 녹색
    '건강기능식품·펫푸드': '#f57c00', // 주황색
    '기타': '#757575', // 회색
  };
  
  return categoryColors[category] || '#757575';
};

// 로컬 스토리지 유틸리티
export const storage = {
  get: (key, defaultValue = null) => {
    try {
      const value = localStorage.getItem(key);
      return value !== null ? JSON.parse(value) : defaultValue;
    } catch (error) {
      console.error('로컬 스토리지 데이터 읽기 실패:', error);
      return defaultValue;
    }
  },
  
  set: (key, value) => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (error) {
      console.error('로컬 스토리지 데이터 저장 실패:', error);
      return false;
    }
  },
  
  remove: (key) => {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (error) {
      console.error('로컬 스토리지 데이터 삭제 실패:', error);
      return false;
    }
  }
};
