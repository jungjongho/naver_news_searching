import React from 'react';
import { Backdrop, CircularProgress, Typography, Box } from '@mui/material';

const LoadingOverlay = ({ open, message = '로딩 중...' }) => {
  return (
    <Backdrop
      sx={{
        color: '#fff',
        zIndex: (theme) => theme.zIndex.drawer + 1,
        flexDirection: 'column',
      }}
      open={open}
    >
      <CircularProgress color="inherit" size={60} />
      <Box mt={2}>
        <Typography variant="h6">{message}</Typography>
      </Box>
    </Backdrop>
  );
};

export default LoadingOverlay;
