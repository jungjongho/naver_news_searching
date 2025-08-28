// 파일 업로드 관련 API 서비스
import apiClient from './client';

class UploadService {
  /**
   * 엑셀 파일 업로드
   */
  async uploadExcelFile(file) {
    // FormData 객체 생성하여 파일 데이터 준비
    const formData = new FormData();
    formData.append('file', file);
    
    // axios를 통해 POST 요청 전송 (multipart/form-data)
    const response = await apiClient.post('/api/upload/excel', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      }
    });
    
    // 응답 데이터 반환
    return response.data;
  }
  
  /**
   * 파일 검증 요구사항 조회
   */
  async getValidationRequirements() {
    // GET 요청으로 업로드 파일 검증 규칙 조회
    const response = await apiClient.get('/api/upload/validation-requirements');
    return response.data;
  }
}

export default new UploadService();
