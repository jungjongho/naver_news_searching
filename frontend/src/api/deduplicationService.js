// 중복 제거 API 서비스
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class DeduplicationService {
  /**
   * 뉴스 기사 중복 제거 (GPT 임베딩 방식)
   */
  async removeDuplicates(filePath, apiKey, similarityThreshold = 0.85, batchSize = 50, sessionId = null) {
    try {
      // API 키 검증
      if (!apiKey || !apiKey.trim()) {
        throw new Error('OpenAI API 키가 필요합니다.');
      }

      const response = await fetch(`${API_BASE_URL}/api/deduplication/remove`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file_path: filePath,
          api_key: apiKey,
          similarity_threshold: similarityThreshold,
          batch_size: batchSize,
          session_id: sessionId,
          embedding_model: 'text-embedding-3-small'
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || errorData.message || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('GPT 임베딩 중복 제거 응답:', data);
      return data;
    } catch (error) {
      console.error('GPT 임베딩 중복 제거 요청 오류:', error);
      throw error;
    }
  }

  /**
   * 중복 제거 중지
   */
  async stopDeduplication(sessionId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/deduplication/stop/${sessionId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('중복 제거 중지 요청 오류:', error);
      throw error;
    }
  }

  /**
   * 중복 제거 상태 확인
   */
  async getDeduplicationStatus(sessionId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/deduplication/status/${sessionId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('중복 제거 상태 확인 오류:', error);
      throw error;
    }
  }

  /**
   * 결과 파일 자동 다운로드
   */
  async downloadResultFile(filePath, fileName = null) {
    try {
      // 파일명이 전체 경로인 경우 기본명만 추출
      const actualFileName = fileName || filePath.split('/').pop() || filePath;
      
      console.log('다운로드 시도:', { filePath, actualFileName });
      
      // 브라우저에서 직접 다운로드 트리거 (새 탭 열리지 않도록 수정)
      const link = document.createElement('a');
      link.href = `${API_BASE_URL}/api/download/${encodeURIComponent(actualFileName)}`; // 다운로드 API 사용
      link.download = actualFileName;
      // link.target = '_blank'; // 이 줄을 제거하여 새 탭이 열리지 않도록 함
      
      // 숨겨진 상태로 DOM에 추가
      link.style.display = 'none';
      document.body.appendChild(link);
      
      // 클릭 이벤트 트리거
      link.click();
      
      // 약간의 지연 후 DOM에서 제거
      setTimeout(() => {
        document.body.removeChild(link);
      }, 100);
      
      console.log('파일 다운로드 시작:', actualFileName);
      return true;
    } catch (error) {
      console.error('파일 다운로드 오류:', error);
      return false;
    }
  }
}

export default new DeduplicationService();
