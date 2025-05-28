import apiClient from './client';

// 파일 다운로드 링크 가져오기
export const getDownloadLink = async (fileName) => {
  try {
    const response = await apiClient.get(`/api/crawler/files/${fileName}/download-link`);
    return response.data;
  } catch (error) {
    console.error('다운로드 링크 가져오기 실패:', error);
    throw error;
  }
};

// 파일 직접 다운로드
export const downloadFile = (fileName) => {
  const downloadUrl = `${apiClient.defaults.baseURL}/api/download/${fileName}`;
  
  // 새 창에서 다운로드 링크 열기 (또는 직접 다운로드)
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.target = '_blank';
  link.download = fileName;
  link.click();
};

// 압축 파일 다운로드
export const downloadZipFolder = (folderName) => {
  const downloadUrl = `${apiClient.defaults.baseURL}/api/download/zip/${folderName}`;
  
  // 새 창에서 다운로드 링크 열기 (또는 직접 다운로드)
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.target = '_blank';
  link.download = `${folderName}.zip`;
  link.click();
};

export default {
  getDownloadLink,
  downloadFile,
  downloadZipFolder,
};
