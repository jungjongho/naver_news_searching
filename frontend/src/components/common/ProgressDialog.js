import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Box,
  Typography,
  LinearProgress,
  CircularProgress,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Grid,
  Divider
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import ArticleIcon from '@mui/icons-material/Article';

const ProgressDialog = ({ 
  open, 
  title = "관련성 평가 진행 중",
  progress = {},
  onClose = null // null이면 닫기 불가능
}) => {
  const {
    current = 0,
    total = 0,
    stage = '',
    currentItem = '',
    processedItems = [],
    errors = [],
    stats = {}
  } = progress;

  const percentage = total > 0 ? Math.round((current / total) * 100) : 0;
  const startTime = progress.startTime || Date.now();
  const elapsedTime = Math.floor((Date.now() - startTime) / 1000);
  const remainingTime = total > 0 && current > 0 ? 
    Math.round(((total - current) / current) * elapsedTime) : 
    null;

  const formatTime = (seconds) => {
    if (seconds < 60) return `${seconds}초`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}분 ${seconds % 60}초`;
    return `${Math.floor(seconds / 3600)}시간 ${Math.floor((seconds % 3600) / 60)}분`;
  };

  const getRelevanceRate = () => {
    if (stats.relevant_items !== undefined && current > 0) {
      return Math.round((stats.relevant_items / current) * 100);
    }
    return 0;
  };

  return (
    <Dialog 
      open={open} 
      onClose={onClose}
      maxWidth="md" 
      fullWidth
      disableEscapeKeyDown={!onClose}
      PaperProps={{
        sx: { 
          minHeight: '500px',
          bgcolor: 'background.default'
        }
      }}
    >
      <DialogTitle sx={{ pb: 1, bgcolor: 'primary.main', color: 'white' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AnalyticsIcon />
          {title}
        </Box>
      </DialogTitle>
      
      <DialogContent sx={{ pt: 3 }}>
        {/* 전체 진행률 섹션 개선 */}
        <Paper sx={{ p: 3, mb: 3, bgcolor: 'grey.50' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" color="primary" fontWeight="bold">
              진행률: {current} / {total}
            </Typography>
            <Chip 
              label={`${percentage}%`} 
              color="primary" 
              variant="filled"
              sx={{ fontWeight: 'bold', fontSize: '1.1rem', px: 2 }}
            />
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={percentage} 
            sx={{ 
              height: 12, 
              borderRadius: 6,
              bgcolor: 'grey.200',
              '& .MuiLinearProgress-bar': {
                borderRadius: 6,
                bgcolor: percentage < 30 ? 'warning.main' : 
                         percentage < 70 ? 'info.main' : 'success.main'
              }
            }}
          />
          
          {/* 시간 정보 */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2, gap: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AccessTimeIcon fontSize="small" color="action" />
              <Typography variant="body2" color="text.secondary">
                경과: {formatTime(elapsedTime)}
              </Typography>
            </Box>
            {remainingTime && remainingTime > 0 && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TrendingUpIcon fontSize="small" color="action" />
                <Typography variant="body2" color="text.secondary">
                  예상 남은 시간: {formatTime(remainingTime)}
                </Typography>
              </Box>
            )}
          </Box>
        </Paper>

        {/* 현재 단계 정보 개선 */}
        {stage && (
          <Paper sx={{ p: 2, mb: 3, bgcolor: 'info.50', border: '1px solid', borderColor: 'info.200' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <ArticleIcon color="info" fontSize="small" />
              <Typography variant="subtitle1" color="info.dark" fontWeight="medium">
                {stage}
              </Typography>
            </Box>
            {currentItem && (
              <Typography variant="body2" color="text.secondary" sx={{ 
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}>
                현재 처리중: {currentItem}
              </Typography>
            )}
          </Paper>
        )}

        {/* 실시간 통계 개선 */}
        {Object.keys(stats).length > 0 && (
          <Paper sx={{ p: 2, mb: 3 }}>
            <Typography variant="subtitle1" gutterBottom sx={{ color: 'primary.main', fontWeight: 'medium' }}>
              실시간 분석 통계
            </Typography>
            <Grid container spacing={2}>
              {stats.relevant_items !== undefined && (
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center', p: 1 }}>
                    <Typography variant="h5" color="success.main" fontWeight="bold">
                      {stats.relevant_items}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      관련 기사
                    </Typography>
                    <Typography variant="caption" color="success.main">
                      ({getRelevanceRate()}%)
                    </Typography>
                  </Box>
                </Grid>
              )}
              {stats.irrelevant_items !== undefined && (
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center', p: 1 }}>
                    <Typography variant="h5" color="text.secondary" fontWeight="bold">
                      {stats.irrelevant_items}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      비관련 기사
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      ({100 - getRelevanceRate()}%)
                    </Typography>
                  </Box>
                </Grid>
              )}
              {stats.processing_rate !== undefined && (
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center', p: 1 }}>
                    <Typography variant="h5" color="info.main" fontWeight="bold">
                      {stats.processing_rate}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      기사/분
                    </Typography>
                    <Typography variant="caption" color="info.main">
                      처리 속도
                    </Typography>
                  </Box>
                </Grid>
              )}
              {stats.errors !== undefined && stats.errors > 0 && (
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center', p: 1 }}>
                    <Typography variant="h5" color="error.main" fontWeight="bold">
                      {stats.errors}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      오류 발생
                    </Typography>
                    <Typography variant="caption" color="error.main">
                      문제 기사
                    </Typography>
                  </Box>
                </Grid>
              )}
            </Grid>
          </Paper>
        )}

        {/* 최근 처리된 항목들 개선 */}
        {processedItems.length > 0 && (
          <Paper sx={{ p: 2, mb: 3 }}>
            <Typography variant="subtitle1" gutterBottom sx={{ color: 'primary.main', fontWeight: 'medium' }}>
              최근 처리된 기사 (최대 5개)
            </Typography>
            <Divider sx={{ mb: 1 }} />
            <List dense sx={{ maxHeight: 250, overflow: 'auto' }}>
              {processedItems.slice(-5).reverse().map((item, index) => (
                <ListItem key={index} sx={{ py: 1, px: 1, borderRadius: 1, '&:hover': { bgcolor: 'grey.50' } }}>
                  <ListItemIcon sx={{ minWidth: 32 }}>
                    <CheckCircleIcon color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Typography variant="body2" sx={{ 
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        fontWeight: 'medium'
                      }}>
                        {item.title || `항목 ${item.index || index + 1}`}
                      </Typography>
                    }
                    secondary={
                      <Box sx={{ mt: 0.5 }}>
                        {item.category && (
                          <Chip 
                            label={item.category} 
                            size="small" 
                            color={
                              item.category.includes('자사') ? 'error' :
                              item.category.includes('업계') ? 'primary' :
                              item.category.includes('건기식') ? 'warning' : 'default'
                            }
                            variant="outlined"
                          />
                        )}
                        {item.confidence && (
                          <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                            신뢰도: {Math.round(item.confidence * 100)}%
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        )}

        {/* 오류 목록 개선 */}
        {errors.length > 0 && (
          <Paper sx={{ p: 2, bgcolor: 'error.50', border: '1px solid', borderColor: 'error.200' }}>
            <Typography variant="subtitle1" color="error.dark" gutterBottom fontWeight="medium">
              오류 발생 ({errors.length}개)
            </Typography>
            <Divider sx={{ mb: 1, borderColor: 'error.200' }} />
            <List dense sx={{ maxHeight: 200, overflow: 'auto' }}>
              {errors.slice(-3).map((error, index) => (
                <ListItem key={index} sx={{ py: 1, px: 1, borderRadius: 1 }}>
                  <ListItemIcon sx={{ minWidth: 32 }}>
                    <ErrorIcon color="error" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Typography variant="body2" color="error.dark" fontWeight="medium">
                        {error.message || error}
                      </Typography>
                    }
                    secondary={error.item && (
                      <Typography variant="caption" color="text.secondary">
                        항목: {error.item}
                      </Typography>
                    )}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        )}

        {/* 로딩 상태 표시 개선 */}
        {current === 0 && total === 0 && (
          <Paper sx={{ p: 4, textAlign: 'center', bgcolor: 'grey.50' }}>
            <CircularProgress size={60} sx={{ mb: 2 }} />
            <Typography variant="h6" color="primary" gutterBottom>
              분석 준비 중
            </Typography>
            <Typography variant="body2" color="text.secondary">
              AI 모델을 초기화하고 분석을 준비하고 있습니다...
            </Typography>
          </Paper>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default ProgressDialog;