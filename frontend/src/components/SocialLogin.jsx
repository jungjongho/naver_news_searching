// 🔥 참고용 - 실제 프론트엔드 구현 예시
import React, { useState } from 'react';

const SocialLogin = () => {
  const [loading, setLoading] = useState(false);

  const handleSocialLogin = async (provider) => {
    try {
      setLoading(true);
      
      // 1. 소셜 로그인 URL 요청
      const urlResponse = await fetch(`/api/auth/${provider}/url`);
      const urlData = await urlResponse.json();
      
      if (urlData.auth_url) {
        // 2. 소셜 로그인 페이지로 리다이렉트
        window.location.href = urlData.auth_url;
      }
    } catch (error) {
      console.error('소셜 로그인 오류:', error);
      alert('로그인 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="social-login-container">
      <h2>로그인</h2>
      <p>소셜 계정으로 간편하게 로그인하세요</p>
      
      <div className="social-buttons">
        <button 
          onClick={() => handleSocialLogin('kakao')}
          disabled={loading}
          className="kakao-login-btn"
          style={{
            backgroundColor: '#FEE500',
            color: '#000',
            border: 'none',
            padding: '12px 24px',
            borderRadius: '8px',
            margin: '8px',
            cursor: 'pointer'
          }}
        >
          카카오로 로그인
        </button>
        
        <button 
          onClick={() => handleSocialLogin('naver')}
          disabled={loading}
          className="naver-login-btn"
          style={{
            backgroundColor: '#03C75A',
            color: '#fff',
            border: 'none',
            padding: '12px 24px',
            borderRadius: '8px',
            margin: '8px',
            cursor: 'pointer'
          }}
        >
          네이버로 로그인
        </button>
      </div>
    </div>
  );
};

export default SocialLogin;