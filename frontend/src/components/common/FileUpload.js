import React, { useState, useRef } from 'react';
import {
  Box,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Collapse,
  IconButton
} from '@mui/material';
import {
  CloudUpload,
  CheckCircle,
  Error,
  ExpandMore,
  ExpandLess
} from '@mui/icons-material';
import uploadService from '../../api/uploadService';

const FileUpload = ({ onUploadSuccess, onUploadError }) => {
  // 파일 업로드 상태 관리
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [validationExpanded, setValidationExpanded] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);
    setUploadResult(null);

    try {
      const result = await uploadService.uploadExcelFile(file);
      
      if (result.success) {
        setUploadResult(result);
        if (onUploadSuccess) {
          onUploadSuccess(result);
        }
      } else {
        throw new Error(result.message || '파일 업로드에 실패했습니다.');
      }
    } catch (error) {
      console.error('파일 업로드 오류:', error);
      const errorResult = {
        success: false,
        message: error.message,
        validation_result: error.validation_result
      };
      setUploadResult(errorResult);
      
      if (onUploadError) {
        onUploadError(error);
      }
    } finally {
      setUploading(false);
      // 파일 입력 초기화
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const renderValidationResult = (validation) => {
    if (!validation) return null;

    return (
      <Box sx={{ mt: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <IconButton
            onClick={() => setValidationExpanded(!validationExpanded)}
            size="small"
          >
            {validationExpanded ? <ExpandLess /> : <ExpandMore />}
          </IconButton>
          <Typography variant="body2">
            파일 검증 결과 상세보기
          </Typography>
        </Box>
        
        <Collapse in={validationExpanded}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              기본 정보
            </Typography>
            <Typography variant="body2">
              총 {validation.row_count}개 행 / {validation.columns.length}개 열
            </Typography>
            
            {validation.missing_columns.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" color="error" gutterBottom>
                  누락된 필수 열
                </Typography>
                {validation.missing_columns.map(col => (
                  <Chip
                    key={col}
                    label={col}
                    color="error"
                    size="small"
                    sx={{ mr: 1, mb: 1 }}
                  />
                ))}
              </Box>
            )}
            
            {validation.available_optional_columns?.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" color="success" gutterBottom>
                  사용 가능한 선택적 열
                </Typography>
                {validation.available_optional_columns.map(col => (
                  <Chip
                    key={col}
                    label={col}
                    color="success"
                    size="small"
                    sx={{ mr: 1, mb: 1 }}
                  />
                ))}
              </Box>
            )}
            
            {validation.sample_data && validation.sample_data.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  샘플 데이터 (상위 3행)
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        {Object.keys(validation.sample_data[0]).map(key => (
                          <TableCell key={key}>{key}</TableCell>
                        ))}
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {validation.sample_data.map((row, index) => (
                        <TableRow key={index}>
                          {Object.values(row).map((value, i) => (
                            <TableCell key={i}>
                              {String(value).substring(0, 50)}
                              {String(value).length > 50 ? '...' : ''}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}
          </Paper>
        </Collapse>
      </Box>
    );
  };

  return (
    <Box>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileSelect}
        accept=".xlsx,.xls,.csv"
        style={{ display: 'none' }}
      />
      
      <Button
        variant="outlined"
        onClick={() => fileInputRef.current?.click()}
        disabled={uploading}
        startIcon={uploading ? <CircularProgress size={20} /> : <CloudUpload />}
        fullWidth
      >
        {uploading ? '업로드 중...' : '엑셀 파일 업로드'}
      </Button>
      
      <Typography variant="caption" display="block" sx={{ mt: 1, textAlign: 'center' }}>
        지원 형식: Excel (.xlsx, .xls), CSV (.csv) | 최대 50MB
      </Typography>
      
      {uploadResult && (
        <Box sx={{ mt: 2 }}>
          <Alert
            severity={uploadResult.success ? 'success' : 'error'}
            icon={uploadResult.success ? <CheckCircle /> : <Error />}
          >
            <Typography variant="body2">
              {uploadResult.message}
            </Typography>
            
            {uploadResult.success && uploadResult.validation_result && (
              <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                파일: {uploadResult.original_filename} 
                ({uploadResult.validation_result.row_count}개 행)
              </Typography>
            )}
          </Alert>
          
          {uploadResult.validation_result && 
           renderValidationResult(uploadResult.validation_result)}
        </Box>
      )}
    </Box>
  );
};

export default FileUpload;