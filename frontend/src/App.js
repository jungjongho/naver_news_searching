import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Box, CssBaseline } from '@mui/material';

// 레이아웃 컴포넌트
import MainLayout from './components/layouts/MainLayout';

// 페이지 컴포넌트
import HomePage from './pages/HomePage';
import CrawlerPage from './pages/CrawlerPage';
import DeduplicationPage from './pages/DeduplicationPage';
import RelevancePage from './pages/RelevancePage';
import ResultsPage from './pages/ResultsPage';
import PromptsPage from './pages/PromptsPage';
import NotFoundPage from './pages/NotFoundPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';

// 인증 관련
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/auth/ProtectedRoute';

// 파일 상단 import 부분에 추가

function App() {
  return (
    <Router>
      <CssBaseline />
       <AuthProvider>
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <Routes>
          {/* 인증이 필요 없는 라우트 */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
          <Route path="/" element={<MainLayout />}>
            <Route index element={<HomePage />} />
            <Route path="crawler" element={<CrawlerPage />} />
            <Route path="deduplication" element={<DeduplicationPage />} />
            <Route path="relevance" element={<RelevancePage />} />
            <Route path="results" element={<ResultsPage />} />
            <Route path="prompts" element={<PromptsPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </Box>
      </AuthProvider>
    </Router>
  );
}

export default App;
