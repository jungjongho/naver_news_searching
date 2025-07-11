import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  TextField,
  Paper,
  Typography,
  Grid,
  Chip,
  Stack,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Divider,
  FormControlLabel,
  Radio,
  RadioGroup,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
// import DeleteIcon from '@mui/icons-material/Delete';
import KeyboardArrowRightIcon from '@mui/icons-material/KeyboardArrowRight';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import { CheckCircle } from '@mui/icons-material';

import PageTitle from '../components/common/PageTitle';
import AlertMessage from '../components/common/AlertMessage';
import LoadingOverlay from '../components/common/LoadingOverlay';
import crawlerService from '../api/crawlerService';
import { storage, removeDuplicates } from '../utils/helpers';

// 추천 키워드 카테고리
const KEYWORD_CATEGORIES = [
  {
    name: '화장품',
    keywords: ['코스맥스', '코스맥스엔비티', '콜마', 'HK이노엔', '아모레퍼시픽', 'LG생활건강', '올리브영', '화장품', '뷰티'],
  },
  {
    name: '건강기능식품',
    keywords: ['건강기능식품', '펫푸드', '마이크로바이옴', '식품의약품안전처'],
  },
];

const CrawlerPage = () => {
  const navigate = useNavigate();
  
  // 상태 관리
  const [keywords, setKeywords] = useState([]);
  const [newKeyword, setNewKeyword] = useState('');
  const [maxNewsPerKeyword, setMaxNewsPerKeyword] = useState(100);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [loading, setLoading] = useState(false);
  const [alert, setAlert] = useState({ open: false, type: 'info', message: '' });
  const [savedKeywords, setSavedKeywords] = useState([]);
  
  // 날짜 필터링 상태
  const [dateFilterType, setDateFilterType] = useState('days'); // 'days' 또는 'range'
  const [days, setDays] = useState(30);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // 저장된 키워드 로드
  useEffect(() => {
    const saved = storage.get('savedKeywords', []);
    setSavedKeywords(saved);
    
    // 마지막으로 사용한 키워드 로드
    const lastKeywords = storage.get('lastKeywords', []);
    if (lastKeywords.length > 0) {
      setKeywords(lastKeywords);
    }
    
    // 마지막으로 사용한 최대 뉴스 수 로드
    const lastMaxNews = storage.get('lastMaxNews', 100);
    setMaxNewsPerKeyword(lastMaxNews);
    
    // 마지막으로 사용한 날짜 설정 로드
    const lastDateFilterType = storage.get('lastDateFilterType', 'days');
    const lastDays = storage.get('lastDays', 30);
    const lastStartDate = storage.get('lastStartDate', '');
    const lastEndDate = storage.get('lastEndDate', '');
    
    setDateFilterType(lastDateFilterType);
    setDays(lastDays);
    setStartDate(lastStartDate);
    setEndDate(lastEndDate);
  }, []);

  // 키워드 추가
  const handleAddKeyword = () => {
    if (newKeyword.trim() === '') return;
    
    const updatedKeywords = [...keywords, newKeyword.trim()];
    setKeywords(removeDuplicates(updatedKeywords));
    setNewKeyword('');
  };

  // 키워드 삭제
  const handleDeleteKeyword = (index) => {
    const updatedKeywords = [...keywords];
    updatedKeywords.splice(index, 1);
    setKeywords(updatedKeywords);
  };

  // 카테고리 선택 시 키워드 추가
  const handleCategorySelect = (event) => {
    const category = event.target.value;
    setSelectedCategory(category);
    
    if (category) {
      const categoryItem = KEYWORD_CATEGORIES.find(item => item.name === category);
      if (categoryItem) {
        // 기존 키워드와 새 키워드 합치고 중복 제거
        const updatedKeywords = [...keywords, ...categoryItem.keywords];
        setKeywords(removeDuplicates(updatedKeywords));
      }
    }
  };

  // 키워드 저장
  const handleSaveKeywords = () => {
    if (keywords.length === 0) return;
    
    // 이미 저장된 키워드와 합치고 중복 제거
    const updatedSavedKeywords = removeDuplicates([...savedKeywords, ...keywords]);
    setSavedKeywords(updatedSavedKeywords);
    storage.set('savedKeywords', updatedSavedKeywords);
    
    setAlert({
      open: true,
      type: 'success',
      message: '키워드가 저장되었습니다.',
    });
    
    // 3초 후 알림 닫기
    setTimeout(() => {
      setAlert({ ...alert, open: false });
    }, 3000);
  };

  // 저장된 키워드 불러오기
  const handleLoadSavedKeyword = (keyword) => {
    if (!keywords.includes(keyword)) {
      const updatedKeywords = [...keywords, keyword];
      setKeywords(updatedKeywords);
    }
  };

  // 최대 뉴스 수 변경 핸들러
  const handleMaxNewsChange = (e) => {
    const value = e.target.value;
    
    // 빈 값일 때는 그대로 두기 (사용자가 입력 중일 수 있음)
    if (value === '') {
      setMaxNewsPerKeyword('');
      return;
    }
    
    const numValue = parseInt(value);
    
    // 유효한 숫자이고 1 이상 1000 이하일 때만 업데이트
    if (!isNaN(numValue) && numValue >= 1 && numValue <= 1000) {
      setMaxNewsPerKeyword(numValue);
    }
  };

  // blur 이벤트에서 최소값 보장
  const handleMaxNewsBlur = () => {
    if (maxNewsPerKeyword === '' || maxNewsPerKeyword < 1) {
      setMaxNewsPerKeyword(1);
    }
  };

  // 뉴스 크롤링 실행
  const handleCrawl = async () => {
    if (keywords.length === 0) {
      setAlert({
        open: true,
        type: 'error',
        message: '최소 1개 이상의 키워드를 입력해주세요.',
      });
      return;
    }
    
    // 날짜 범위 검증
    if (dateFilterType === 'range') {
      if (!startDate || !endDate) {
        setAlert({
          open: true,
          type: 'error',
          message: '날짜 범위를 선택할 때는 시작 날짜와 종료 날짜를 모두 입력해주세요.',
        });
        return;
      }
      
      if (new Date(startDate) > new Date(endDate)) {
        setAlert({
          open: true,
          type: 'error',
          message: '시작 날짜는 종료 날짜보다 이전이어야 합니다.',
        });
        return;
      }
    }
    
    // 최대 뉴스 수가 유효하지 않으면 기본값으로 설정
    const finalMaxNews = maxNewsPerKeyword === '' || maxNewsPerKeyword < 1 ? 100 : maxNewsPerKeyword;
    
    // 설정 저장
    storage.set('lastKeywords', keywords);
    storage.set('lastMaxNews', finalMaxNews);
    storage.set('lastDateFilterType', dateFilterType);
    storage.set('lastDays', days);
    storage.set('lastStartDate', startDate);
    storage.set('lastEndDate', endDate);
    
    setLoading(true);
    
    try {
      let result;
      if (dateFilterType === 'range') {
        result = await crawlerService.crawlNews(
          keywords, 
          finalMaxNews, 
          'date', 
          30, // days는 사용되지 않지만 기본값 전달
          startDate, 
          endDate
        );
      } else {
        result = await crawlerService.crawlNews(
          keywords, 
          finalMaxNews, 
          'date', 
          days
        );
      }
      
      if (result.success) {
        // 다운로드 폴더 저장 여부에 따라 메시지 다르게 표시
        let successMessage = `${result.item_count}개의 뉴스 기사를 성공적으로 수집했습니다.`;
        if (result.download_path) {
          successMessage += ` 결과 파일이 다운로드 폴더에 자동으로 저장되었습니다.`;
        }
        
        setAlert({
          open: true,
          type: 'success',
          message: successMessage,
        });
        
        // 결과 페이지로 이동 (0.5초 후)
        setTimeout(() => {
          navigate('/relevance', { 
            state: { 
              crawlResult: result,
              fromCrawler: true
            }
          });
        }, 500);
      } else {
        setAlert({
          open: true,
          type: 'error',
          message: `뉴스 수집에 실패했습니다: ${result.message}`,
        });
      }
    } catch (error) {
      console.error('뉴스 크롤링 오류:', error);
      setAlert({
        open: true,
        type: 'error',
        message: `오류가 발생했습니다: ${error.message}`,
      });
    } finally {
      setLoading(false);
    }
  };

  // 표시할 최대 뉴스 수 계산 (빈 값이거나 잘못된 값일 때 기본값 사용)
  const displayMaxNews = maxNewsPerKeyword === '' || maxNewsPerKeyword < 1 ? 100 : maxNewsPerKeyword;

  return (
    <Box>
      <PageTitle 
        title="뉴스 수집" 
        subtitle="네이버 뉴스에서 키워드 기반으로 최신 뉴스를 수집합니다."
        breadcrumbs={[{ text: '뉴스 수집', path: '/crawler' }]}
      />
      
      <AlertMessage
        open={alert.open}
        type={alert.type}
        message={alert.message}
        onClose={() => setAlert({ ...alert, open: false })}
      />
      
      <Grid container spacing={3}>
        {/* 왼쪽 영역: 키워드 입력 */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              검색 키워드
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <TextField
                fullWidth
                label="키워드 입력"
                variant="outlined"
                value={newKeyword}
                onChange={(e) => setNewKeyword(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleAddKeyword();
                  }
                }}
                InputProps={{
                  endAdornment: (
                    <Button
                      variant="contained"
                      color="primary"
                      onClick={handleAddKeyword}
                      startIcon={<AddIcon />}
                      disabled={newKeyword.trim() === ''}
                    >
                      추가
                    </Button>
                  ),
                }}
              />
            </Box>
            
            <Box sx={{ mb: 3 }}>
              <FormControl fullWidth variant="outlined">
                <InputLabel>추천 키워드 카테고리</InputLabel>
                <Select
                  value={selectedCategory}
                  onChange={handleCategorySelect}
                  label="추천 키워드 카테고리"
                >
                  <MenuItem value="">
                    <em>카테고리 선택</em>
                  </MenuItem>
                  {KEYWORD_CATEGORIES.map((category) => (
                    <MenuItem key={category.name} value={category.name}>
                      {category.name} ({category.keywords.length}개)
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
            
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle1" gutterBottom>
                선택된 키워드 ({keywords.length}개)
              </Typography>
              {keywords.length > 0 ? (
                <Stack direction="row" spacing={1} flexWrap="wrap">
                  {keywords.map((keyword, index) => (
                    <Chip
                      key={index}
                      label={keyword}
                      onDelete={() => handleDeleteKeyword(index)}
                      color="primary"
                      variant="outlined"
                      sx={{ mb: 1 }}
                    />
                  ))}
                </Stack>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  아직 선택된 키워드가 없습니다. 키워드를 입력하거나 추천 카테고리를 선택해주세요.
                </Typography>
              )}
            </Box>
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Button
                variant="outlined"
                color="primary"
                onClick={handleSaveKeywords}
                disabled={keywords.length === 0}
              >
                키워드 저장
              </Button>
              
              <Button
                variant="contained"
                color="primary"
                onClick={() => setKeywords([])}
                disabled={keywords.length === 0}
              >
                모두 지우기
              </Button>
            </Box>
          </Paper>
          
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              크롤링 설정
            </Typography>
            
            <Box sx={{ mb: 4 }}>
              <Typography variant="subtitle1" gutterBottom>
                키워드당 최대 뉴스 수
              </Typography>
              <TextField
                fullWidth
                variant="outlined"
                type="number"
                value={maxNewsPerKeyword}
                onChange={handleMaxNewsChange}
                onBlur={handleMaxNewsBlur}
                inputProps={{
                  min: 1,
                  max: 1000,
                  step: 1
                }}
                helperText="1부터 1000까지 입력 가능합니다. (네이버 API 제한)"
                sx={{ mb: 2 }}
              />
              <Typography variant="body2" color="text.secondary">
                권장값: 100-300개 (너무 많으면 처리 시간이 오래 걸릴 수 있습니다)
              </Typography>
            </Box>
            
            <Divider sx={{ mb: 3 }} />
            
            <Box sx={{ mb: 4 }}>
              <Typography variant="subtitle1" gutterBottom>
                날짜 필터링
              </Typography>
              
              <FormControl component="fieldset" sx={{ mb: 3 }}>
                <RadioGroup
                  value={dateFilterType}
                  onChange={(e) => setDateFilterType(e.target.value)}
                  row
                >
                  <FormControlLabel 
                    value="days" 
                    control={<Radio />} 
                    label="최근 일수 지정" 
                  />
                  <FormControlLabel 
                    value="range" 
                    control={<Radio />} 
                    label="날짜 범위 지정" 
                  />
                </RadioGroup>
              </FormControl>
              
              {dateFilterType === 'days' ? (
                <Box>
                  <TextField
                    fullWidth
                    variant="outlined"
                    type="number"
                    label="최근 며 일"
                    value={days}
                    onChange={(e) => setDays(parseInt(e.target.value) || 1)}
                    inputProps={{
                      min: 1,
                      max: 365,
                      step: 1
                    }}
                    helperText="1부터 365일까지 설정 가능합니다."
                    sx={{ mb: 2 }}
                  />
                  <Typography variant="body2" color="text.secondary">
                    최근 {days}일 내의 뉴스를 검색합니다.
                  </Typography>
                </Box>
              ) : (
                <Box>
                  <Grid container spacing={2} sx={{ mb: 2 }}>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        variant="outlined"
                        type="date"
                        label="시작 날짜"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        InputLabelProps={{
                          shrink: true,
                        }}
                        inputProps={{
                          max: new Date().toISOString().split('T')[0]
                        }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        variant="outlined"
                        type="date"
                        label="종료 날짜"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        InputLabelProps={{
                          shrink: true,
                        }}
                        inputProps={{
                          max: new Date().toISOString().split('T')[0],
                          min: startDate || undefined
                        }}
                      />
                    </Grid>
                  </Grid>
                  <Typography variant="body2" color="text.secondary">
                    {startDate && endDate ? 
                      `${startDate}부터 ${endDate}까지의 뉴스를 검색합니다.` :
                      '시작 날짜와 종료 날짜를 모두 선택해주세요.'
                    }
                  </Typography>
                </Box>
              )}
            </Box>
            
            <Divider sx={{ mb: 3 }} />
            
            <Box sx={{ textAlign: 'center' }}>
              <Button
                variant="contained"
                color="primary"
                size="large"
                onClick={handleCrawl}
                disabled={keywords.length === 0 || loading}
                sx={{ px: 4, py: 1 }}
              >
                뉴스 수집 시작
              </Button>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                총 {keywords.length}개 키워드, 최대 {keywords.length * displayMaxNews}개의 뉴스 기사를 수집합니다.
                {dateFilterType === 'range' && startDate && endDate && 
                  ` (${startDate} ~ ${endDate})`
                }
                {dateFilterType === 'days' && 
                  ` (최근 ${days}일)`
                }
              </Typography>
            </Box>
          </Paper>
        </Grid>
        
        {/* 오른쪽 영역: 저장된 키워드 & 도움말 */}
        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                저장된 키워드
              </Typography>
              
              {savedKeywords.length > 0 ? (
                <List dense>
                  {savedKeywords.map((keyword, index) => (
                    <ListItem
                      key={index}
                      secondaryAction={
                        <IconButton
                          edge="end"
                          onClick={() => handleLoadSavedKeyword(keyword)}
                          size="small"
                        >
                          <KeyboardArrowRightIcon />
                        </IconButton>
                      }
                    >
                      <ListItemText primary={keyword} />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  저장된 키워드가 없습니다. 자주 사용하는 키워드를 저장하면 빠르게 접근할 수 있습니다.
                </Typography>
              )}
            </CardContent>
          </Card>
          
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                도움말
              </Typography>
              
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <HelpOutlineIcon color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="여러 키워드 검색"
                    secondary="다양한 키워드를 동시에 검색할 수 있습니다. 각 키워드는 독립적으로 검색됩니다."
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <HelpOutlineIcon color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="최대 뉴스 수"
                    secondary="키워드당 최대 뉴스 수를 자유롭게 입력할 수 있습니다. 1부터 1000까지 가능합니다."
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <HelpOutlineIcon color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="추천 카테고리"
                    secondary="미리 정의된 추천 카테고리를 사용하여 빠르게 키워드를 추가할 수 있습니다."
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <HelpOutlineIcon color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="날짜 필터링"
                    secondary="최근 일수 또는 직접 날짜 범위를 지정하여 원하는 기간의 뉴스만 검색할 수 있습니다."
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CheckCircle color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="결과 저장"
                    secondary="크롤링 결과는 자동으로 저장되며, 다운로드 폴더에도 복사됩니다. '결과 목록' 페이지에서도 확인할 수 있습니다."
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      <LoadingOverlay
        open={loading}
        message="뉴스를 수집 중입니다. 키워드 수에 따라 최대 수 분이 소요될 수 있습니다..."
      />
    </Box>
  );
};

export default CrawlerPage;