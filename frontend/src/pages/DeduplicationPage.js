import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
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
  Slider,
  FormControlLabel,
  Switch,
  Tooltip,
  IconButton,
  TextField,
} from '@mui/material';
import DeDupeIcon from '@mui/icons-material/FilterList';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import SettingsIcon from '@mui/icons-material/Settings';

import PageTitle from '../components/common/PageTitle';
import AlertMessage from '../components/common/AlertMessage';
import LoadingOverlay from '../components/common/LoadingOverlay';
import ProgressDialog from '../components/common/ProgressDialog';
import deduplicationService from '../api/deduplicationService';
import crawlerService from '../api/crawlerService';

const DeduplicationPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  
  // 상태 관리
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [similarityThreshold, setSimilarityThreshold] = useState(0.85);
  const [batchSize, setBatchSize] = useState(50);
  const [loading, setLoading] = useState(false);
  const [showProgress, setShowProgress] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [alert, setAlert] = useState({ open: false, type: 'info', message: '', title: '' });
  const [advancedSettings, setAdvancedSettings] = useState(false);
  
  // 컴포넌트 마운트 시 초기 데이터 로드
  useEffect(() => {
    loadFiles();
  }, []);
  
  // WebSocket 완료 메시지 처리
  useEffect(() => {
    const handleDeduplicationComplete = (stats, autoNavigate = false) => {
      console.log('🎉 WebSocket을 통해 중복 제거 완료 수신:', stats);
      
      setAlert({
        open: true,
        type: 'success',
        title: '중복 제거 완료',
        message: `중복 제거가 완료되었습니다. 원본 ${stats.original_count}개 → 최종 ${stats.deduplicated_count}개 (${stats.removed_count}개 제거, ${stats.reduction_percentage}% 감소) - "확인" 버튼을 눌러 결과를 확인하세요.`,
      });
      
      // 결과를 전역에 저장
      window.deduplicationResult = {
        success: true,
        stats: stats,
        message: '중복 제거 완료'
      };
    };
    
    // 결과 페이지 이동 함수
    const navigateToRelevance = (result) => {
      console.log('📊 관련성 평가 페이지로 이동:', result);
      navigate('/relevance', {
        state: {
          deduplicationResult: result,
          fromDeduplication: true
        }
      });
    };
    
    // 전역 함수로 등록
    window.showDeduplicationSuccessAlert = handleDeduplicationComplete;
    window.navigateToRelevance = navigateToRelevance;
    
    // 컴포넌트 언마운트 시 정리
    return () => {
      delete window.showDeduplicationSuccessAlert;
      delete window.deduplicationResult;
      delete window.navigateToRelevance;
    };
  }, [navigate]);
  
  // 크롤러 페이지에서 전달된 데이터 처리
  useEffect(() => {
    if (location.state?.crawlResult && location.state?.fromCrawler) {
      const crawlResult = location.state.crawlResult;
      setSelectedFile(crawlResult.file_path);
      
      setAlert({
        open: true,
        type: 'success',
        title: '뉴스 수집 완료',
        message: `${crawlResult.item_count}개의 뉴스 기사가 성공적으로 수집되었습니다. 이제 중복을 제거할 수 있습니다.`,
      });
    }
  }, [location.state]);
  
  // 파일 목록 로드
  const loadFiles = async (showRefreshMessage = false) => {
    try {
      if (showRefreshMessage) {
        await crawlerService.refreshFiles();
      }
      
      const fileList = await crawlerService.getFiles();
      console.log('📂 전체 파일 목록:', fileList);
      
      // 크롤링 파일만 필터링 (중복 제거되지 않은 파일)
      const crawlingFiles = fileList.filter(file => 
        file.directory_type === 'crawling' || 
        (file.file_type === 'crawling' && !file.has_evaluation && !file.has_deduplication)
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

  // 중복 제거 실행
  const handleRemoveDuplicates = async () => {
    if (!selectedFile) {
      setAlert({
        open: true,
        type: 'error',
        message: '중복 제거할 파일을 선택해주세요.',
      });
      return;
    }
    
    if (!apiKey || !apiKey.trim()) {
      setAlert({
        open: true,
        type: 'error',
        message: 'OpenAI API 키를 입력해주세요. GPT 임베딩 방식을 사용하기 위해 필요합니다.',
      });
      return;
    }
    
    try {
      console.log('🚀 GPT 임베딩 중복 제거 시작...');
      
      // 1. 로딩 상태부터 설정
      setLoading(true);
      
      // 2. session_id 생성
      const newSessionId = `dedup_session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
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
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // 5. 요청 데이터
      const requestData = {
        file_path: selectedFile,
        similarity_threshold: similarityThreshold,
        batch_size: batchSize,
        session_id: newSessionId
      };
      
      console.log('📤 API 요청 시작:', requestData);
      
      // 6. API 요청을 비동기로 시작 (결과를 기다리지 않음)
      deduplicationService.removeDuplicates(
        selectedFile,
        apiKey,  // API 키 추가
        similarityThreshold,
        batchSize,
        newSessionId
      )
        .then(result => {
          console.log('📊 API 응답 수신:', result);
          
          if (result.success) {
            console.log('✅ API 요청 성공 - WebSocket 완료 메시지 대기 중...');
          } else {
            setAlert({
              open: true,
              type: 'error',
              message: `중복 제거에 실패했습니다: ${result.message}`,
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
      
      console.log('🔄 API 요청 시작됨 - WebSocket을 통한 진행도 업데이트 대기 중...');
      
    } catch (error) {
      console.error('❌ 중복 제거 중 오류:', error);
      setAlert({
        open: true,
        type: 'error',
        message: `오류가 발생했습니다: ${error.message}`,
      });
      setLoading(false);
      setShowProgress(false);
      setSessionId(null);
    }
  };

  const getSimilarityDescription = (threshold) => {
    if (threshold >= 0.9) return '매우 엄격 (거의 동일한 기사만 중복으로 판단)';
    if (threshold >= 0.8) return '엄격 (유사한 기사들을 중복으로 판단)';
    if (threshold >= 0.7) return '보통 (어느 정도 유사한 기사들을 중복으로 판단)';
    if (threshold >= 0.6) return '관대 (약간 유사한 기사들도 중복으로 판단)';
    return '매우 관대 (조금이라도 유사하면 중복으로 판단)';
  };

  return (
    <Box>
      <PageTitle 
        title="중복 제거" 
        subtitle="수집된 뉴스 기사에서 의미적으로 유사한 중복 기사를 제거합니다."
        breadcrumbs={[{ text: '중복 제거', path: '/deduplication' }]}
      />
      
      <AlertMessage
        open={alert.open}
        type={alert.type}
        title={alert.title}
        message={alert.message}
        onClose={() => setAlert({ ...alert, open: false })}
      />
      
      <Grid container spacing={3}>
        {/* 왼쪽 영역: 파일 선택 및 중복 제거 설정 */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              중복 제거할 파일 선택
            </Typography>
            
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
                  중복 제거할 파일이 없습니다. 먼저 '뉴스 수집' 페이지에서 뉴스를 수집해주세요.
                </Typography>
              )}
            </Box>
            
            {/* OpenAI API 키 입력 */}
            <Box sx={{ mb: 3 }}>
              <TextField
                fullWidth
                label="OpenAI API 키"
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk-..."
                helperText="GPT 임베딩 방식으로 중복 제거를 위해 OpenAI API 키가 필요합니다."
                variant="outlined"
                required
              />
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
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <Typography variant="h6" sx={{ flexGrow: 1 }}>
                중복 제거 설정
              </Typography>
              <Tooltip title="고급 설정 토글">
                <IconButton onClick={() => setAdvancedSettings(!advancedSettings)}>
                  <SettingsIcon />
                </IconButton>
              </Tooltip>
            </Box>
            
            {/* 유사도 임계값 설정 */}
            <Box sx={{ mb: 3 }}>
              <Typography gutterBottom>
                유사도 임계값: {similarityThreshold}
              </Typography>
              <Slider
                value={similarityThreshold}
                onChange={(e, value) => setSimilarityThreshold(value)}
                min={0.5}
                max={0.95}
                step={0.05}
                marks={[
                  { value: 0.5, label: '0.5' },
                  { value: 0.65, label: '0.65' },
                  { value: 0.8, label: '0.8' },
                  { value: 0.85, label: '0.85 (권장)' },
                  { value: 0.95, label: '0.95' }
                ]}
                valueLabelDisplay="auto"
              />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {getSimilarityDescription(similarityThreshold)}
              </Typography>
            </Box>
            
            {/* 고급 설정 */}
            {advancedSettings && (
              <Box sx={{ mb: 3, p: 2, border: '1px solid #e0e0e0', borderRadius: 1 }}>
                <Typography variant="h6" gutterBottom>
                  고급 설정
                </Typography>
                
                <Box sx={{ mt: 2 }}>
                  <Typography gutterBottom>
                    배치 크기: {batchSize}개
                  </Typography>
                  <Slider
                    value={batchSize}
                    onChange={(e, value) => setBatchSize(value)}
                    min={10}
                    max={100}
                    step={10}
                    marks={[
                      { value: 10, label: '10' },
                      { value: 30, label: '30' },
                      { value: 50, label: '50 (권장)' },
                      { value: 70, label: '70' },
                      { value: 100, label: '100' }
                    ]}
                    valueLabelDisplay="auto"
                  />
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    배치 크기가 클수록 빠르지만 메모리를 더 많이 사용합니다. 권장: 50개
                  </Typography>
                </Box>
              </Box>
            )}
            
            <Divider sx={{ mb: 3 }} />
            
            <Box sx={{ textAlign: 'center' }}>
              <Button
                variant="contained"
                color="primary"
                size="large"
                onClick={handleRemoveDuplicates}
                disabled={!selectedFile || !apiKey || loading}
                startIcon={<DeDupeIcon />}
                sx={{ px: 4, py: 1 }}
              >
                중복 제거 시작
              </Button>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                GPT 임베딩 방식으로 선택한 파일의 모든 뉴스 기사를 분석하여 중복을 제거합니다. 기사 수에 따라 수 분이 소요될 수 있습니다.
              </Typography>
            </Box>
          </Paper>
        </Grid>
        
        {/* 오른쪽 영역: 도움말 */}
        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                GPT 임베딩 중복 제거 정보
              </Typography>
              
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <InfoOutlinedIcon color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="고정확도 의미적 유사도 분석"
                    secondary="OpenAI의 GPT 임베딩 모델을 사용하여 제목과 내용의 의미를 이해하고 유사한 기사들을 탐지합니다. 정확도 90-95%"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <InfoOutlinedIcon color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="DBSCAN 클러스터링"
                    secondary="효율적인 중복 그룹 탐지로 성능 최적화. 대용량 데이터도 빠르게 처리"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <InfoOutlinedIcon color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="비용 최적화"
                    secondary="배치 처리로 API 비용 최소화. 1000개 기사 처리 시 약 $0.02-0.05 예상"
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                설정 가이드
              </Typography>
              
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <HelpOutlineIcon color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="API 키 설정"
                    secondary="OpenAI API 키가 필요합니다. openai.com에서 발급 받으세요. sk-로 시작합니다."
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <HelpOutlineIcon color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="유사도 임계값"
                    secondary="0.85 (권장): 적절한 수준의 중복 제거. 0.9 이상: 매우 엄격, 0.8 이하: 더 많은 기사를 중복으로 판단"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <HelpOutlineIcon color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="처리 시간 및 비용"
                    secondary="1000개 기사 기준 약 2-3분 소요. API 비용은 매우 저렴합니다 ($0.02-0.05)."
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      <LoadingOverlay
        open={loading && !showProgress}
        message="중복 제거를 준비하고 있습니다..."
      />
      
      {showProgress && sessionId && (
        <ProgressDialog
          open={showProgress}
          onClose={() => {
            setShowProgress(false);
            setSessionId(null);
            setLoading(false);
          }}
          sessionId={sessionId}
          title="중복 제거 진행중"
          type="deduplication"
        />
      )}
    </Box>
  );
};

export default DeduplicationPage;
