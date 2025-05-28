import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Box,
  Button,
  Paper,
  Typography,
  Grid,
  Table,
  TableContainer,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  // Card,
  // CardContent,
  Tabs,
  Tab,
  Chip,
  // Link,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  Stack,
  Snackbar,
  Alert,
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import VisibilityIcon from '@mui/icons-material/Visibility';
// import TableChartIcon from '@mui/icons-material/TableChart';
import BarChartIcon from '@mui/icons-material/BarChart';
import PieChartIcon from '@mui/icons-material/PieChart';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import CloudDownloadIcon from '@mui/icons-material/CloudDownload';
import { Bar, Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip as ChartTooltip, Legend, CategoryScale, LinearScale, BarElement, Title } from 'chart.js';

import PageTitle from '../components/common/PageTitle';
import AlertMessage from '../components/common/AlertMessage';
import LoadingOverlay from '../components/common/LoadingOverlay';
import DownloadButton from '../components/common/DownloadButton';
import BulkDownloadButton from '../components/common/BulkDownloadButton';
import crawlerService from '../api/crawlerService';
import { downloadFile } from '../api/downloadService';
import { formatDate, /* formatFileSize, */ getFileDownloadUrl, getCategoryColor } from '../utils/helpers';

// ChartJS 등록
ChartJS.register(ArcElement, ChartTooltip, Legend, CategoryScale, LinearScale, BarElement, Title);

const ResultsPage = () => {
  const location = useLocation();
  
  // 상태 관리
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [filePreview, setFilePreview] = useState(null);
  const [fileStats, setFileStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [alert, setAlert] = useState({ open: false, type: 'info', message: '', title: '' });
  const [tabValue, setTabValue] = useState(0);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  

  
  // 평가 페이지에서 전달된 데이터 처리
  useEffect(() => {
    if (location.state?.evaluationResult && location.state?.fromRelevance) {
      const evalResult = location.state.evaluationResult;
      
      // 자동으로 떠있는 알림 표시
      setAlert({
        open: true,
        type: 'success',
        title: '관련성 평가 완료',
        message: `뉴스 기사의 관련성 평가가 완료되었습니다. 관련 뉴스: ${evalResult.stats.relevant_count}/${evalResult.stats.total_count} (${evalResult.stats.relevant_percent}%)`,
      });
    }
    
    // 파일 목록 로드
    loadFiles();
  }, [location.state]);
  
  // 파일 목록 로드
  const loadFiles = async () => {
    setLoading(true);
    try {
      const fileList = await crawlerService.getFiles();
      setFiles(fileList);
      
      // 평가된 파일이 있으면 첫 번째 파일 선택
      const evaluatedFiles = fileList.filter(file => file.has_evaluation || file.is_evaluated);
      if (evaluatedFiles.length > 0) {
        handleSelectFile(evaluatedFiles[0]);
      }
    } catch (error) {
      console.error('파일 목록 로드 중 오류:', error);
      setAlert({
        open: true,
        type: 'error',
        message: '파일 목록을 불러오는 중 오류가 발생했습니다.',
      });
    } finally {
      setLoading(false);
    }
  };
  
  // 파일 선택
  const handleSelectFile = async (file) => {
    setSelectedFile(file);
    setLoading(true);
    
    try {
      // 파일 미리보기 및 통계 로드
      const preview = await crawlerService.getFilePreview(file.file_name, 10);
      const stats = await crawlerService.getFileStatistics(file.file_name);
      
      setFilePreview(preview);
      setFileStats(stats);
    } catch (error) {
      console.error('파일 정보 로드 중 오류:', error);
      setAlert({
        open: true,
        type: 'error',
        message: '파일 정보를 불러오는 중 오류가 발생했습니다.',
      });
    } finally {
      setLoading(false);
    }
  };
  
  // 탭 변경
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };
  
  // 미리보기 다이얼로그 열기
  const handleOpenPreviewDialog = () => {
    setPreviewDialogOpen(true);
  };
  
  // 미리보기 다이얼로그 닫기
  const handleClosePreviewDialog = () => {
    setPreviewDialogOpen(false);
  };
  
  // 파일 다운로드
  const handleDownload = () => {
    if (selectedFile) {
      downloadFile(selectedFile.file_name);
      setSnackbar({
        open: true,
        message: `${selectedFile.file_name} 파일 다운로드를 시작합니다.`,
        severity: 'success'
      });
    }
  };
  
  // 카테고리 차트 데이터 생성
  const getCategoryChartData = () => {
    if (!fileStats || !fileStats.category_counts) return null;
    
    const categories = Object.keys(fileStats.category_counts);
    const counts = Object.values(fileStats.category_counts);
    
    return {
      labels: categories,
      datasets: [
        {
          data: counts,
          backgroundColor: categories.map(category => getCategoryColor(category)),
          borderWidth: 1,
        },
      ],
    };
  };
  
  // 관련성 차트 데이터 생성
  const getRelevanceChartData = () => {
    if (!fileStats || !fileStats.relevant_count) return null;
    
    return {
      labels: ['관련 있음', '관련 없음'],
      datasets: [
        {
          data: [fileStats.relevant_count, fileStats.total_count - fileStats.relevant_count],
          backgroundColor: ['#4caf50', '#f44336'],
          borderWidth: 1,
        },
      ],
    };
  };
  
  // 키워드 차트 데이터 생성
  const getKeywordChartData = () => {
    if (!fileStats || !fileStats.keyword_counts) return null;
    
    // 상위 10개 키워드만 표시
    const keywordEntries = Object.entries(fileStats.keyword_counts).sort((a, b) => b[1] - a[1]).slice(0, 10);
    const keywords = keywordEntries.map(entry => entry[0]);
    const counts = keywordEntries.map(entry => entry[1]);
    
    return {
      labels: keywords,
      datasets: [
        {
          label: '뉴스 기사 수',
          data: counts,
          backgroundColor: 'rgba(54, 162, 235, 0.6)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1,
        },
      ],
    };
  };

  return (
    <Box>
      <PageTitle 
        title="결과 목록" 
        subtitle="수집 및 평가된 뉴스 기사의 결과를 확인합니다."
        breadcrumbs={[{ text: '결과 목록', path: '/results' }]}
      />
      
      <AlertMessage
        open={alert.open}
        type={alert.type}
        title={alert.title}
        message={alert.message}
        onClose={() => setAlert({ ...alert, open: false })}
      />
      
      <Grid container spacing={3}>
        {/* 왼쪽 영역: 파일 목록 */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, mb: { xs: 2, md: 0 } }}>
            <Typography variant="h6" gutterBottom>
              파일 목록
            </Typography>
            
            {files.length > 0 ? (
              <Box>
                <TableContainer sx={{ maxHeight: 500 }}>
                  <Table stickyHeader size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>파일명</TableCell>
                        <TableCell>수정 날짜</TableCell>
                        <TableCell>크기</TableCell>
                        <TableCell>평가</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {files.map((file) => (
                        <TableRow 
                          key={file.file_name}
                          onClick={() => handleSelectFile(file)}
                          hover
                          selected={selectedFile && selectedFile.file_name === file.file_name}
                          sx={{ cursor: 'pointer' }}
                        >
                          <TableCell sx={{ maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {file.file_name}
                          </TableCell>
                          <TableCell>{formatDate(file.modified_time_str)}</TableCell>
                          <TableCell>{file.file_size_str}</TableCell>
                          <TableCell>
                            {file.has_evaluation || file.is_evaluated ? (
                              <Chip 
                                label="평가됨" 
                                size="small" 
                                color="success" 
                                variant="outlined" 
                              />
                            ) : (
                              <Chip 
                                label="미평가" 
                                size="small" 
                                color="default" 
                                variant="outlined" 
                              />
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
                
                <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    총 {files.length}개 파일
                  </Typography>
                  
                  <Box>
                    <BulkDownloadButton 
                      files={files}
                      variant="outlined"
                      size="small"
                      label="일괄 다운로드"
                      sx={{ mr: 1 }}
                    />
                    <Button
                      variant="outlined"
                      color="primary"
                      size="small"
                      onClick={loadFiles}
                    >
                      새로고침
                    </Button>
                  </Box>
                </Box>
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">
                파일이 없습니다. 먼저 '뉴스 수집' 페이지에서 뉴스를 수집해주세요.
              </Typography>
            )}
          </Paper>
        </Grid>
        
        {/* 오른쪽 영역: 파일 정보 및 차트 */}
        <Grid item xs={12} md={8}>
          {selectedFile ? (
            <Box>
              {/* 선택된 파일 정보 */}
              <Paper sx={{ p: 2, mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">
                    {selectedFile.file_name}
                  </Typography>
                  
                  <Box>
                    <Tooltip title="파일 다운로드">
                      <IconButton color="primary" onClick={handleDownload}>
                        <DownloadIcon />
                      </IconButton>
                    </Tooltip>
                    
                    <Tooltip title="미리보기">
                      <IconButton color="primary" onClick={handleOpenPreviewDialog}>
                        <VisibilityIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>
                
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="body2">
                      <strong>수정 날짜:</strong> {formatDate(selectedFile.modified_time_str)}
                    </Typography>
                    <Typography variant="body2">
                      <strong>파일 크기:</strong> {selectedFile.file_size_str}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    {fileStats && (
                      <>
                        <Typography variant="body2">
                          <strong>총 기사 수:</strong> {fileStats.total_rows || 0}
                        </Typography>
                        {fileStats.relevant_count && (
                          <Typography variant="body2">
                            <strong>관련 기사 수:</strong> {fileStats.relevant_count} ({fileStats.relevant_percent}%)
                          </Typography>
                        )}
                      </>
                    )}
                  </Grid>
                </Grid>
                
                <Divider sx={{ my: 2 }} />
                
                <Stack direction="row" spacing={2} justifyContent="flex-end">
                  <DownloadButton
                    fileName={selectedFile.file_name}
                    variant="outlined"
                    size="small"
                    label="파일 다운로드"
                  />
                </Stack>
              </Paper>
              
              {/* 차트 및 데이터 탭 */}
              <Paper sx={{ p: 2 }}>
                <Tabs
                  value={tabValue}
                  onChange={handleTabChange}
                  indicatorColor="primary"
                  textColor="primary"
                  variant="fullWidth"
                  aria-label="데이터 탭"
                >
                  <Tab 
                    icon={<PieChartIcon />} 
                    label="카테고리 분석" 
                    disabled={!fileStats || !fileStats.category_counts}
                  />
                  <Tab 
                    icon={<PieChartIcon />} 
                    label="관련성 분석" 
                    disabled={!fileStats || !fileStats.relevant_count}
                  />
                  <Tab 
                    icon={<BarChartIcon />} 
                    label="키워드 분석" 
                    disabled={!fileStats || !fileStats.keyword_counts}
                  />
                </Tabs>
                
                <Box sx={{ p: 2 }}>
                  {/* 카테고리 분석 탭 */}
                  {tabValue === 0 && fileStats && fileStats.category_counts && (
                    <Box>
                      <Typography variant="subtitle1" gutterBottom align="center">
                        카테고리별 기사 수
                      </Typography>
                      
                      <Box sx={{ height: 300, display: 'flex', justifyContent: 'center' }}>
                        <Pie 
                          data={getCategoryChartData()} 
                          options={{
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                              legend: {
                                position: 'right',
                              },
                            },
                          }}
                        />
                      </Box>
                      
                      <Box sx={{ mt: 3 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                          <Typography variant="subtitle2" gutterBottom>
                            카테고리 통계
                          </Typography>
                          <DownloadButton 
                            fileName={selectedFile.file_name} 
                            variant="text" 
                            size="small" 
                            label="데이터 다운로드" 
                          />
                        </Box>
                        
                        <TableContainer>
                          <Table size="small">
                            <TableHead>
                              <TableRow>
                                <TableCell>카테고리</TableCell>
                                <TableCell align="right">기사 수</TableCell>
                                <TableCell align="right">비율</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {fileStats.category_counts && Object.entries(fileStats.category_counts).map(([category, count]) => (
                                <TableRow key={category}>
                                  <TableCell>
                                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                      <Box
                                        sx={{
                                          width: 12,
                                          height: 12,
                                          borderRadius: '50%',
                                          backgroundColor: getCategoryColor(category),
                                          mr: 1,
                                        }}
                                      />
                                      {category}
                                    </Box>
                                  </TableCell>
                                  <TableCell align="right">{count}</TableCell>
                                  <TableCell align="right">
                                    {Math.round((count / fileStats.total_rows) * 100)}%
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </Box>
                    </Box>
                  )}
                  
                  {/* 관련성 분석 탭 */}
                  {tabValue === 1 && fileStats && fileStats.relevant_count && (
                    <Box>
                      <Typography variant="subtitle1" gutterBottom align="center">
                        관련성 평가 결과
                      </Typography>
                      
                      <Box sx={{ height: 300, display: 'flex', justifyContent: 'center' }}>
                        <Pie 
                          data={getRelevanceChartData()} 
                          options={{
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                              legend: {
                                position: 'right',
                              },
                            },
                          }}
                        />
                      </Box>
                      
                      <Box sx={{ mt: 3 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                          <Typography variant="subtitle2" gutterBottom>
                            관련성 통계
                          </Typography>
                          <DownloadButton 
                            fileName={selectedFile.file_name} 
                            variant="text" 
                            size="small" 
                            label="데이터 다운로드" 
                          />
                        </Box>
                        
                        <TableContainer>
                          <Table size="small">
                            <TableHead>
                              <TableRow>
                                <TableCell>관련성</TableCell>
                                <TableCell align="right">기사 수</TableCell>
                                <TableCell align="right">비율</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              <TableRow>
                                <TableCell>
                                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                    <Box
                                      sx={{
                                        width: 12,
                                        height: 12,
                                        borderRadius: '50%',
                                        backgroundColor: '#4caf50',
                                        mr: 1,
                                      }}
                                    />
                                    관련 있음
                                  </Box>
                                </TableCell>
                                <TableCell align="right">{fileStats.relevant_count}</TableCell>
                                <TableCell align="right">{fileStats.relevant_percent}%</TableCell>
                              </TableRow>
                              <TableRow>
                                <TableCell>
                                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                    <Box
                                      sx={{
                                        width: 12,
                                        height: 12,
                                        borderRadius: '50%',
                                        backgroundColor: '#f44336',
                                        mr: 1,
                                      }}
                                    />
                                    관련 없음
                                  </Box>
                                </TableCell>
                                <TableCell align="right">{fileStats.total_count - fileStats.relevant_count}</TableCell>
                                <TableCell align="right">{100 - fileStats.relevant_percent}%</TableCell>
                              </TableRow>
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </Box>
                    </Box>
                  )}
                  
                  {/* 키워드 분석 탭 */}
                  {tabValue === 2 && fileStats && fileStats.keyword_counts && (
                    <Box>
                      <Typography variant="subtitle1" gutterBottom align="center">
                        상위 10개 키워드 분포
                      </Typography>
                      
                      <Box sx={{ height: 300 }}>
                        <Bar 
                          data={getKeywordChartData()} 
                          options={{
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                              legend: {
                                display: false,
                              },
                            },
                            scales: {
                              y: {
                                beginAtZero: true,
                              },
                            },
                          }}
                        />
                      </Box>
                      
                      <Box sx={{ mt: 3 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                          <Typography variant="subtitle2" gutterBottom>
                            키워드 통계
                          </Typography>
                          <DownloadButton 
                            fileName={selectedFile.file_name} 
                            variant="text" 
                            size="small" 
                            label="데이터 다운로드" 
                          />
                        </Box>
                        
                        <TableContainer>
                          <Table size="small">
                            <TableHead>
                              <TableRow>
                                <TableCell>키워드</TableCell>
                                <TableCell align="right">기사 수</TableCell>
                                <TableCell align="right">비율</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {fileStats.keyword_counts && Object.entries(fileStats.keyword_counts)
                                .sort((a, b) => b[1] - a[1])
                                .slice(0, 10)
                                .map(([keyword, count]) => (
                                  <TableRow key={keyword}>
                                    <TableCell>{keyword}</TableCell>
                                    <TableCell align="right">{count}</TableCell>
                                    <TableCell align="right">
                                      {Math.round((count / fileStats.total_rows) * 100)}%
                                    </TableCell>
                                  </TableRow>
                                ))}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </Box>
                    </Box>
                  )}
                </Box>
              </Paper>
            </Box>
          ) : (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <InfoOutlinedIcon color="action" sx={{ fontSize: 48, mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                파일을 선택해주세요
              </Typography>
              <Typography variant="body2" color="text.secondary">
                왼쪽 목록에서 파일을 선택하면 상세 정보와 분석 결과를 확인할 수 있습니다.
              </Typography>
            </Paper>
          )}
        </Grid>
      </Grid>
      
      {/* 미리보기 다이얼로그 */}
      <Dialog
        open={previewDialogOpen}
        onClose={handleClosePreviewDialog}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          파일 미리보기: {selectedFile?.file_name}
        </DialogTitle>
        <DialogContent dividers>
          {filePreview ? (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    {filePreview.column_names.map((column) => (
                      <TableCell key={column}>{column}</TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filePreview.preview_data.map((row, rowIndex) => (
                    <TableRow key={rowIndex}>
                      {filePreview.column_names.map((column) => (
                        <TableCell key={column}>
                          {typeof row[column] === 'boolean' ? (
                            row[column] ? '예' : '아니오'
                          ) : (
                            row[column]?.toString() || ''
                          )}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Typography>미리보기 데이터를 불러오는 중입니다...</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClosePreviewDialog}>닫기</Button>
          <DownloadButton 
            fileName={selectedFile?.file_name}
            variant="contained" 
            color="primary" 
          />
        </DialogActions>
      </Dialog>
      
      <LoadingOverlay open={loading} message="파일 정보를 불러오는 중입니다..." />
      
      {/* 다운로드 알림 */}
      <Snackbar 
        open={snackbar.open} 
        autoHideDuration={6000} 
        onClose={() => setSnackbar({...snackbar, open: false})}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={() => setSnackbar({...snackbar, open: false})} 
          severity={snackbar.severity} 
          variant="filled"
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ResultsPage;
