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
  FormControlLabel,
  Switch,
  Slider,
} from '@mui/material';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import LockIcon from '@mui/icons-material/Lock';

import PageTitle from '../components/common/PageTitle';
import AlertMessage from '../components/common/AlertMessage';
import LoadingOverlay from '../components/common/LoadingOverlay';
import ProgressDialog from '../components/common/ProgressDialog';
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
  const [loading, setLoading] = useState(false);
  const [showProgress, setShowProgress] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [alert, setAlert] = useState({ open: false, type: 'info', message: '', title: '' });
  const [apiKeyMasked, setApiKeyMasked] = useState(true);
  
  // 배치 처리 옵션
  const [useBatchProcessing, setUseBatchProcessing] = useState(true);
  const [batchSize, setBatchSize] = useState(10);
  
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
  
  // WebSocket 완료 메시지 처리
  useEffect(() => {
    const handleAnalysisComplete = (stats, autoNavigate = false) => {
      console.log('🎉 WebSocket을 통해 분석 완료 수신:', stats);
      
      setAlert({
        open: true,
        type: 'success',
        title: '관련성 평가 완료',
        message: `뉴스 기사의 관련성 평가가 완룈되었습니다. 관련 뉴스: ${stats.relevant_items}/${stats.total_items} (${stats.relevant_percent}%) - "확인" 버튼을 눌러 결과를 확인하세요.`,
      });
      
      // 자동 이동 제거 - 사용자가 ProgressDialog에서 "확인" 버튼을 누를 때만 이동
      window.analysisResult = {
        success: true,
        stats: stats,
        message: '분석 완료'
      };
    };
    
    // 결과 페이지 이동 함수
    const navigateToResults = (result) => {
      console.log('📊 결과 페이지로 이동:', result);
      navigate('/results', {
        state: {
          evaluationResult: result,
          fromRelevance: true
        }
      });
    };
    
    // 전역 함수로 등록
    window.showSuccessAlert = handleAnalysisComplete;
    window.navigateToResults = navigateToResults;
    
    // 컴포넌트 언마운트 시 정리
    return () => {
      delete window.showSuccessAlert;
      delete window.analysisResult;
      delete window.navigateToResults;
    };
  }, [navigate]);
  
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
  const loadFiles = async (showRefreshMessage = false) => {
    try {
      // 파일 목록 새로고침 요청 (캐시 무효화)
      if (showRefreshMessage) {
        await crawlerService.refreshFiles();
      }
      
      const fileList = await crawlerService.getFiles();
      console.log('📂 전체 파일 목록:', fileList);
      
      // 크롤링 디렉토리에서 온 파일만 필터링 (더 정확한 필터링)
      const crawlingFiles = fileList.filter(file => 
        file.directory_type === 'crawling' || 
        (file.file_type === 'crawling' && !file.has_evaluation)
      );
      
      console.log('📁 크롤링 파일 목록:', crawlingFiles);
      setFiles(crawlingFiles);
      
      if (showRefreshMessage) {
        setAlert({
          open: true,
          type: 'success',
          message: `파일 목록이 새로고침되었습니다. ${crawlingFiles.length}개의 파일을 찾았습니다.`,
        });
      }
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
    
    if (!selectedPrompt) {
      setAlert({
        open: true,
        type: 'error',
        title: '프롬프트 템플릿 필수',
        message: '관련성 평가를 위해서는 프롬프트 템플릿이 반드시 필요합니다. 프롬프트 관리 페이지에서 프롬프트를 선택하거나 새로 생성해주세요.',
      });
      return;
    }
    
    try {
      console.log('🚀 관련성 평가 시작...');
      
      // 1. 로딩 상태부터 설정
      setLoading(true);
      
      // 2. session_id 생성
      const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      console.log('📋 생성된 Session ID:', newSessionId);
      
      // 3. 상태를 한번에 동기적으로 업데이트
      setSessionId(newSessionId);
      setShowProgress(true);
      
      console.log('📊 상태 업데이트 완료:', { 
        sessionId: newSessionId, 
        showProgress: true, 
        loading: true 
      });
      
      // 4. 약간의 지연으로 React 상태가 완전히 업데이트되도록 보장
      await new Promise(resolve => setTimeout(resolve, 1000)); // 1초로 증가
      
      // 5. 프롬프트 ID 포함한 요청 데이터
      const requestData = {
        file_path: selectedFile,
        api_key: apiKey,
        model: model,
        prompt_id: selectedPrompt || null,
        session_id: newSessionId,  // 프론트엔드에서 생성한 session_id 전달
        use_batch_processing: useBatchProcessing,
        batch_size: useBatchProcessing ? batchSize : 1
      };
      
      console.log('📤 API 요청 시작:', requestData);
      
      // 6. API 요청을 비동기로 시작 (결과를 기다리지 않음)
      relevanceService.evaluateNews(requestData)
        .then(result => {
          console.log('📊 API 응답 수신:', result);
          
          if (result.success) {
            // WebSocket을 통해 완료 메시지가 올 때까지 기다림
            console.log('✅ API 요청 성공 - WebSocket 완료 메시지 대기 중...');
          } else {
            setAlert({
              open: true,
              type: 'error',
              message: `관련성 평가에 실패했습니다: ${result.message}`,
            });
            setLoading(false);
            setShowProgress(false);
            setSessionId(null);
          }
        })
        .catch(error => {
          console.error('❌ API 요청 오류:', error);
          setAlert({
            open: true,
            type: 'error',
            message: `오류가 발생했습니다: ${error.message}`,
          });
          setLoading(false);
          setShowProgress(false);
          setSessionId(null);
        });
      
      // 7. API 요청을 시작한 후 바로 리턴 (완료를 기다리지 않음)
      console.log('🔄 API 요청 시작됨 - WebSocket을 통한 진행도 업데이트 대기 중...');
      
    } catch (error) {
      console.error('❌ 관련성 평가 중 오류:', error);
      setAlert({
        open: true,
        type: 'error',
        message: `오류가 발생했습니다: ${error.message}`,
      });
      setLoading(false); // 오류 시에만 loading 해제
      setShowProgress(false);
      setSessionId(null);
    }
    // finally 블록 제거 - ProgressDialog에서 완료 시 loading 해제
  };

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
                <InputLabel>프롬프트 템플릿 (필수)</InputLabel>
                <Select
                  value={selectedPrompt}
                  onChange={(e) => setSelectedPrompt(e.target.value)}
                  label="프롬프트 템플릿 (필수)"
                  error={!selectedPrompt}
                >
                  <MenuItem value="">
                    <em>프롬프트 템플릿을 선택해주세요 (필수)</em>
                  </MenuItem>
                  {prompts.map((prompt) => (
                    <MenuItem key={prompt.id} value={prompt.id}>
                      {prompt.name} {prompt.is_active && '(활성)'}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <Typography variant="body2" color={selectedPrompt ? "text.secondary" : "error"} sx={{ mt: 1 }}>
                {selectedPrompt ? (
                  <>선택한 프롬프트: {prompts.find(p => p.id === selectedPrompt)?.description || '커스텀 프롬프트'}</>
                ) : (
                  <>⚠️ 프롬프트 템플릿이 반드시 필요합니다. 기본 프롬프트는 더 이상 지원되지 않습니다.</>
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
                onClick={() => loadFiles(true)}
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
            
            {/* 배치 처리 옵션 */}
            <Box sx={{ mb: 3, p: 2, border: '1px solid #e0e0e0', borderRadius: 1 }}>
              <Typography variant="h6" gutterBottom>
                배치 처리 설정
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={useBatchProcessing}
                    onChange={(e) => setUseBatchProcessing(e.target.checked)}
                    color="primary"
                  />
                }
                label="배치 처리 사용 (추청)"
              />
              
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                배치 처리는 여러 기사를 한번에 분석하여 속도를 향상시킵니다.
              </Typography>
              
              {useBatchProcessing && (
                <Box sx={{ mt: 2 }}>
                  <Typography gutterBottom>
                    배치 크기: {batchSize}개
                  </Typography>
                  <Slider
                    value={batchSize}
                    onChange={(e, value) => setBatchSize(value)}
                    min={1}
                    max={20}
                    step={1}
                    marks={[
                      { value: 1, label: '1' },
                      { value: 5, label: '5' },
                      { value: 10, label: '10' },
                      { value: 15, label: '15' },
                      { value: 20, label: '20' }
                    ]}
                    valueLabelDisplay="auto"
                  />
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    배치 크기가 클수록 빠르지만 API 비용이 많이 들 수 있습니다. 권장: 10개
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
                onClick={handleEvaluate}
                disabled={!selectedFile || !apiKey || !selectedPrompt || loading}
                startIcon={<AnalyticsIcon />}
                sx={{ px: 4, py: 1 }}
              >
                관련성 평가 시작
              </Button>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                선택한 파일의 모든 뉴스 기사를 평가합니다. 기사 수에 따라 수 분이 소요될 수 있습니다.
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
                    primary="프롬프트 템플릿 필수"
                    secondary="관련성 평가를 위해 프롬프트 템플릿을 반드시 선택해야 합니다. 기본 프롬프트는 더 이상 지원되지 않습니다."
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
                    primary="배치 처리 지원"
                    secondary="여러 기사를 한번에 분석하여 속도를 향상시킵니다. 기본 10개씩 배치 처리됩니다."
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <InfoOutlinedIcon color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="분석 진행"
                    secondary="선택한 파일의 모든 기사를 순차적으로 분석하며, 완료 후 결과를 확인할 수 있습니다."
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
                    primary="배치 처리"
                    secondary="배치 처리는 여러 기사를 한번에 분석하여 속도를 3-5배 향상시킵니다. 배치 크기가 클수록 빠르지만 API 비용이 더 들 수 있습니다."
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <HelpOutlineIcon color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="백엔드 진행률 로그"
                    secondary="서버 콘솔에서 각 기사의 분석 진행 상황과 통계를 확인할 수 있습니다."
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
      
      {showProgress && sessionId && (
        <ProgressDialog
          open={showProgress}
          onClose={() => {
            setShowProgress(false);
            setSessionId(null);
            setLoading(false); // ProgressDialog 닫힐 때 loading 해제
          }}
          sessionId={sessionId}
        />
      )}
    </Box>
  );
};

export default RelevancePage;