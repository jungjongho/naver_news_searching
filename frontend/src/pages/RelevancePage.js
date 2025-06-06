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
import ProgressDialog from '../components/common/ProgressDialog';
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
  const [showProgress, setShowProgress] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [progressData, setProgressData] = useState({});
  const [progressInterval, setProgressInterval] = useState(null);
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

  // 진행 상황 폴링 시작
  const startProgressPolling = (sessionId) => {
    console.log('Starting progress polling for session:', sessionId);
    setCurrentSessionId(sessionId);
    setShowProgress(true);
    setProgressData({ current: 0, total: 0, stage: '분석 준비중', startTime: Date.now() });
    
    const interval = setInterval(async () => {
      try {
        console.log('Polling progress for session:', sessionId);
        const response = await relevanceService.getAnalysisProgress(sessionId);
        console.log('Progress response:', response);
        
        if (response.success) {
          const progress = response.progress;
          setProgressData(prev => ({
            ...progress,
            startTime: prev.startTime || Date.now()
          }));
          
          // 분석 완료 확인
          if (progress.stage === '분석 완료' || (progress.current >= progress.total && progress.total > 0)) {
            clearInterval(interval);
            setProgressInterval(null);
            
            // 잠시 후 다이얼로그 닫기
            setTimeout(() => {
              setShowProgress(false);
              setAlert({
                open: true,
                type: 'success',
                title: '관련성 평가 완료',
                message: `뉴스 기사의 관련성 평가가 완료되었습니다.`,
              });
              
              // 결과 페이지로 이동
              setTimeout(() => {
                navigate('/results', { 
                  state: { 
                    fromRelevance: true
                  }
                });
              }, 1000);
            }, 1500);
          }
        } else {
          console.error('Progress polling failed:', response);
        }
      } catch (error) {
        console.error('진행 상황 확인 중 오류:', error);
      }
    }, 800); // 0.8초마다 확인 (더 빠르게)
    
    setProgressInterval(interval);
  };
  
  // 진행 상황 폴링 중지
  const stopProgressPolling = () => {
    if (progressInterval) {
      clearInterval(progressInterval);
      setProgressInterval(null);
    }
    setShowProgress(false);
    setCurrentSessionId(null);
    setProgressData({});
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
        // 동기 방식 - 진행 상황 추적
        setLoading(false); // 로딩 오버레이 대신 진행 다이얼로그 사용
        
        // 고정된 세션 ID 사용 (백엔드와 동일)
        const sessionId = "current_analysis";
        console.log('Generated session ID:', sessionId);
        console.log('Selected file:', selectedFile);
        
        try {
          // 1. 먼저 진행 상황 초기화
          console.log('초기화 중...');
          const initResult = await relevanceService.initializeProgress(requestData);
          
          if (!initResult.success) {
            throw new Error(initResult.message);
          }
          
          console.log('Progress initialized:', initResult);
          
          // 2. 진행 상황 추적 시작
          startProgressPolling(sessionId);
          
          // 3. 진행 상황이 업데이트된 후 동기 API 호출
          setTimeout(async () => {
            try {
              console.log('분석 시작...');
              result = await relevanceService.evaluateNewsSync(requestData);
              
              // 진행 상황 폴링 중지
              stopProgressPolling();
              
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
            } catch (error) {
              stopProgressPolling();
              throw error;
            }
          }, 1000); // 1초 후 API 호출 시작 (진행 상황이 표시될 시간 확보)
        } catch (error) {
          stopProgressPolling();
          console.error('관련성 평가 중 오류:', error);
          setAlert({
            open: true,
            type: 'error',
            message: `오류가 발생했습니다: ${error.message}`,
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
  
  // 상태 폴링 시작 (비동기 방식용)
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
      if (progressInterval) {
        clearInterval(progressInterval);
      }
    };
  }, [pollingInterval, progressInterval]);

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

      {/* 진행 상황 다이얼로그 */}
      <ProgressDialog
        open={showProgress}
        title="관련성 평가 진행 중"
        progress={progressData}
        onClose={null} // 닫기 불가능
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
                  <MenuItem value="sync">동기 방식 (실시간 진행률 표시) - 추천</MenuItem>
                  <MenuItem value="async">비동기 방식 (백그라운드 처리)</MenuItem>
                </Select>
              </FormControl>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {analysisMode === 'sync' 
                  ? '분석 진행 상황을 실시간으로 확인하며 완료까지 기다립니다. 기사 수에 따라 수 분이 소요될 수 있습니다.'
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
                disabled={!selectedFile || !apiKey || loading || showProgress}
                startIcon={<AnalyticsIcon />}
                sx={{ px: 4, py: 1 }}
              >
                관련성 평가 시작
              </Button>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {analysisMode === 'sync' 
                  ? '선택한 파일의 모든 뉴스 기사를 평가하고 실시간으로 진행 상황을 확인합니다.'
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
                    secondary="기사를 '자사언급기사', '업계관련기사', '건기식펫푸드관련기사', '기타' 카테고리로 분류합니다."
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <InfoOutlinedIcon color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="실시간 진행률"
                    secondary="동기 방식 선택 시 각 기사의 분석 진행 상황과 통계를 실시간으로 확인할 수 있습니다."
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
                    secondary="GPT-4.1-Nano는 빠르고 저렴한 최신 모델입니다. GPT-4는 정확도가 높지만 비용이 더 비쌉니다."
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <HelpOutlineIcon color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="평가 시간"
                    secondary="뉴스 기사 수에 따라 평가 시간이 달라집니다. 100개 기사 기준 약 3-5분이 소요됩니다."
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <HelpOutlineIcon color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="진행률 표시"
                    secondary="동기 방식 선택 시 각 기사의 처리 상황, 카테고리 분류 결과, 예상 남은 시간 등을 실시간으로 확인할 수 있습니다."
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      <LoadingOverlay
        open={loading && !showProgress}
        message="분석을 준비하고 있습니다..."
      />
    </Box>
  );
};

export default RelevancePage;