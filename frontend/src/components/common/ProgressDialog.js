import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  LinearProgress,
  Typography,
  Box,
  Chip,
  List,
  ListItem,
  ListItemText,
  Card,
  CardContent,
  Grid,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';

const ProgressDialog = ({ open, onClose, sessionId }) => {
  const [progress, setProgress] = useState({
    current: 0,
    total: 0,
    percentage: 0,
    isComplete: false,
    error: null
  });
  
  const [recentArticles, setRecentArticles] = useState([]);
  const [stats, setStats] = useState(null);
  const wsRef = useRef(null);
  const maxRecentArticles = 5;

  // WebSocket 연결 함수
  const connectWebSocket = useCallback(() => {
    if (!open || !sessionId) {
      console.log('🚫 WebSocket 연결 조건 불충족:', { open, sessionId });
      return;
    }

    console.log('🚀 WebSocket 연결 준비 시작...');

    // WebSocket URL (백엔드 포트 8000으로 명시적 지정)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const backendHost = window.location.hostname;
    const backendPort = '8000';  // 백엔드 포트 명시적 지정
    const wsUrl = `${protocol}//${backendHost}:${backendPort}/ws/${sessionId}`;
    
    console.log('🔗 WebSocket 연결 시도:', wsUrl);
    console.log('🖥️ 백엔드 호스트:', `${backendHost}:${backendPort}`);
    console.log('🏷️ 세션 ID:', sessionId);
    console.log('🌐 현재 URL:', window.location.href);
    console.log('🔌 프로토콜:', protocol);
    
    try {
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('✅ WebSocket 연결 성공:', sessionId);
        // 연결 확인 메시지 전송
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: 'ping', sessionId }));
          console.log('🏓 Ping 메시지 전송 완료');
        }
      };
      
      wsRef.current.onmessage = (event) => {
        console.log('📨 WebSocket 메시지 수신:', event.data);
        
        try {
          const data = JSON.parse(event.data);
          console.log('📊 파싱된 데이터:', data);
          
          // 즉시 처리를 위해 setTimeout 사용 안함
          switch (data.type) {
            case 'connection_established':
              console.log('🔗 연결 확인됨');
              break;
              
            case 'pong':
              console.log('🏓 Pong 응답 수신');
              break;
              
            case 'progress_update':
              console.log(`🔄 진행률 업데이트: ${data.current}/${data.total} (${data.percentage}%)`);
              
              // 즉시 업데이트
              setProgress({
                current: data.current,
                total: data.total,
                percentage: data.percentage,
                isComplete: false,
                error: null
              });
              
              // 최근 처리된 기사 목록 업데이트
              if (data.article_title && data.category) {
                setRecentArticles(prev => {
                  const newArticle = {
                    id: Date.now() + Math.random(), // 고유 ID 보장
                    title: data.article_title,
                    category: data.category,
                    confidence: data.confidence,
                    timestamp: new Date().toLocaleTimeString()
                  };
                  
                  const updated = [newArticle, ...prev].slice(0, maxRecentArticles);
                  console.log('📝 기사 목록 업데이트:', newArticle.title.substring(0, 50));
                  return updated;
                });
              }
              break;
              
            case 'analysis_complete':
              console.log('✅ 분석 완료:', data.stats);
              setProgress(prev => ({
                ...prev,
                isComplete: true
              }));
              setStats(data.stats);
              
              // 성공 알림 표시 (자동 이동 제거)
              setTimeout(() => {
                // 부모 컴포넌트에서 alert 설정하도록 커스텀 이벤트 발송
                if (window.showSuccessAlert) {
                  window.showSuccessAlert(data.stats, false); // 자동 이동 비활성화
                }
              }, 1000);
              break;
              
            case 'error':
              console.error('❌ 서버 오류:', data.message);
              setProgress(prev => ({
                ...prev,
                error: data.message
              }));
              break;
              
            default:
              console.log('❓ 알 수 없는 메시지 타입:', data.type);
          }
        } catch (parseError) {
          console.error('❌ JSON 파싱 오류:', parseError, 'Raw data:', event.data);
        }
      };
      
      wsRef.current.onerror = (error) => {
        console.error('❌ WebSocket 오류:', error);
        setProgress(prev => ({
          ...prev,
          error: 'WebSocket 연결 오류가 발생했습니다.'
        }));
      };
      
      wsRef.current.onclose = (event) => {
        console.log('🔌 WebSocket 연결 종료:', {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean
        });
      };
    } catch (connectionError) {
      console.error('❌ WebSocket 생성 오류:', connectionError);
      setProgress(prev => ({
        ...prev,
        error: `WebSocket 연결 실패: ${connectionError.message}`
      }));
    }
  }, [open, sessionId, maxRecentArticles]);

  // WebSocket 연결
  useEffect(() => {
    console.log('🔄 ProgressDialog useEffect 트리거:', { open, sessionId });
    
    if (!open || !sessionId) {
      console.log('⏸️ WebSocket 연결 조건 불충족:', { open, sessionId });
      return;
    }

    console.log('⏰ WebSocket 연결 준비 중...');
    
    // 상태가 완전히 업데이트되었는지 확인 후 연결
    const connectTimeout = setTimeout(() => {
      console.log('🚀 WebSocket 연결 시도 시작');
      connectWebSocket();
    }, 500); // 500ms로 증가

    // 컴포넌트 언마운트 시 WebSocket 연결 해제
    return () => {
      clearTimeout(connectTimeout);
      if (wsRef.current) {
        console.log('🔌 WebSocket 연결 해제 중...');
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [open, sessionId]); // connectWebSocket 의존성 제거

  // 다이얼로그 닫기 시 상태 초기화
  const handleClose = () => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    setProgress({
      current: 0,
      total: 0,
      percentage: 0,
      isComplete: false,
      error: null
    });
    setRecentArticles([]);
    setStats(null);
    
    // 분석 완료 시 결과 페이지로 이동
    if (progress.isComplete && window.analysisResult) {
      // 부모 컴포넌트에서 navigate 호출
      if (window.navigateToResults) {
        window.navigateToResults(window.analysisResult);
      }
    }
    
    onClose(); // 부모 컴포넌트에서 loading 상태 해제하도록 전달
  };

  const getCategoryColor = (category) => {
    switch (category) {
      case '자사언급기사':
        return 'error';
      case '업계관련기사':
        return 'primary';
      case '건기식펫푸드관련기사':
        return 'secondary';
      case '기타':
        return 'default';
      default:
        return 'default';
    }
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case '자사언급기사':
        return '🏢';
      case '업계관련기사':
        return '💄';
      case '건기식펫푸드관련기사':
        return '🍃';
      case '기타':
        return '📰';
      default:
        return '📰';
    }
  };

  return (
    <Dialog 
      open={open} 
      onClose={progress.isComplete ? handleClose : undefined}
      maxWidth="md"
      fullWidth
      disableEscapeKeyDown={!progress.isComplete}
    >
      <DialogTitle>
        {progress.isComplete ? (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CheckCircleIcon color="success" />
            <Typography variant="h6" component="span">관련성 평가 완료!</Typography>
          </Box>
        ) : progress.error ? (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ErrorIcon color="error" />
            <Typography variant="h6" component="span">오류 발생</Typography>
          </Box>
        ) : (
          <Typography variant="h6" component="span">관련성 평가 진행 중...</Typography>
        )}
      </DialogTitle>
      
      <DialogContent>
        {progress.error ? (
          <Typography color="error" variant="body1">
            {progress.error}
          </Typography>
        ) : (
          <Box>
            {/* 진행률 표시 */}
            <Box sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">
                  진행률: {progress.current}/{progress.total} 
                  {progress.total > 0 && ` (${progress.percentage.toFixed(1)}%)`}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {progress.isComplete ? '완료됨' : '진행 중...'}
                </Typography>
              </Box>
              
              <LinearProgress 
                variant="determinate" 
                value={progress.percentage} 
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Box>

            {/* 완료 통계 */}
            {progress.isComplete && stats && (
              <Card sx={{ mb: 3, bgcolor: 'success.light', color: 'success.contrastText' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    분석 완료 결과
                  </Typography>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={6} sm={3}>
                      <Typography variant="body2">총 기사 수</Typography>
                      <Typography variant="h6">{stats.total_items}개</Typography>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Typography variant="body2">관련 기사</Typography>
                      <Typography variant="h6">{stats.relevant_items}개</Typography>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Typography variant="body2">관련성 비율</Typography>
                      <Typography variant="h6">{stats.relevant_percent}%</Typography>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Typography variant="body2">처리 오류</Typography>
                      <Typography variant="h6">{stats.processing_errors}개</Typography>
                    </Grid>
                  </Grid>
                  
                  {/* 카테고리별 통계 */}
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body2" gutterBottom>카테고리별 분류:</Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {Object.entries(stats.categories || {}).map(([category, count]) => (
                        <Chip
                          key={category}
                          label={`${getCategoryIcon(category)} ${category}: ${count}개`}
                          color={getCategoryColor(category)}
                          size="small"
                        />
                      ))}
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            )}

            {/* 최근 처리된 기사 목록 */}
            {recentArticles.length > 0 && (
              <Box>
                <Typography variant="h6" gutterBottom>
                  최근 처리된 기사 ({recentArticles.length}개)
                </Typography>
                
                <List dense>
                  {recentArticles.map((article) => (
                    <ListItem key={article.id} divider>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                            <Typography variant="body2" sx={{ flex: 1, minWidth: 0 }}>
                              {article.title}
                            </Typography>
                            <Chip
                              label={`${getCategoryIcon(article.category)} ${article.category}`}
                              color={getCategoryColor(article.category)}
                              size="small"
                            />
                            {article.confidence && (
                              <Chip
                                label={`신뢰도: ${(article.confidence * 100).toFixed(1)}%`}
                                variant="outlined"
                                size="small"
                              />
                            )}
                          </Box>
                        }
                        secondary={`처리 시간: ${article.timestamp}`}
                      />
                    </ListItem>
                  ))}
                </List>
              </Box>
            )}
            
            {!progress.isComplete && progress.total === 0 && (
              <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center' }}>
                분석을 준비하고 있습니다...
              </Typography>
            )}
          </Box>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button 
          onClick={handleClose}
          variant={progress.isComplete ? "contained" : "outlined"}
          disabled={!progress.isComplete && !progress.error}
        >
          {progress.isComplete ? '확인' : progress.error ? '닫기' : '대기 중...'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ProgressDialog;
