import React, { useState } from 'react';
import { 
  Button, 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  List, 
  ListItem, 
  ListItemText, 
  Checkbox, 
  Typography,
  Box,
  Divider
} from '@mui/material';
import CloudDownloadIcon from '@mui/icons-material/CloudDownload';
import { downloadFile } from '../../api/downloadService';

/**
 * 여러 파일을 선택하여 일괄 다운로드할 수 있는 버튼 컴포넌트
 * @param {Array} files - 다운로드 가능한 파일 목록
 * @param {string} variant - 버튼 스타일 (contained, outlined, text)
 * @param {string} color - 버튼 색상 (primary, secondary, error, etc.)
 * @param {string} label - 버튼 텍스트 (기본값: '일괄 다운로드')
 * @param {object} buttonProps - 추가 버튼 속성
 */
const BulkDownloadButton = ({
  files = [],
  variant = 'contained',
  color = 'primary',
  label = '일괄 다운로드',
  ...buttonProps
}) => {
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState([]);

  const handleOpen = () => {
    setOpen(true);
    setSelected([]);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleToggle = (file) => {
    const currentIndex = selected.findIndex(item => item.file_name === file.file_name);
    const newSelected = [...selected];

    if (currentIndex === -1) {
      newSelected.push(file);
    } else {
      newSelected.splice(currentIndex, 1);
    }

    setSelected(newSelected);
  };

  const handleSelectAll = () => {
    if (selected.length === files.length) {
      setSelected([]);
    } else {
      setSelected([...files]);
    }
  };

  const handleDownload = () => {
    // 일괄 다운로드 수행
    if (selected.length === 0) return;

    // 약간의 간격을 두고 파일 다운로드 시작
    selected.forEach((file, index) => {
      setTimeout(() => {
        downloadFile(file.file_name);
      }, index * 1000); // 각 파일 다운로드 사이에 1초 간격
    });

    handleClose();
  };

  return (
    <>
      <Button
        variant={variant}
        color={color}
        startIcon={<CloudDownloadIcon />}
        onClick={handleOpen}
        disabled={files.length === 0}
        {...buttonProps}
      >
        {label}
      </Button>

      <Dialog
        open={open}
        onClose={handleClose}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle>파일 일괄 다운로드</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            다운로드할 파일을 선택해주세요. 선택한 파일들은 순차적으로 다운로드됩니다.
          </Typography>
          
          <Box sx={{ mt: 2, mb: 2 }}>
            <Button 
              variant="outlined" 
              size="small"
              onClick={handleSelectAll}
            >
              {selected.length === files.length ? '전체 해제' : '전체 선택'}
            </Button>
          </Box>
          
          <Divider />
          
          <List sx={{ width: '100%', maxHeight: 300, overflow: 'auto' }}>
            {files.map((file) => {
              const isChecked = selected.some(item => item.file_name === file.file_name);
              
              return (
                <ListItem 
                  key={file.file_name} 
                  dense 
                  button 
                  onClick={() => handleToggle(file)}
                >
                  <Checkbox
                    edge="start"
                    checked={isChecked}
                    tabIndex={-1}
                    disableRipple
                  />
                  <ListItemText 
                    primary={file.file_name}
                    secondary={`${file.file_size_str} - ${file.modified_time_str}`}
                  />
                </ListItem>
              );
            })}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>취소</Button>
          <Button 
            onClick={handleDownload} 
            color="primary"
            variant="contained" 
            disabled={selected.length === 0}
          >
            {`${selected.length}개 파일 다운로드`}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default BulkDownloadButton;
