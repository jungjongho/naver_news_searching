import React from 'react';
import { Box, Typography, Link } from '@mui/material';

const Footer = () => {
  return (
    <Box 
      component="footer" 
      sx={{ 
        py: 2, 
        mt: 'auto',
        backgroundColor: (theme) => theme.palette.grey[100],
        borderTop: '1px solid',
        borderColor: 'divider'
      }}
    >
      <Typography 
        variant="body2" 
        color="text.secondary" 
        align="center"
      >
        {'© '}
        {new Date().getFullYear()}
        {' 네이버 뉴스 스크래퍼 | '}
        <Link 
          color="inherit" 
          href="https://github.com"
          target="_blank"
          rel="noopener noreferrer"
        >
          GitHub
        </Link>
      </Typography>
    </Box>
  );
};

export default Footer;
