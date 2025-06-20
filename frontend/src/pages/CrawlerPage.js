import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Paper,
  Typography,
  Grid,
  Divider,
} from '@mui/material';

import PageTitle from '../components/common/PageTitle';
import AlertMessage from '../components/common/AlertMessage';
import LoadingOverlay from '../components/common/LoadingOverlay';

// 분리된 컴포넌트들
import KeywordInput from '../components/crawler/KeywordInput';
import CrawlSettings from '../components/crawler/CrawlSettings';
import SavedKeywords from '../components/crawler/SavedKeywords';
import CrawlerHelp from '../components/crawler/CrawlerHelp';

// 분리된 훅들
import { useCrawlerState } from '../hooks/useCrawlerState';
import { useKeywordManager } from '../hooks/useKeywordManager';
import { useCrawlSettings } from '../hooks/useCrawlSettings';

// 서비스 및 설정
import crawlerService from '../api/crawlerService';
import { MESSAGES } from '../config/crawlerConfig';

const CrawlerPage = () => {
  const navigate = useNavigate();
  
  // 상태 관리
  const crawlerState = useCrawlerState();
  
  // 키워드 관리
  const keywordManager = useKeywordManager(
    crawlerState.keywords,
    crawlerState.setKeywords,
    crawlerState.newKeyword,
    crawlerState.setNewKeyword,
    crawlerState.savedKeywords,
    crawlerState.setSavedKeywords,
    crawlerState.selectedCategory,
    crawlerState.setSelectedCategory,
    crawlerState.showAlert
  );
  
  // 크롤링 설정 관리
  const crawlSettings = useCrawlSettings(
    crawlerState.maxNewsPerKeyword,
    crawlerState.setMaxNewsPerKeyword,
    crawlerState.dateFilterType,
    crawlerState.setDateFilterType,
    crawlerState.days,
    crawlerState.setDays,
    crawlerState.startDate,
    crawlerState.setStartDate,
    crawlerState.endDate,
    crawlerState.setEndDate
  );

  // 뉴스 크롤링 실행
  const handleCrawl = async () => {
    // 키워드 검증
    if (crawlerState.keywords.length === 0) {
      crawlerState.showAlert('error', MESSAGES.ERROR.NO_KEYWORDS);
      return;
    }
    
    // 설정 검증
    const validationError = crawlSettings.validateSettings();
    if (validationError) {
      crawlerState.showAlert('error', validationError);
      return;
    }
    
    // 설정 저장
    crawlerState.saveCurrentSettings();
    
    crawlerState.setLoading(true);
    
    try {
      const settings = crawlSettings.getFinalSettings();
      
      let result;
      if (settings.dateFilterType === 'range') {
        result = await crawlerService.crawlNews(
          crawlerState.keywords, 
          settings.maxNewsPerKeyword, 
          'date', 
          30, // days는 사용되지 않지만 기본값 전달
          settings.startDate, 
          settings.endDate
        );
      } else {
        result = await crawlerService.crawlNews(
          crawlerState.keywords, 
          settings.maxNewsPerKeyword, 
          'date', 
          settings.days
        );
      }
      
      if (result.success) {
        // 성공 메시지 생성
        let successMessage = MESSAGES.SUCCESS.CRAWL_COMPLETE(result.item_count);
        if (result.download_path) {
          successMessage += ` ${MESSAGES.SUCCESS.DOWNLOAD_SAVED(result.download_path)}`;
        }
        
        crawlerState.showAlert('success', successMessage);
        
        // 결과 페이지로 이동 (0.5초 후)
        setTimeout(() => {
          navigate('/deduplication', { 
            state: { 
              crawlResult: result,
              fromCrawler: true
            }
          });
        }, 500);
      } else {
        crawlerState.showAlert('error', MESSAGES.ERROR.CRAWL_FAILED(result.message));
      }
    } catch (error) {
      console.error('뉴스 크롤링 오류:', error);
      crawlerState.showAlert('error', MESSAGES.ERROR.UNEXPECTED_ERROR(error.message));
    } finally {
      crawlerState.setLoading(false);
    }
  };

  return (
    <Box>
      <PageTitle 
        title="뉴스 수집" 
        subtitle="네이버 뉴스에서 키워드 기반으로 최신 뉴스를 수집합니다."
        breadcrumbs={[{ text: '뉴스 수집', path: '/crawler' }]}
      />
      
      <AlertMessage
        open={crawlerState.alert.open}
        type={crawlerState.alert.type}
        message={crawlerState.alert.message}
        onClose={crawlerState.closeAlert}
      />
      
      <Grid container spacing={3}>
        {/* 왼쪽 영역: 키워드 입력 및 설정 */}
        <Grid item xs={12} md={8}>
          {/* 키워드 입력 섹션 */}
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              검색 키워드
            </Typography>
            
            <KeywordInput
              keywords={crawlerState.keywords}
              newKeyword={crawlerState.newKeyword}
              selectedCategory={crawlerState.selectedCategory}
              onNewKeywordChange={(e) => crawlerState.setNewKeyword(e.target.value)}
              onKeywordInputKeyPress={keywordManager.handleKeywordInputKeyPress}
              onAddKeyword={keywordManager.handleAddKeyword}
              onCategorySelect={keywordManager.handleCategorySelect}
              onDeleteKeyword={keywordManager.handleDeleteKeyword}
              onSaveKeywords={keywordManager.handleSaveKeywords}
              onClearAllKeywords={keywordManager.handleClearAllKeywords}
            />
          </Paper>
          
          {/* 크롤링 설정 섹션 */}
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              크롤링 설정
            </Typography>
            
            <CrawlSettings
              maxNewsPerKeyword={crawlerState.maxNewsPerKeyword}
              dateFilterType={crawlerState.dateFilterType}
              days={crawlerState.days}
              startDate={crawlerState.startDate}
              endDate={crawlerState.endDate}
              onMaxNewsChange={crawlSettings.handleMaxNewsChange}
              onMaxNewsBlur={crawlSettings.handleMaxNewsBlur}
              onDateFilterTypeChange={crawlSettings.handleDateFilterTypeChange}
              onDaysChange={crawlSettings.handleDaysChange}
              onStartDateChange={crawlSettings.handleStartDateChange}
              onEndDateChange={crawlSettings.handleEndDateChange}
              getDateRangeDescription={crawlSettings.getDateRangeDescription}
            />
            
            <Divider sx={{ mb: 3 }} />
            
            {/* 실행 버튼 */}
            <Box sx={{ textAlign: 'center' }}>
              <Button
                variant="contained"
                color="primary"
                size="large"
                onClick={handleCrawl}
                disabled={crawlerState.keywords.length === 0 || crawlerState.loading}
                sx={{ px: 4, py: 1 }}
              >
                뉴스 수집 시작
              </Button>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                총 {crawlerState.keywords.length}개 키워드, 
                최대 {crawlerState.keywords.length * crawlSettings.getDisplayMaxNews()}개의 뉴스 기사를 수집합니다.
                {crawlerState.dateFilterType === 'range' && crawlerState.startDate && crawlerState.endDate && 
                  ` (${crawlerState.startDate} ~ ${crawlerState.endDate})`
                }
                {crawlerState.dateFilterType === 'days' && 
                  ` (최근 ${crawlerState.days}일)`
                }
              </Typography>
            </Box>
          </Paper>
        </Grid>
        
        {/* 오른쪽 영역: 저장된 키워드 & 도움말 */}
        <Grid item xs={12} md={4}>
          <Box sx={{ mb: 3 }}>
            <SavedKeywords
              savedKeywords={crawlerState.savedKeywords}
              onLoadSavedKeyword={keywordManager.handleLoadSavedKeyword}
            />
          </Box>
          
          <CrawlerHelp />
        </Grid>
      </Grid>
      
      <LoadingOverlay
        open={crawlerState.loading}
        message="뉴스를 수집 중입니다. 키워드 수에 따라 최대 수 분이 소요될 수 있습니다..."
      />
    </Box>
  );
};

export default CrawlerPage;
