import React from 'react';
import { Box, Typography, Divider, Breadcrumbs, Link as MuiLink } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

const PageTitle = ({ title, subtitle, breadcrumbs = [], action }) => {
  return (
    <Box sx={{ mb: 4 }}>
      {/* 브레드크럼 */}
      {breadcrumbs.length > 0 && (
        <Breadcrumbs aria-label="breadcrumb" sx={{ mb: 2 }}>
          <MuiLink component={RouterLink} to="/" underline="hover" color="inherit">
            홈
          </MuiLink>
          {breadcrumbs.map((crumb, index) => {
            const isLast = index === breadcrumbs.length - 1;
            return isLast ? (
              <Typography key={index} color="text.primary">
                {crumb.text}
              </Typography>
            ) : (
              <MuiLink
                key={index}
                component={RouterLink}
                to={crumb.path}
                underline="hover"
                color="inherit"
              >
                {crumb.text}
              </MuiLink>
            );
          })}
        </Breadcrumbs>
      )}

      {/* 제목 영역 */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
        <Typography variant="h4" component="h1" fontWeight="bold">
          {title}
        </Typography>
        {action && <Box>{action}</Box>}
      </Box>

      {/* 부제목 */}
      {subtitle && (
        <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 2 }}>
          {subtitle}
        </Typography>
      )}

      <Divider sx={{ mt: 1, mb: 3 }} />
    </Box>
  );
};

export default PageTitle;
