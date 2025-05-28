import React from 'react';
import { Button, Tooltip } from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import { downloadFile } from '../../api/downloadService';

/**
 * 파일 다운로드 버튼 컴포넌트
 * @param {string} fileName - 다운로드할 파일 이름
 * @param {string} variant - 버튼 스타일 (contained, outlined, text)
 * @param {string} color - 버튼 색상 (primary, secondary, error, etc.)
 * @param {string} label - 버튼 텍스트 (기본값: '다운로드')
 * @param {object} buttonProps - 추가 버튼 속성
 */
const DownloadButton = ({
  fileName,
  variant = 'contained',
  color = 'primary',
  label = '다운로드',
  ...buttonProps
}) => {
  const handleDownload = () => {
    if (!fileName) {
      console.error('다운로드할 파일 이름이 제공되지 않았습니다.');
      return;
    }

    downloadFile(fileName);
  };

  return (
    <Tooltip title={`${fileName} 다운로드`} arrow>
      <Button
        variant={variant}
        color={color}
        startIcon={<DownloadIcon />}
        onClick={handleDownload}
        {...buttonProps}
      >
        {label}
      </Button>
    </Tooltip>
  );
};

export default DownloadButton;
