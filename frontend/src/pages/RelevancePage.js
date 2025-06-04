import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  TextField,
  Paper,
  Typography,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Card,
  CardContent,
  Divider,
  IconButton,
  Tooltip,
} from '@mui/material';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import LockIcon from '@mui/icons-material/Lock';

import PageTitle from '../components/common/PageTitle';
import AlertMessage from '../components/common/AlertMessage';
import LoadingOverlay from '../components/common/LoadingOverlay';
import relevanceService from '../api/relevanceService';
import crawlerService from '../api/crawlerService';
import promptService from '../api/promptService';
import { storage } from '../utils/helpers';

// AI 모델 옵션
const AI_MODELS = [
  { value: 'gpt-4.1-nano', label: 'GPT-4.1 Nano (추천)', description: 'OpenAI 최신 고속 저비용 모델 (2025년 4월 출시)' },
  { value: 'gpt-4.1-mini', label: 'GPT-4.1 Mini', description: '뛰어난 성능과 낮은 비용을 제공하는 경량화 모델' },
  { value: 'gpt-4.1', label: 'GPT-4.1', description: '코딩과 지시 이행에 특화된 최신 대화형 모델' },
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini', description: '기존 경량화 모델, 빠른 속도와 저렴한 비용' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo', description: '빠르고 비용 효율적인 모델' },
  { value: 'gpt-4', label: 'GPT-4', description: '더 높은 정확도를 제공하지만 비용이 더 높음' },
  { value: 'claude-instant-1', label: 'Claude Instant', description: 'Anthropic Claude 빠른 모델' },
  { value: 'claude-2', label: 'Claude 2', description: 'Anthropic Claude 고성능 모델' },
];

const RelevancePage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  
  // 상태 관리
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('gpt-4.1-nano');
  const [prompts, setPrompts] = useState([]);
  const [selectedPrompt, setSelectedPrompt] = useState('');
  const [analysisMode, setAnalysisMode] = useState('sync'); // 'sync', 'async'
  const [loading, setLoading] = useState(false);
  const [alert, setAlert] = useState({ open: false, type: 'info', message: '', title: '' });
  const [apiKeyMasked, setApiKeyMasked] = useState(true);
  const [pollingInterval, setPollingInterval] = useState(null);
  
  // 프롬프트 목록 로드
  const loadPrompts = async () => {
    try {
      const response = await promptService.getAllPrompts();
      setPrompts(response.prompts || []);
      
      // 활성 프롬프트 자동 선택
      const activePrompt = response.prompts?.find(p => p.is_active);
      if (activePrompt) {
        setSelectedPrompt(activePrompt.id);
      }
    } catch (error) {
      console.error('프롬프트 목록 로드 중 오류:', error);
    }
  };
  
  // 컴포넌트 마운트 시 초기 데이터 로드
  useEffect(() => {
    loadFiles();
    loadPrompts();
  }, []);
  
  // 크롤러 페이지에서 전달된 데이터 처리
  useEffect(() => {
    if (location.state?.crawlResult && location.state?.fromCrawler) {
      const crawlResult = location.state.crawlResult;
      setSelectedFile(crawlResult.file_path);
      
      // 자동으로 떠있는 알림 표시
      setAlert({
        open: true,
        type: 'success',
        title: '뉴스 수집 완료',
        message: `${crawlResult.item_count}개의 뉴스 기사가 성공적으로 수집되었습니다. 이제 관련성을 평가할 수 있습니다.`,
      });
    }
    
    // API 키 설정 로드
    const savedApiKey = storage.get('openai_api_key', '');
    if (savedApiKey) {
      setApiKey(savedApiKey);
    }
    
    const savedModel = storage.get('ai_model', 'gpt-4.1-nano');
    if (savedModel) {
      setModel(savedModel);
    }
  }, [location.state]);
  
  // 파일 목록 로드
  const loadFiles = async () => {
    try {
      const fileList = await crawlerService.getFiles();
      // 평가되지 않은 파일만 필터링
      const unevaluatedFiles = fileList.filter(file => !file.has_evaluation && !file.is_evaluated);
      setFiles(unevaluatedFiles);
    } catch (error) {
      console.error('파일 목록 로드 중 오류:', error);
      setAlert({
        open: true,
        type: 'error',
        message: '파일 목록을 불러오는 중 오류가 발생했습니다.',
      });
    }
  };
  
  // API 키 저장
  const handleSaveApiKey = () => {
    if (apiKey.trim()) {
      storage.set('openai_api_key', apiKey);
      setAlert({
        open: true,
        type: 'success',
        message: 'API 키가 저장되었습니다.',
      });
      
      // 3초 후 알림 닫기
      setTimeout(() => {
        setAlert({ ...alert, open: false });
      }, 3000);
    }
  };
  
  // API 키 마스킹 토글
  const toggleApiKeyMask = () => {
    setApiKeyMasked(!apiKeyMasked);
  };
  
  // 모델 변경 및 저장
  const handleModelChange = (event) => {
    const selectedModel = event.target.value;
    setModel(selectedModel);
    storage.set('ai_model', selectedModel);
  };
  
  // 관련성 평가 실행
  const handleEvaluate = async () => {
    if (!selectedFile) {
      setAlert({
        open: true,
        type: 'error',
        message: '평가할 파일을 선택해주세요.',
      });
      return;
    }
    
    if (!apiKey) {
      setAlert({
        open: true,
        type: 'error',
        message: 'API 키를 입력해주세요.',
      });
      return;
    }
    
    setLoading(true);
    
    try {
      // 프롬프트 ID 포함한 요청 데이터
      const requestData = {
        file_path: selectedFile,
        api_key: apiKey,
        model: model,
        prompt_id: selectedPrompt || null
      };
      
      let result;
      
      if (analysisMode === 'sync') {
        // 동기 방식 - 즉시 결과 반환
        result = await relevanceService.evaluateNewsSync(requestData);
        
        if (result.success) {
          setAlert({
            open: true,
            type: 'success',
            title: '관련성 평가 완료',
            message: `뉴스 기사의 관련성 평가가 완료되었습니다. 관련 뉴스: ${result.stats.relevant_items}/${result.stats.total_items} (${result.stats.relevant_percent}%)`,
          });
          
          // 결과 페이지로 이동 (1초 후)
          setTimeout(() => {
            navigate('/results', { 
              state: { 
                evaluationResult: result,
                fromRelevance: true
              }
            });
          }, 1000);
        } else {
          setAlert({
            open: true,
            type: 'error',
            message: `관련성 평가에 실패했습니다: ${result.message}`,
          });
        }
      } else {
        // 비동기 방식 - 백그라운드 처리
        result = await relevanceService.evaluateNews(requestData);
        
        if (result.success) {
          setAlert({
            open: true,
            type: 'info',
            title: '관련성 평가 시작',
            message: `${result.stats?.total_items || '선택된'}개 뉴스 항목의 관련성 평가를 시작했습니다. 분석은 백그라운드에서 진행되며, 완료되면 자동으로 결과 페이지로 이동합니다.`,
          });
          
          // 상태 폴링 시작
          startPolling(selectedFile);
        } else {
          setAlert({
            open: true,
            type: 'error',
            message: `관련성 평가 시작에 실패했습니다: ${result.message}`,
          });
        }
      }
    } catch (error) {
      console.error('관련성 평가 중 오류:', error);
      setAlert({
        open: true,
        type: 'error',
        message: `오류가 발생했습니다: ${error.message}`,
      });
    } finally {
      setLoading(false);
    }
  };
  
  // 상태 폴링 시작
  const startPolling = (fileName) => {
    const interval = setInterval(async () => {
      try {
        const statusResult = await relevanceService.checkAnalysisStatus(fileName);
        
        if (statusResult.status === 'completed') {
          clearInterval(interval);
          setPollingInterval(null);
          
          setAlert({
            open: true,
            type: 'success',
            title: '관련성 평가 완료',
            message: '뉴스 기사의 관련성 평가가 완료되었습니다.',
          });
          
          // 결과 페이지로 이동
          setTimeout(() => {
            navigate('/results', { 
              state: { 
                evaluationResult: {
                  success: true,
                  file_path: statusResult.file.file_name,
                  message: '분석 완료'
                },
                fromRelevance: true
              }
            });
          }, 1000);
        } else if (statusResult.status === 'error') {
          clearInterval(interval);
          setPollingInterval(null);
          
          setAlert({
            open: true,
            type: 'error',
            message: `분석 중 오류가 발생했습니다: ${statusResult.message}`,
          });
        }
      } catch (error) {
        console.error('상태 확인 중 오류:', error);
      }
    }, 5000); // 5초마다 확인
    
    setPollingInterval(interval);
  };
  
  // 컴포넌트 언마운트 시 폴링 정리
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);

  return (
    <Box>
      <PageTitle 
        title="관련성 평가" 
        subtitle="수집된 뉴스 기사의 화장품 업계 관련성을 평가합니다."
        breadcrumbs={[{ text: '관련성 평가', path: '/relevance' }]}
      />
      
      <AlertMessage
        open={alert.open}
        type={alert.type}
        title={alert.title}
        message={alert.message}
        onClose={() => setAlert({ ...alert, open: false })}
      />
      
      <Grid container spacing={3}>
        {/* 왼쪽 영역: 파일 선택 및 평가 설정 */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              평가할 파일 선택
            </Typography>
            
            <Box sx={{ mb: 3 }}>
              <FormControl fullWidth variant="outlined">
                <InputLabel>프롬프트 템플릿</InputLabel>
                <Select
                  value={selectedPrompt}
                  onChange={(e) => setSelectedPrompt(e.target.value)}
                  label="프롬프트 템플릿"
                >
                  <MenuItem value="">
                    <em>기본 프롬프트 사용</em>
                  </MenuItem>
                  {prompts.map((prompt) => (
                    <MenuItem key={prompt.id} value={prompt.id}>
                      {prompt.name} {prompt.is_active && '(활성)'}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {selectedPrompt ? (
                  <>선택한 프롬프트: {prompts.find(p => p.id === selectedPrompt)?.description || '커스텀 프롬프트'}</>
                ) : (
                  '기본 프롬프트를 사용합니다. 프롬프트 관리 페이지에서 커스텀 프롬프트를 생성할 수 있습니다.'
                )}
              </Typography>
              
              <Button
                variant="text"
                color="primary"
                onClick={() => navigate('/prompts')}
                sx={{ mt: 1 }}
              >
                프롬프트 관리 페이지로 이동
              </Button>
            </Box>
            
            <Box sx={{ mb: 3 }}>
              <FormControl fullWidth variant="outlined">
                <InputLabel>파일 선택</InputLabel>
                <Select
                  value={selectedFile}
                  onChange={(e) => setSelectedFile(e.target.value)}
                  label="파일 선택"
                >
                  <MenuItem value="">
                    <em>파일을 선택해주세요</em>
                  </MenuItem>
                  {files.map((file) => (
                    <MenuItem key={file.file_name} value={file.file_name}>
                      {file.file_name} ({file.file_size_str})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              {files.length === 0 && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  평가할 파일이 없습니다. 먼저 '뉴스 수집' 페이지에서 뉴스를 수집해주세요.
                </Typography>
              )}
            </Box>
            
            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="outlined"
                color="primary"
                onClick={loadFiles}
                startIcon={<UploadFileIcon />}
              >
                파일 새로고침
              </Button>
            </Box>
          </Paper>
          
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              API 설정
            </Typography>
            
            <Box sx={{ mb: 3 }}>
              <TextField
                fullWidth
                label="API 키 (OpenAI 또는 Claude)"
                variant="outlined"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                type={apiKeyMasked ? 'password' : 'text'}
                InputProps={{
                  endAdornment: (
                    <Tooltip title={apiKeyMasked ? "API 키 보기" : "API 키 숨기기"}>
                      <IconButton onClick={toggleApiKeyMask}>
                        <LockIcon />
                      </IconButton>
                    </Tooltip>
                  ),
                }}
              />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                선택한 모델에 따라 OpenAI 또는 Anthropic API 키가 필요합니다. API 키는 브라우저에 로컬로 저장되며, 서버로 전송되지 않습니다.
              </Typography>
              
              <Button
                variant="outlined"
                color="primary"
                onClick={handleSaveApiKey}
                disabled={!apiKey.trim()}
                sx={{ mt: 1 }}
              >
                API 키 저장
              </Button>
            </Box>
            
            <Box sx={{ mb: 3 }}>
              <FormControl fullWidth variant="outlined">
                <InputLabel>AI 모델</InputLabel>
                <Select
                  value={model}
                  onChange={handleModelChange}
                  label="AI 모델"
                >
                  {AI_MODELS.map((modelOption) => (
                    <MenuItem key={modelOption.value} value={modelOption.value}>
                      {modelOption.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                선택한 모델: {AI_MODELS.find(m => m.value === model)?.description || ''}
              </Typography>
            </Box>
            
            <Box sx={{ mb: 3 }}>
              <FormControl fullWidth variant="outlined">
                <InputLabel>분석 방식</InputLabel>
                <Select
                  value={analysisMode}
                  onChange={(e) => setAnalysisMode(e.target.value)}
                  label="분석 방식"
                >
                  <MenuItem value="sync">동기 방식 (즉시 결과 확인) - 추천</MenuItem>
                  <MenuItem value="async">비동기 방식 (백그라운드 처리)</MenuItem>
                </Select>
              </FormControl>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {analysisMode === 'sync' 
                  ? '분석 완료까지 기다린 후 즉시 결과를 확인할 수 있습니다. 기사 수가 많으면 시간이 오래 걸릴 수 있습니다.'
                  : '분석을 백그라운드에서 진행하며, 완료되면 자동으로 결과 페이지로 이동합니다.'
                }
              </Typography>
            </Box>
            
            <Divider sx={{ mb: 3 }} />
            
            <Box sx={{ textAlign: 'center' }}>
              <Button
                variant="contained"
                color="primary"
                size="large"
                onClick={handleEvaluate}
                disabled={!selectedFile || !apiKey || loading}
                startIcon={<AnalyticsIcon />}
                sx={{ px: 4, py: 1 }}
              >
                관련성 평가 시작
              </Button>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {analysisMode === 'sync' 
                  ? '선택한 파일의 모든 뉴스 기사를 평가하고 완료까지 기다립니다. 기사 수에 따라 수 분이 소요될 수 있습니다.'
                  : '선택한 파일의 모든 뉴스 기사를 백그라운드에서 평가합니다. 완료되면 자동으로 알림을 받습니다.'
                }
              </Typography>
            </Box>
          </Paper>
        </Grid>
        
        {/* 오른쪽 영역: 도움말 */}
        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                관련성 평가 정보
              </Typography>
              
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <InfoOutlinedIcon color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="LLM 기반 평가"
                    secondary="OpenAI나 Claude API를 사용하여 뉴스 기사의 화장품 업계 관련성을 자동으로 평가합니다."
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <InfoOutlinedIcon color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="카테고리 분류"
                    secondary="기사를 '자사 언급기사', '업계 관련기사', '건강기능식품·펫푸드', '기타' 카테고리로 분류합니다."
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <InfoOutlinedIcon color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="평가 기준"
                    secondary="기사의 내용, 키워드, 제목 등을 종합적으로 분석하여 화장품 업계와의 관련성을 판단합니다."
                  />
                </ListItem>
              </List>
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
                    primary="API 키"
                    secondary="OpenAI나 Anthropic API 키가 필요합니다. 선택한 모델에 해당하는 API 키를 입력해주세요."
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <HelpOutlineIcon color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="모델 선택"
                    secondary="GPT-3.5-turbo는 빠르고 저렴한 모델입니다. GPT-4는 정확도가 높지만 비용이 더 비쌉니다."
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <HelpOutlineIcon color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="평가 시간"
                    secondary="뉴스 기사 수에 따라 평가 시간이 달라집니다. 100개 기사 기준 약 5-10분이 소요됩니다."
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <HelpOutlineIcon color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="분석 방식"
                    secondary="동기 방식은 결과를 즉시 확인하고, 비동기 방식은 백그라운드에서 처리하여 다른 작업을 계속할 수 있습니다."
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      <LoadingOverlay
        open={loading}
        message={`뉴스 기사의 관련성을 평가 중입니다. ${analysisMode === 'sync' ? '기사 수에 따라 최대 수 분이 소요될 수 있습니다...' : '백그라운드에서 처리 중이며, 완료되면 자동으로 알림을 받습니다...'}`}
      />
    </Box>
  );
};

export default RelevancePage;
