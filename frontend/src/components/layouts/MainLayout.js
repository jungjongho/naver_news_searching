import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Box,
  CssBaseline,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Container,
  useMediaQuery,
  useTheme,
  Button
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import HomeIcon from '@mui/icons-material/Home';
import SearchIcon from '@mui/icons-material/Search';
import CalculateIcon from '@mui/icons-material/Calculate';
import TableViewIcon from '@mui/icons-material/TableView';
import FilterListIcon from '@mui/icons-material/FilterList';
import EditIcon from '@mui/icons-material/Edit';
import Footer from './Footer';
import { useAuth } from '../../contexts/AuthContext';

const drawerWidth = 240;

// 메뉴 항목 정의
const menuItems = [
  { text: '홈', path: '/', icon: <HomeIcon /> },
  { text: '뉴스 수집', path: '/crawler', icon: <SearchIcon /> },
  { text: '중복 제거', path: '/deduplication', icon: <FilterListIcon /> },
  { text: '관련성 평가', path: '/relevance', icon: <CalculateIcon /> },
  { text: '결과 목록', path: '/results', icon: <TableViewIcon /> },
  { text: '프롬프트 관리', path: '/prompts', icon: <EditIcon /> },
];

const MainLayout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileOpen, setMobileOpen] = useState(false);

  // 인증 관련 추가
  const { isAuthenticated, user, logout } = useAuth();


  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleNavigation = (path) => {
    navigate(path);
    if (isMobile) {
      setMobileOpen(false);
    }
  };

  // 로그아웃 핸들러 추가
  const handleLogout = () => {
    logout();
    navigate('/login');
  };
  

  // 현재 페이지 제목 가져오기
  const getPageTitle = () => {
    const currentRoute = menuItems.find(item => item.path === location.pathname);
    return currentRoute ? currentRoute.text : '네이버 뉴스 스크래퍼';
  };

  // 사이드바 컨텐츠
  const drawer = (
    <div>
      <Toolbar 
        sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          py: 1
        }}
      >
        <Typography variant="h6" noWrap component="div">
          뉴스 스크래퍼
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => handleNavigation(item.path)}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </div>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      
      {/* 앱 바 */}
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${drawerWidth}px)` },
          ml: { md: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div">
            {getPageTitle()}
          </Typography>

          {/* 🔐 인증 UI 추가 - 오른쪽 끝에 배치 */}
          <Box sx={{ ml: 'auto' }}>
            {isAuthenticated ? (
              <Box display="flex" alignItems="center" gap={2}>
                <Typography variant="body2" sx={{ display: { xs: 'none', sm: 'block' } }}>
                  {user?.name}님 환영합니다
                </Typography>
                <Button color="inherit" onClick={handleLogout}>
                  로그아웃
                </Button>
              </Box>
            ) : (
              <Button color="inherit" onClick={() => navigate('/login')}>
                로그인
              </Button>
            )}
          </Box>
        </Toolbar>
      </AppBar>

      {/* 사이드바 */}
      <Box
        component="nav"
        sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
        aria-label="navigation menu"
      >
        {/* 모바일 드로어 */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // 모바일 성능 향상
          }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        
        {/* 데스크톱 드로어 */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      {/* 메인 컨텐츠 */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - ${drawerWidth}px)` },
          display: 'flex',
          flexDirection: 'column',
          minHeight: '100vh',
        }}
      >
        <Toolbar /> {/* 앱 바 아래 공간 확보 */}
        <Container maxWidth="xl" sx={{ flexGrow: 1, py: 2 }}>
          <Outlet />
        </Container>
        <Footer />
      </Box>
    </Box>
  );
};

export default MainLayout;
