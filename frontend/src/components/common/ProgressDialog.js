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
  Grid
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import AnalyticsIcon from '@mui/icons-material/Analytics';

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
  const remainingTime = total > 0 && current > 0 ? 
    Math.round(((total - current) / current) * (Date.now() - (progress.startTime || Date.now())) / 1000) : 
    null;

  return (
    <Dialog 
      open={open} 
      onClose={onClose}
      maxWidth="md" 
      fullWidth
      disableEscapeKeyDown={!onClose}
    >
      <DialogTitle sx={{ pb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AnalyticsIcon color="primary" />
          {title}
        </Box>
      </DialogTitle>
      
      <DialogContent>
        <Box sx={{ mb: 3 }}>
          {/* 전체 진행률 */}
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2" color="text.secondary">
                전체 진행률
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {current} / {total} ({percentage}%)
              </Typography>
            </Box>
            <LinearProgress 
              variant="determinate" 
              value={percentage} 
              sx={{ height: 8, borderRadius: 4 }}
            />
          </Box>

          {/* 현재 단계 정보 */}
          {stage && (
            <Paper sx={{ p: 2, mb: 2, bgcolor: 'primary.50' }}>
              <Typography variant="subtitle2" color="primary" gutterBottom>
                현재 단계: {stage}
              </Typography>
              {currentItem && (
                <Typography variant="body2" color="text.secondary">
                  처리 중: {currentItem}
                </Typography>
              )}
              
              {remainingTime && remainingTime > 0 && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  예상 남은 시간: {Math.floor(remainingTime / 60)}분 {remainingTime % 60}초
                </Typography>
              )}
            </Paper>
          )}

          {/* 통계 정보 */}
          {Object.keys(stats).length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                현재 통계
              </Typography>
              <Grid container spacing={1}>
                {stats.relevant_items !== undefined && (
                  <Grid item xs={6} sm={3}>
                    <Chip 
                      label={`관련 기사: ${stats.relevant_items}`} 
                      color="success" 
                      variant="outlined" 
                      size="small" 
                    />
                  </Grid>
                )}
                {stats.irrelevant_items !== undefined && (
                  <Grid item xs={6} sm={3}>
                    <Chip 
                      label={`비관련 기사: ${stats.irrelevant_items}`} 
                      color="default" 
                      variant="outlined" 
                      size="small" 
                    />
                  </Grid>
                )}
                {stats.errors !== undefined && stats.errors > 0 && (
                  <Grid item xs={6} sm={3}>
                    <Chip 
                      label={`오류: ${stats.errors}`} 
                      color="error" 
                      variant="outlined" 
                      size="small" 
                    />
                  </Grid>
                )}
                {stats.processing_rate !== undefined && (
                  <Grid item xs={6} sm={3}>
                    <Chip 
                      label={`처리 속도: ${stats.processing_rate}/분`} 
                      color="info" 
                      variant="outlined" 
                      size="small" 
                    />
                  </Grid>
                )}
              </Grid>
            </Box>
          )}

          {/* 최근 처리된 항목들 */}
          {processedItems.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                최근 처리된 기사 (최대 5개)
              </Typography>
              <List dense sx={{ maxHeight: 200, overflow: 'auto' }}>
                {processedItems.slice(-5).reverse().map((item, index) => (
                  <ListItem key={index} sx={{ py: 0.5 }}>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      <CheckCircleIcon color="success" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Typography variant="body2" noWrap>
                          {item.title || `항목 ${item.index || index + 1}`}
                        </Typography>
                      }
                      secondary={
                        item.category && (
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
                        )
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}

          {/* 오류 목록 */}
          {errors.length > 0 && (
            <Box>
              <Typography variant="subtitle2" color="error" gutterBottom>
                오류 발생 ({errors.length}개)
              </Typography>
              <List dense sx={{ maxHeight: 150, overflow: 'auto' }}>
                {errors.slice(-3).map((error, index) => (
                  <ListItem key={index} sx={{ py: 0.5 }}>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      <ErrorIcon color="error" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Typography variant="body2" color="error">
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
            </Box>
          )}

          {/* 로딩 상태 표시 */}
          {current === 0 && total === 0 && (
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', py: 4 }}>
              <CircularProgress sx={{ mr: 2 }} />
              <Typography variant="body2" color="text.secondary">
                분석을 준비하고 있습니다...
              </Typography>
            </Box>
          )}
        </Box>
      </DialogContent>
    </Dialog>
  );
};

export default ProgressDialog;