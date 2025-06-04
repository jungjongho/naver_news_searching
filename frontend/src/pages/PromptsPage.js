// src/pages/PromptsPage.js
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Grid,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Switch,
  Alert,
  Tooltip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  Paper
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  FileCopy as CopyIcon,
  Visibility as PreviewIcon,
  CheckCircle as ActiveIcon,
  RadioButtonUnchecked as InactiveIcon,
  ExpandMore as ExpandMoreIcon
} from '@mui/icons-material';
import { promptService } from '../api/promptService';

const PromptsPage = () => {
  const [prompts, setPrompts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [openPreviewDialog, setOpenPreviewDialog] = useState(false);
  const [dialogMode, setDialogMode] = useState('create'); // 'create' or 'edit'
  const [currentPrompt, setCurrentPrompt] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [alert, setAlert] = useState({ show: false, message: '', severity: 'info' });
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    batch_prompt: '',
    single_prompt: '',
    system_message: 'JSON 형식으로만 응답하세요.'
  });

  useEffect(() => {
    loadPrompts();
  }, []);

  const loadPrompts = async () => {
    try {
      setLoading(true);
      const response = await promptService.getAllPrompts();
      setPrompts(response.prompts || []);
    } catch (error) {
      showAlert('프롬프트 목록을 불러오는데 실패했습니다: ' + error.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const showAlert = (message, severity = 'info') => {
    setAlert({ show: true, message, severity });
    setTimeout(() => setAlert({ show: false, message: '', severity: 'info' }), 5000);
  };

  const handleOpenDialog = (mode, prompt = null) => {
    setDialogMode(mode);
    if (mode === 'edit' && prompt) {
      setCurrentPrompt(prompt);
      setFormData({
        name: prompt.name || '',
        description: prompt.description || '',
        batch_prompt: prompt.batch_prompt || '',
        single_prompt: prompt.single_prompt || '',
        system_message: prompt.system_message || 'JSON 형식으로만 응답하세요.'
      });
    } else {
      setCurrentPrompt(null);
      setFormData({
        name: '',
        description: '',
        batch_prompt: '',
        single_prompt: '',
        system_message: 'JSON 형식으로만 응답하세요.'
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setCurrentPrompt(null);
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = async () => {
    try {
      if (!formData.name.trim()) {
        showAlert('프롬프트 이름을 입력해주세요.', 'error');
        return;
      }
      if (!formData.batch_prompt.trim()) {
        showAlert('배치 프롬프트를 입력해주세요.', 'error');
        return;
      }
      if (!formData.single_prompt.trim()) {
        showAlert('단일 프롬프트를 입력해주세요.', 'error');
        return;
      }

      if (dialogMode === 'create') {
        await promptService.createPrompt(formData);
        showAlert('프롬프트가 성공적으로 생성되었습니다.', 'success');
      } else {
        await promptService.updatePrompt(currentPrompt.id, formData);
        showAlert('프롬프트가 성공적으로 수정되었습니다.', 'success');
      }

      handleCloseDialog();
      loadPrompts();
    } catch (error) {
      showAlert(`프롬프트 ${dialogMode === 'create' ? '생성' : '수정'}에 실패했습니다: ` + error.message, 'error');
    }
  };

  const handleActivate = async (promptId) => {
    try {
      await promptService.activatePrompt(promptId);
      showAlert('프롬프트가 활성화되었습니다.', 'success');
      loadPrompts();
    } catch (error) {
      showAlert('프롬프트 활성화에 실패했습니다: ' + error.message, 'error');
    }
  };

  const handleDelete = async (promptId) => {
    if (window.confirm('정말로 이 프롬프트를 삭제하시겠습니까?')) {
      try {
        await promptService.deletePrompt(promptId);
        showAlert('프롬프트가 삭제되었습니다.', 'success');
        loadPrompts();
      } catch (error) {
        showAlert('프롬프트 삭제에 실패했습니다: ' + error.message, 'error');
      }
    }
  };

  const handleDuplicate = async (promptId) => {
    try {
      const originalPrompt = prompts.find(p => p.id === promptId);
      const newName = prompt(`복제할 프롬프트의 이름을 입력하세요:`, `${originalPrompt.name} (복사본)`);
      if (newName) {
        await promptService.duplicatePrompt(promptId, newName);
        showAlert('프롬프트가 복제되었습니다.', 'success');
        loadPrompts();
      }
    } catch (error) {
      showAlert('프롬프트 복제에 실패했습니다: ' + error.message, 'error');
    }
  };

  const handlePreview = async (promptId) => {
    try {
      const response = await promptService.previewPrompt(promptId, '코스맥스 신제품 출시', '코스맥스가 새로운 화장품 라인을 출시했다고 발표했습니다.');
      setPreviewData(response);
      setOpenPreviewDialog(true);
    } catch (error) {
      showAlert('프롬프트 미리보기에 실패했습니다: ' + error.message, 'error');
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <Typography>프롬프트 목록을 불러오는 중...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {alert.show && (
        <Alert severity={alert.severity} sx={{ mb: 2 }}>
          {alert.message}
        </Alert>
      )}

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          프롬프트 관리
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog('create')}
        >
          새 프롬프트 생성
        </Button>
      </Box>

      <Grid container spacing={3}>
        {prompts.map((prompt) => (
          <Grid item xs={12} md={6} lg={4} key={prompt.id}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <Typography variant="h6" component="h2" sx={{ flexGrow: 1 }}>
                    {prompt.name}
                  </Typography>
                  {prompt.is_active ? (
                    <Chip
                      icon={<ActiveIcon />}
                      label="활성"
                      color="success"
                      size="small"
                    />
                  ) : (
                    <Chip
                      icon={<InactiveIcon />}
                      label="비활성"
                      color="default"
                      size="small"
                    />
                  )}
                </Box>

                {prompt.description && (
                  <Typography variant="body2" color="text.secondary" paragraph>
                    {prompt.description}
                  </Typography>
                )}

                <Typography variant="caption" color="text.secondary">
                  생성일: {new Date(prompt.created_at).toLocaleDateString('ko-KR')}
                </Typography>
                {prompt.updated_at !== prompt.created_at && (
                  <Typography variant="caption" color="text.secondary" display="block">
                    수정일: {new Date(prompt.updated_at).toLocaleDateString('ko-KR')}
                  </Typography>
                )}
              </CardContent>

              <CardActions>
                <Tooltip title="미리보기">
                  <IconButton onClick={() => handlePreview(prompt.id)} size="small">
                    <PreviewIcon />
                  </IconButton>
                </Tooltip>
                
                {!prompt.is_active && (
                  <Tooltip title="활성화">
                    <IconButton onClick={() => handleActivate(prompt.id)} size="small" color="primary">
                      <ActiveIcon />
                    </IconButton>
                  </Tooltip>
                )}

                <Tooltip title="수정">
                  <IconButton onClick={() => handleOpenDialog('edit', prompt)} size="small">
                    <EditIcon />
                  </IconButton>
                </Tooltip>

                <Tooltip title="복제">
                  <IconButton onClick={() => handleDuplicate(prompt.id)} size="small">
                    <CopyIcon />
                  </IconButton>
                </Tooltip>

                <Tooltip title="삭제">
                  <IconButton onClick={() => handleDelete(prompt.id)} size="small" color="error">
                    <DeleteIcon />
                  </IconButton>
                </Tooltip>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* 프롬프트 생성/수정 다이얼로그 */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {dialogMode === 'create' ? '새 프롬프트 생성' : '프롬프트 수정'}
        </DialogTitle>
        <DialogContent>
          <TextField
            label="프롬프트 이름"
            fullWidth
            margin="normal"
            value={formData.name}
            onChange={(e) => handleInputChange('name', e.target.value)}
            required
          />
          
          <TextField
            label="설명"
            fullWidth
            margin="normal"
            multiline
            rows={2}
            value={formData.description}
            onChange={(e) => handleInputChange('description', e.target.value)}
          />

          <TextField
            label="시스템 메시지"
            fullWidth
            margin="normal"
            value={formData.system_message}
            onChange={(e) => handleInputChange('system_message', e.target.value)}
            helperText="LLM에게 전달할 시스템 메시지입니다."
          />

          <TextField
            label="배치 처리용 프롬프트"
            fullWidth
            margin="normal"
            multiline
            rows={8}
            value={formData.batch_prompt}
            onChange={(e) => handleInputChange('batch_prompt', e.target.value)}
            helperText="여러 기사를 한 번에 처리할 때 사용할 프롬프트입니다. {articles} 플레이스홀더를 포함해야 합니다."
            required
          />

          <TextField
            label="단일 기사용 프롬프트"
            fullWidth
            margin="normal"
            multiline
            rows={6}
            value={formData.single_prompt}
            onChange={(e) => handleInputChange('single_prompt', e.target.value)}
            helperText="단일 기사를 처리할 때 사용할 프롬프트입니다. {title}과 {content} 플레이스홀더를 포함해야 합니다."
            required
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>취소</Button>
          <Button onClick={handleSubmit} variant="contained">
            {dialogMode === 'create' ? '생성' : '수정'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* 프롬프트 미리보기 다이얼로그 */}
      <Dialog open={openPreviewDialog} onClose={() => setOpenPreviewDialog(false)} maxWidth="lg" fullWidth>
        <DialogTitle>프롬프트 미리보기</DialogTitle>
        <DialogContent>
          {previewData && (
            <Box>
              <Typography variant="h6" gutterBottom>
                프롬프트: {previewData.prompt_name}
              </Typography>
              
              <Accordion defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="subtitle1">시스템 메시지</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                      {previewData.system_message}
                    </Typography>
                  </Paper>
                </AccordionDetails>
              </Accordion>

              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="subtitle1">단일 기사용 프롬프트</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                      {previewData.single_prompt_preview}
                    </Typography>
                  </Paper>
                </AccordionDetails>
              </Accordion>

              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="subtitle1">배치 처리용 프롬프트</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                      {previewData.batch_prompt_preview}
                    </Typography>
                  </Paper>
                </AccordionDetails>
              </Accordion>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenPreviewDialog(false)}>닫기</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PromptsPage;
