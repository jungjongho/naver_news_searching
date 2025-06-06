import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import {
  Box, Typography, Button, Card, CardContent, CardActions, CardHeader,
  Grid, Chip, IconButton, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Alert, Tooltip, Accordion, AccordionSummary, AccordionDetails,
  Paper, Badge, LinearProgress, Tabs, Tab, Divider
} from '@mui/material';
import {
  Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon, FileCopy as CopyIcon,
  Visibility as PreviewIcon, CheckCircle as ActiveIcon, RadioButtonUnchecked as InactiveIcon,
  ExpandMore as ExpandMoreIcon, AutoAwesome as AutoAwesomeIcon, School as SchoolIcon,
  Analytics as AnalyticsIcon, Star as StarIcon, Person as PersonIcon,
  Assignment as AssignmentIcon, AccountTree as TreeIcon, Code as CodeIcon
} from '@mui/icons-material';
import { promptService } from '../api/promptService';

// 안정화된 TextField 컴포넌트 - 포커스 유지 및 스크롤 방지
const StableTextField = React.memo(({ label, value, onChange, required, multiline, rows, ...props }) => {
  const inputRef = useRef(null);
  const [localValue, setLocalValue] = useState(value);
  const debounceRef = useRef(null);
  const focusPositionRef = useRef({ start: 0, end: 0 });
  
  // value prop이 변경될 때만 localValue 업데이트 (무한 루프 방지)
  useEffect(() => {
    if (value !== localValue) {
      setLocalValue(value);
    }
  }, [value]);
  
  // 포커스 위치 저장
  const saveFocusPosition = useCallback(() => {
    if (inputRef.current && inputRef.current.selectionStart !== null) {
      focusPositionRef.current = {
        start: inputRef.current.selectionStart,
        end: inputRef.current.selectionEnd
      };
    }
  }, []);
  
  // 포커스 위치 복원
  const restoreFocusPosition = useCallback(() => {
    if (inputRef.current && document.activeElement === inputRef.current) {
      requestAnimationFrame(() => {
        try {
          inputRef.current.setSelectionRange(
            focusPositionRef.current.start,
            focusPositionRef.current.end
          );
        } catch (e) {
          // 에러 무시 (일부 브라우저에서 발생할 수 있음)
        }
      });
    }
  }, []);
  
  const handleChange = useCallback((e) => {
    const newValue = e.target.value;
    
    // 포커스 위치 저장
    saveFocusPosition();
    
    // 즉시 로컬 상태 업데이트
    setLocalValue(newValue);
    
    // 부모 컴포넌트로의 전달은 디바운스
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    
    debounceRef.current = setTimeout(() => {
      onChange(newValue);
      // 포커스 위치 복원
      restoreFocusPosition();
    }, 500); // 500ms 디바운스로 증가
  }, [onChange, saveFocusPosition, restoreFocusPosition]);
  
  // 포커스 이벤트 핸들러
  const handleFocus = useCallback((e) => {
    // 스크롤 방지
    e.preventDefault();
    if (props.onFocus) {
      props.onFocus(e);
    }
  }, [props.onFocus]);
  
  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);
  
  return (
    <TextField
      ref={inputRef}
      label={label}
      fullWidth
      multiline={multiline}
      rows={rows}
      value={localValue}
      onChange={handleChange}
      onFocus={handleFocus}
      onBlur={saveFocusPosition}
      required={required}
      InputProps={{
        style: { resize: 'vertical' },
        sx: {
          '& .MuiInputBase-input': {
            scrollMargin: 0,
            '&:focus': {
              scrollMarginTop: 0,
              scrollMarginBottom: 0
            }
          }
        }
      }}
      sx={{
        '& .MuiInputBase-root': {
          scrollMargin: 0,
          '&:focus-within': {
            scrollMarginTop: 0,
            scrollMarginBottom: 0
          }
        }
      }}
      {...props}
    />
  );
});

StableTextField.displayName = 'StableTextField';

const PromptsPage = () => {
  const [prompts, setPrompts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [openPreviewDialog, setOpenPreviewDialog] = useState(false);
  const [openTemplateDialog, setOpenTemplateDialog] = useState(false);
  const [dialogMode, setDialogMode] = useState('create');
  const [currentPrompt, setCurrentPrompt] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [alert, setAlert] = useState({ show: false, message: '', severity: 'info' });
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [currentTab, setCurrentTab] = useState(0);
  const [formData, setFormData] = useState({
    name: '', description: '', role_definition: '', detailed_instructions: '',
    few_shot_examples: '', cot_process: '', base_prompt: '',
    system_message: '정확한 JSON 형식으로만 응답하세요.'
  });
  
  // 스크롤 위치 및 포커스 상태 저장
  const dialogContentRef = useRef(null);
  const scrollPositionRef = useRef(0);
  const activeElementRef = useRef(null);

  const promptTemplates = {
    enhanced: {
      name: '네이버 뉴스 스크랩 전문가',
      description: '네이버 뉴스 스크랩 업무에 최적화된 통합 프롬프트',
      color: 'primary', icon: <AutoAwesomeIcon />,
      template: {
        role_definition: '당신은 코스맥스의 전문 뉴스 큐레이터입니다.',
        detailed_instructions: '다음 기준에 따라 뉴스 기사를 분류하고 평가하세요.',
        few_shot_examples: '예시: "코스맥스 신제품 출시" → 자사언급기사',
        cot_process: '1단계: 키워드 식별 → 2단계: 관련성 평가',
        base_prompt: '주어진 뉴스 기사를 분석하여 JSON으로 응답하세요.'
      }
    },
    simple: {
      name: '간단 뉴스 분류기',
      description: '빠른 분류를 위한 간소화된 프롬프트',
      color: 'success', icon: <SchoolIcon />,
      template: {
        role_definition: '당신은 뉴스 분류 전문가입니다.',
        detailed_instructions: '4개 카테고리로 분류하세요.',
        few_shot_examples: '예시: "코스맥스" → 자사언급기사',
        cot_process: '1. 키워드 확인 → 2. 카테고리 선택',
        base_prompt: '기사를 분류하세요.'
      }
    }
  };

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
    // 스크롤 위치 초기화
    scrollPositionRef.current = 0;
    activeElementRef.current = null;
    
    setDialogMode(mode);
    setCurrentTab(0);
    
    if (mode === 'edit' && prompt) {
      setCurrentPrompt(prompt);
      setFormData({
        name: prompt.name || '', description: prompt.description || '',
        role_definition: prompt.role_definition || '', detailed_instructions: prompt.detailed_instructions || '',
        few_shot_examples: prompt.few_shot_examples || '', cot_process: prompt.cot_process || '',
        base_prompt: prompt.base_prompt || '', system_message: prompt.system_message || '정확한 JSON 형식으로만 응답하세요.'
      });
    } else {
      setCurrentPrompt(null);
      setFormData({
        name: '', description: '', role_definition: '', detailed_instructions: '',
        few_shot_examples: '', cot_process: '', base_prompt: '',
        system_message: '정확한 JSON 형식으로만 응답하세요.'
      });
    }
    setOpenDialog(true);
  };

  const handleApplyTemplate = () => {
    if (selectedTemplate) {
      const template = promptTemplates[selectedTemplate];
      setFormData(prev => ({ ...prev, name: template.name, description: template.description, ...template.template }));
      setOpenTemplateDialog(false);
      setSelectedTemplate('');
      handleOpenDialog('create');
    }
  };
  
  // 스크롤 위치 저장
  const saveScrollPosition = useCallback(() => {
    if (dialogContentRef.current) {
      scrollPositionRef.current = dialogContentRef.current.scrollTop;
    }
    if (document.activeElement && document.activeElement.tagName === 'TEXTAREA') {
      activeElementRef.current = document.activeElement;
    }
  }, []);
  
  // 스크롤 위치 복원
  const restoreScrollPosition = useCallback(() => {
    if (dialogContentRef.current && scrollPositionRef.current > 0) {
      requestAnimationFrame(() => {
        dialogContentRef.current.scrollTop = scrollPositionRef.current;
      });
    }
  }, []);
  
  // 폼 데이터 변경 핸들러 (스크롤 위치 보존)
  const handleFormDataChange = useCallback((field, value) => {
    saveScrollPosition();
    setFormData(prev => ({ ...prev, [field]: value }));
    setTimeout(restoreScrollPosition, 50);
  }, [saveScrollPosition, restoreScrollPosition]);
  
  // 탭 변경 핸들러 (스크롤 위치 보존)
  const handleTabChange = useCallback((event, newValue) => {
    saveScrollPosition();
    setCurrentTab(newValue);
    setTimeout(restoreScrollPosition, 100);
  }, [saveScrollPosition, restoreScrollPosition]);

  const handleSubmit = async () => {
    try {
      if (!formData.name.trim() || !formData.role_definition.trim() || !formData.base_prompt.trim()) {
        showAlert('이름, 역할 정의, 기본 프롬프트는 필수입니다.', 'error');
        return;
      }

      if (dialogMode === 'create') {
        await promptService.createPrompt(formData);
        showAlert('프롬프트가 생성되었습니다.', 'success');
      } else {
        await promptService.updatePrompt(currentPrompt.id, formData);
        showAlert('프롬프트가 수정되었습니다.', 'success');
      }
      // 다이얼로그 닫기 전 상태 초기화
      scrollPositionRef.current = 0;
      activeElementRef.current = null;
      setOpenDialog(false);
      loadPrompts();
    } catch (error) {
      showAlert('프롬프트 저장에 실패했습니다: ' + error.message, 'error');
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
    if (window.confirm('정말로 삭제하시겠습니까?')) {
      try {
        await promptService.deletePrompt(promptId);
        showAlert('프롬프트가 삭제되었습니다.', 'success');
        loadPrompts();
      } catch (error) {
        showAlert('삭제에 실패했습니다: ' + error.message, 'error');
      }
    }
  };

  const handleDuplicate = async (promptId) => {
    try {
      const originalPrompt = prompts.find(p => p.id === promptId);
      const newName = window.prompt('복제할 프롬프트 이름:', `${originalPrompt.name} (복사본)`);
      if (newName) {
        await promptService.duplicatePrompt(promptId, newName);
        showAlert('프롬프트가 복제되었습니다.', 'success');
        loadPrompts();
      }
    } catch (error) {
      showAlert('복제에 실패했습니다: ' + error.message, 'error');
    }
  };

  const handlePreview = async (promptId) => {
    try {
      const response = await promptService.previewPrompt(promptId, '코스맥스 신제품 출시', '코스맥스가 새로운 화장품을 출시했습니다.');
      setPreviewData(response);
      setOpenPreviewDialog(true);
    } catch (error) {
      showAlert('미리보기에 실패했습니다: ' + error.message, 'error');
    }
  };

  const TabPanel = ({ children, value, index }) => (
    <div hidden={value !== index}>{value === index && <Box sx={{ pt: 2 }}>{children}</Box>}</div>
  );

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>통합 프롬프트 관리</Typography>
        <LinearProgress />
        <Typography sx={{ mt: 2, textAlign: 'center' }}>프롬프트 목록을 불러오는 중...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {alert.show && <Alert severity={alert.severity} sx={{ mb: 2 }}>{alert.message}</Alert>}

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">통합 프롬프트 관리</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" startIcon={<AutoAwesomeIcon />} onClick={() => setOpenTemplateDialog(true)}>
            템플릿에서 생성
          </Button>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpenDialog('create')}>
            새 프롬프트 생성
          </Button>
        </Box>
      </Box>

      <Paper sx={{ p: 2, mb: 3, bgcolor: 'grey.50' }}>
        <Typography variant="h6" gutterBottom>프롬프트 현황</Typography>
        <Grid container spacing={2}>
          <Grid item xs={3}><Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" color="primary">{prompts.length}</Typography>
            <Typography variant="body2" color="text.secondary">전체</Typography>
          </Box></Grid>
          <Grid item xs={3}><Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" color="success.main">{prompts.filter(p => p.is_active).length}</Typography>
            <Typography variant="body2" color="text.secondary">활성</Typography>
          </Box></Grid>
          <Grid item xs={3}><Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" color="secondary.main">{prompts.filter(p => p.name.includes('전문가')).length}</Typography>
            <Typography variant="body2" color="text.secondary">전문가</Typography>
          </Box></Grid>
          <Grid item xs={3}><Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" color="warning.main">{prompts.filter(p => p.name.includes('간단')).length}</Typography>
            <Typography variant="body2" color="text.secondary">간단</Typography>
          </Box></Grid>
        </Grid>
      </Paper>

      <Grid container spacing={3}>
        {prompts.map((prompt) => (
          <Grid item xs={12} md={6} lg={4} key={prompt.id}>
            <Card sx={{ height: '100%', border: prompt.is_active ? 2 : 1, borderColor: prompt.is_active ? 'primary.main' : 'divider' }}>
              <CardHeader
                avatar={<Badge badgeContent={<StarIcon />} color="primary"><Box sx={{ width: 24, height: 24 }} /></Badge>}
                action={<Chip icon={prompt.is_active ? <ActiveIcon /> : <InactiveIcon />} 
                         label={prompt.is_active ? "활성" : "비활성"} 
                         color={prompt.is_active ? "success" : "default"} size="small" />}
                title={<Typography variant="h6" sx={{ fontSize: '1.1rem' }}>{prompt.name}</Typography>}
                subheader={<Typography variant="caption" color="text.secondary">
                  생성: {new Date(prompt.created_at).toLocaleDateString('ko-KR')}
                </Typography>}
              />
              <CardContent sx={{ flexGrow: 1, pt: 0 }}>
                {prompt.description && <Typography variant="body2" color="text.secondary" paragraph>{prompt.description}</Typography>}
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 1 }}>
                  {prompt.role_definition && <Chip icon={<PersonIcon />} label="역할" size="small" variant="outlined" />}
                  {prompt.detailed_instructions && <Chip icon={<AssignmentIcon />} label="지침" size="small" variant="outlined" />}
                  {prompt.few_shot_examples && <Chip icon={<SchoolIcon />} label="예시" size="small" variant="outlined" />}
                  {prompt.cot_process && <Chip icon={<TreeIcon />} label="CoT" size="small" variant="outlined" />}
                </Box>
              </CardContent>
              <CardActions sx={{ justifyContent: 'space-between' }}>
                <Box>
                  <Tooltip title="미리보기"><IconButton onClick={() => handlePreview(prompt.id)} size="small"><PreviewIcon /></IconButton></Tooltip>
                  {!prompt.is_active && <Tooltip title="활성화"><IconButton onClick={() => handleActivate(prompt.id)} size="small" color="primary"><ActiveIcon /></IconButton></Tooltip>}
                </Box>
                <Box>
                  <Tooltip title="수정"><IconButton onClick={() => handleOpenDialog('edit', prompt)} size="small"><EditIcon /></IconButton></Tooltip>
                  <Tooltip title="복제"><IconButton onClick={() => handleDuplicate(prompt.id)} size="small"><CopyIcon /></IconButton></Tooltip>
                  <Tooltip title="삭제"><IconButton onClick={() => handleDelete(prompt.id)} size="small" color="error"><DeleteIcon /></IconButton></Tooltip>
                </Box>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* 템플릿 선택 다이얼로그 */}
      <Dialog open={openTemplateDialog} onClose={() => setOpenTemplateDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle><AutoAwesomeIcon color="primary" sx={{ mr: 1 }} />프롬프트 템플릿 선택</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            {Object.entries(promptTemplates).map(([key, template]) => (
              <Grid item xs={12} sm={6} key={key}>
                <Card sx={{ cursor: 'pointer', border: selectedTemplate === key ? 2 : 1, 
                           borderColor: selectedTemplate === key ? 'primary.main' : 'divider' }}
                      onClick={() => setSelectedTemplate(key)}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <Badge color={template.color}>{template.icon}</Badge>
                      <Typography variant="h6">{template.name}</Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">{template.description}</Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenTemplateDialog(false)}>취소</Button>
          <Button onClick={handleApplyTemplate} variant="contained" disabled={!selectedTemplate}>선택한 템플릿 사용</Button>
        </DialogActions>
      </Dialog>

      {/* 프롬프트 생성/수정 다이얼로그 */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="lg" fullWidth>
        <DialogTitle>{dialogMode === 'create' ? '새 통합 프롬프트 생성' : '통합 프롬프트 수정'}</DialogTitle>
        <DialogContent 
          ref={dialogContentRef} 
          sx={{ 
            position: 'relative',
            '&::-webkit-scrollbar': {
              width: '8px'
            },
            '&::-webkit-scrollbar-track': {
              background: '#f1f1f1'
            },
            '&::-webkit-scrollbar-thumb': {
              background: '#888',
              borderRadius: '4px'
            },
            scrollBehavior: 'smooth',
            overscrollBehavior: 'contain'
          }}>
          <StableTextField 
            label="프롬프트 이름" 
            value={formData.name} 
            onChange={(value) => handleFormDataChange('name', value)} 
            required 
            margin="normal"
          />
          <StableTextField 
            label="설명" 
            value={formData.description}
            onChange={(value) => handleFormDataChange('description', value)} 
            multiline 
            rows={2}
            margin="normal"
          />
          <StableTextField 
            label="시스템 메시지" 
            value={formData.system_message}
            onChange={(value) => handleFormDataChange('system_message', value)} 
            multiline 
            rows={2}
            margin="normal"
          />
          
          <Divider sx={{ my: 3 }} />
          <Typography variant="h6" gutterBottom>통합 프롬프트 구성 요소</Typography>
          
          <Tabs value={currentTab} onChange={handleTabChange}>
            <Tab icon={<PersonIcon />} label="역할 정의" iconPosition="start" />
            <Tab icon={<AssignmentIcon />} label="상세 지침" iconPosition="start" />
            <Tab icon={<SchoolIcon />} label="Few-shot 예시" iconPosition="start" />
            <Tab icon={<TreeIcon />} label="CoT 과정" iconPosition="start" />
            <Tab icon={<CodeIcon />} label="기본 프롬프트" iconPosition="start" />
          </Tabs>

          <TabPanel value={currentTab} index={0}>
            <StableTextField 
              label="역할 정의" 
              value={formData.role_definition}
              onChange={(value) => handleFormDataChange('role_definition', value)} 
              required 
              multiline 
              rows={8}
            />
          </TabPanel>
          <TabPanel value={currentTab} index={1}>
            <StableTextField 
              label="상세 지침" 
              value={formData.detailed_instructions}
              onChange={(value) => handleFormDataChange('detailed_instructions', value)} 
              multiline 
              rows={8}
            />
          </TabPanel>
          <TabPanel value={currentTab} index={2}>
            <StableTextField 
              label="Few-shot 예시" 
              value={formData.few_shot_examples}
              onChange={(value) => handleFormDataChange('few_shot_examples', value)} 
              multiline 
              rows={8}
            />
          </TabPanel>
          <TabPanel value={currentTab} index={3}>
            <StableTextField 
              label="Chain of Thought 과정" 
              value={formData.cot_process}
              onChange={(value) => handleFormDataChange('cot_process', value)} 
              multiline 
              rows={8}
            />
          </TabPanel>
          <TabPanel value={currentTab} index={4}>
            <StableTextField 
              label="기본 프롬프트" 
              value={formData.base_prompt}
              onChange={(value) => handleFormDataChange('base_prompt', value)} 
              required 
              multiline 
              rows={8}
            />
          </TabPanel>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>취소</Button>
          <Button onClick={handleSubmit} variant="contained">{dialogMode === 'create' ? '생성' : '수정'}</Button>
        </DialogActions>
      </Dialog>

      {/* 미리보기 다이얼로그 */}
      <Dialog open={openPreviewDialog} onClose={() => setOpenPreviewDialog(false)} maxWidth="lg" fullWidth>
        <DialogTitle><PreviewIcon color="primary" sx={{ mr: 1 }} />통합 프롬프트 미리보기</DialogTitle>
        <DialogContent>
          {previewData && (
            <Box>
              <Typography variant="h6" gutterBottom>프롬프트: {previewData.prompt_name}</Typography>
              {['시스템 메시지', '역할 정의', '상세 지침', 'Few-shot 예시', 'CoT 과정', '기본 프롬프트', '컴파일된 전체 프롬프트'].map((title, idx) => {
                const keys = ['system_message', 'role_definition', 'detailed_instructions', 'few_shot_examples', 'cot_process', 'base_prompt', 'compiled_prompt_preview'];
                return (
                  <Accordion key={idx} defaultExpanded={idx === 0}>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography variant="subtitle1">{title}</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Paper variant="outlined" sx={{ p: 2, bgcolor: idx === 6 ? 'primary.50' : 'grey.50' }}>
                        <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                          {previewData[keys[idx]]}
                        </Typography>
                      </Paper>
                    </AccordionDetails>
                  </Accordion>
                );
              })}
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
