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

function App() {
  return (
    <Router>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <Routes>
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
    </Router>
  );
}

export default App;
