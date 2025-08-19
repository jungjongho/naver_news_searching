import apiClient from './client';

class AuthService {
  async login(email, password) {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    
    const response = await apiClient.post('/api/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async register(userData) {
    const response = await apiClient.post('/api/auth/register', userData);
    return response.data;
  }

  async getCurrentUser() {
    const response = await apiClient.get('/api/users/me');
    return response.data;
  }
}

export const authService = new AuthService();