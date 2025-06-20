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
import StopIcon from '@mui/icons-material/Stop';
import relevanceService from '../../api/relevanceService';

const ProgressDialog = ({ open, onClose, sessionId }) => {
  const [progress, setProgress] = useState({
    current: 0,
    total: 0,
    percentage: 0,
    isComplete: false,
    error: null,
    isStopped: false
  });
  
  const [isStopRequested, setIsStopRequested] = useState(false);
  
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

    // WebSocket URL - 동적으로 백엔드 주소 생성
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const currentHost = window.location.host;
    
    // 프론트엔드가 3000 포트라면 백엔드는 8000 포트로 추정
    let backendHost;
    if (currentHost.includes(':3000')) {
      backendHost = currentHost.replace(':3000', ':8000');
    } else if (currentHost.includes(':')) {
      // 다른 포트가 있다면 8000으로 변경
      backendHost = currentHost.split(':')[0] + ':8000';
    } else {
      // 포트가 없다면 8000 추가
      backendHost = currentHost + ':8000';
    }
    
    const wsUrl = `${protocol}//${backendHost}/ws/${sessionId}`;
    
    console.log('🔗 WebSocket 연결 시도:', wsUrl);
    console.log('🖥️ 백엔드 호스트:', backendHost);
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
        try {
          const data = JSON.parse(event.data);
          console.log('📊 WebSocket 메시지 수신:', data.type, data.current ? `${data.current}/${data.total}` : '');
          
          // 즉시 처리를 위해 setTimeout 사용 안함
          switch (data.type) {
            case 'connection_established':
              console.log('🔗 연결 확인됨');
              break;
              
            case 'pong':
              // pong 응답은 로그 최소화
              break;
              
            case 'progress_update':
              // 즉시 업데이트
              setProgress({
                current: data.current,
                total: data.total,
                percentage: data.percentage,
                isComplete: false,
                error: null,
                isStopped: false
              });
              
              // 최근 처리된 기사 목록 업데이트 (카테고리가 있는 완료된 기사만)
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
                if (window.showSuccessAlert) {
                  window.showSuccessAlert(data.stats, false); // 자동 이동 비활성화
                }
              }, 1000);
              break;
              
            case 'deduplication_complete':
              console.log('✅ 중복 제거 완료:', data.stats);
              setProgress(prev => ({
                ...prev,
                isComplete: true
              }));
              setStats(data.stats);
              
              // 중복 제거 성공 알림 표시
              setTimeout(() => {
                if (window.showDeduplicationSuccessAlert) {
                  window.showDeduplicationSuccessAlert(data.stats, false);
                }
              }, 1000);
              break;
              
            case 'analysis_stopped':
              console.log('⏹️ 분석 중지:', data.message);
              setProgress(prev => ({
                ...prev,
                isStopped: true,
                isComplete: true // 다이얼로그를 닫을 수 있도록
              }));
              setIsStopRequested(false);
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
          error: 'WebSocket 연결 오류가 발생했습니다. 백엔드 서버가 실행 중인지 확인해주세요.'
        }));
      };
      
      wsRef.current.onclose = (event) => {
        console.log('🔌 WebSocket 연결 종료:', {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean
        });
        
        // 비정상 종료인 경우 재연결 시도 (최대 3회)
        if (!event.wasClean && open && sessionId) {
          const retryCount = (wsRef.current?._retryCount || 0) + 1;
          if (retryCount <= 3) {
            console.log(`🔄 WebSocket 재연결 시도 ${retryCount}/3...`);
            setTimeout(() => {
              if (open && sessionId) {
                const newWs = new WebSocket(wsUrl);
                newWs._retryCount = retryCount;
                wsRef.current = newWs;
                // 이벤트 핸들러 재설정은 생략 (간단한 재연결만)
              }
            }, 2000 * retryCount); // 지수 백오프
          }
        }
      };
    } catch (connectionError) {
      console.error('❌ WebSocket 생성 오류:', connectionError);
      setProgress(prev => ({
        ...prev,
        error: `WebSocket 연결 실패: ${connectionError.message}. 백엔드 서버 상태를 확인해주세요.`
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
        wsRef.current.close(1000, 'Component unmounting'); // 정상 종료 코드
        wsRef.current = null;
      }
    };
  }, [open, sessionId, connectWebSocket]); // connectWebSocket 의존성 추가

  // 분석 중지 함수
  const handleStopAnalysis = async () => {
    if (!sessionId || isStopRequested) {
      return;
    }
    
    setIsStopRequested(true);
    
    try {
      console.log('🛑 분석 중지 요청:', sessionId);
      const response = await relevanceService.stopAnalysis(sessionId);
      
      if (response.success) {
        console.log('✅ 중지 요청 성공:', response.message);
        // WebSocket을 통해 중지 상태가 업데이트됨
      } else {
        console.error('❌ 중지 요청 실패:', response.message);
        setIsStopRequested(false);
        setProgress(prev => ({
          ...prev,
          error: response.message
        }));
      }
    } catch (error) {
      console.error('❌ 중지 요청 중 오류:', error);
      setIsStopRequested(false);
      setProgress(prev => ({
        ...prev,
        error: '중지 요청 중 오류가 발생했습니다.'
      }));
    }
  };
  
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
      error: null,
      isStopped: false
    });
    setRecentArticles([]);
    setStats(null);
    setIsStopRequested(false);
    
    // 분석 완료 시 상태 초기화
    if (progress.isComplete && window.analysisResult) {
      // 부모 컴포넌트에서 navigate 호출
      if (window.navigateToResults) {
        window.navigateToResults(window.analysisResult);
      }
    }
    
    // 중복 제거 완료 시 관련성 평가 페이지로 이동
    if (progress.isComplete && window.deduplicationResult) {
      if (window.navigateToRelevance) {
        window.navigateToRelevance(window.deduplicationResult);
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
          progress.isStopped ? (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <StopIcon color="warning" />
              <Typography variant="h6" component="span">분석이 중지되었습니다</Typography>
            </Box>
          ) : (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CheckCircleIcon color="success" />
              <Typography variant="h6" component="span">관련성 평가 완료!</Typography>
            </Box>
          )
        ) : progress.error ? (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ErrorIcon color="error" />
            <Typography variant="h6" component="span">오류 발생</Typography>
          </Box>
        ) : (
          <Typography variant="h6" component="span">
            {/* 제목을 type prop이나 stats 내용으로 결정 */}
            {stats?.relevant_items !== undefined || recentArticles.some(a => a.category) 
              ? '관련성 평가 진행 중...' 
              : '중복 제거 진행 중...'
            }
          </Typography>
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
                {progress.isComplete ? (
                    progress.isStopped ? '사용자에 의해 중지됨' : '완료됨'
                ) : (
                  isStopRequested ? '중지 요청 중...' : '진행 중...'
                )}
              </Typography>
              </Box>
              
              <LinearProgress 
                variant="determinate" 
                value={progress.percentage} 
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Box>

            {/* 완료 통계 */}
            {progress.isComplete && !progress.isStopped && stats && (
              <Card sx={{ mb: 3, bgcolor: 'success.light', color: 'success.contrastText' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {stats.relevant_items !== undefined ? '분석 완료 결과' : '중복 제거 완료 결과'}
                  </Typography>
                  
                  {stats.relevant_items !== undefined ? (
                    // 관련성 분석 결과
                    <>
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
                    </>
                  ) : (
                    // 중복 제거 결과
                    <Grid container spacing={2}>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2">원본 기사 수</Typography>
                        <Typography variant="h6">{stats.original_count}개</Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2">최종 기사 수</Typography>
                        <Typography variant="h6">{stats.deduplicated_count}개</Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2">제거된 기사</Typography>
                        <Typography variant="h6">{stats.removed_count}개</Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2">제거율</Typography>
                        <Typography variant="h6">{stats.reduction_percentage}%</Typography>
                      </Grid>
                    </Grid>
                  )}
                </CardContent>
              </Card>
            )}

            {/* 중지된 경우 메시지 */}
            {progress.isStopped && (
              <Card sx={{ mb: 3, bgcolor: 'warning.light', color: 'warning.contrastText' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    분석 중지됨
                  </Typography>
                  <Typography variant="body2">
                    사용자 요청에 의해 분석이 중지되었습니다. 
                    {progress.current > 0 && `${progress.current}개 기사가 처리되었습니다.`}
                  </Typography>
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
        {!progress.isComplete && !progress.error && (
          <Button 
            onClick={handleStopAnalysis}
            color="warning"
            variant="outlined"
            disabled={isStopRequested}
            startIcon={<StopIcon />}
            sx={{ mr: 1 }}
          >
            {isStopRequested ? '중지 요청 중...' : '분석 중지'}
          </Button>
        )}
        
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
