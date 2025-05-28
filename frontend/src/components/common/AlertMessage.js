import React from 'react';
import { Alert, AlertTitle, Box, Collapse } from '@mui/material';

const AlertMessage = ({ open, type = 'info', title, message, onClose }) => {
  return (
    <Box sx={{ mb: 2 }}>
      <Collapse in={open}>
        <Alert 
          severity={type} 
          onClose={onClose}
          sx={{ mb: 2 }}
        >
          {title && <AlertTitle>{title}</AlertTitle>}
          {message}
        </Alert>
      </Collapse>
    </Box>
  );
};

export default AlertMessage;
