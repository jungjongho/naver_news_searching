// src/api/promptService.js
import apiClient from './client';

export const promptService = {
  // 모든 프롬프트 조회
  getAllPrompts: async () => {
    const response = await apiClient.get('/api/prompts/');
    return response.data;
  },

  // 활성 프롬프트 조회
  getActivePrompt: async () => {
    const response = await apiClient.get('/api/prompts/active');
    return response.data;
  },

  // ID로 프롬프트 조회
  getPromptById: async (promptId) => {
    const response = await apiClient.get(`/api/prompts/${promptId}`);
    return response.data;
  },

  // 새 프롬프트 생성
  createPrompt: async (promptData) => {
    const response = await apiClient.post('/api/prompts/', promptData);
    return response.data;
  },

  // 프롬프트 수정
  updatePrompt: async (promptId, promptData) => {
    const response = await apiClient.put(`/api/prompts/${promptId}`, promptData);
    return response.data;
  },

  // 프롬프트 삭제
  deletePrompt: async (promptId) => {
    const response = await apiClient.delete(`/api/prompts/${promptId}`);
    return response.data;
  },

  // 프롬프트 활성화
  activatePrompt: async (promptId) => {
    const response = await apiClient.post(`/api/prompts/activate/${promptId}`);
    return response.data;
  },

  // 프롬프트 복제
  duplicatePrompt: async (promptId, newName = null) => {
    const params = newName ? { new_name: newName } : {};
    const response = await apiClient.post(`/api/prompts/duplicate/${promptId}`, {}, { params });
    return response.data;
  },

  // 프롬프트 미리보기
  previewPrompt: async (promptId, sampleTitle = '샘플 제목', sampleContent = '샘플 내용') => {
    const response = await apiClient.get(`/api/prompts/preview/${promptId}`, {
      params: {
        sample_title: sampleTitle,
        sample_content: sampleContent
      }
    });
    return response.data;
  },

  // 통합 프롬프트 컴파일
  compilePrompt: async (promptId, title = '', content = '') => {
    const response = await apiClient.get(`/api/prompts/compile/${promptId}`, {
      params: {
        title: title,
        content: content
      }
    });
    return response.data;
  }
};

export default promptService;
