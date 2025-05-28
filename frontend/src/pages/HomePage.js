import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Grid,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import CalculateIcon from '@mui/icons-material/Calculate';
import TableViewIcon from '@mui/icons-material/TableView';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';

const HomePage = () => {
  const navigate = useNavigate();

  return (
    <Box>
      {/* 헤더 섹션 */}
      <Paper
        elevation={0}
        sx={{
          p: 4,
          mb: 4,
          borderRadius: 2,
          backgroundColor: (theme) => theme.palette.primary.main,
          color: 'white',
        }}
      >
        <Typography variant="h3" component="h1" gutterBottom>
          네이버 뉴스 스크래퍼
        </Typography>
        <Typography variant="h6" sx={{ mb: 3 }}>
          키워드 기반 뉴스 수집 및 관련성 평가를 위한 웹 애플리케이션
        </Typography>
        <Button
          variant="contained"
          color="secondary"
          size="large"
          onClick={() => navigate('/crawler')}
          sx={{ mr: 2 }}
        >
          뉴스 수집 시작하기
        </Button>
        <Button
          variant="outlined"
          color="inherit"
          size="large"
          onClick={() => navigate('/results')}
        >
          결과 보기
        </Button>
      </Paper>

      {/* 기능 카드 섹션 */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flexGrow: 1 }}>
              <Box display="flex" justifyContent="center" mb={2}>
                <SearchIcon fontSize="large" color="primary" />
              </Box>
              <Typography variant="h5" component="h2" gutterBottom align="center">
                뉴스 수집
              </Typography>
              <Typography variant="body1" color="text.secondary">
                네이버 뉴스에서 키워드 기반으로 최신 뉴스 기사를 검색하고 수집합니다. 
                수집된 뉴스는 CSV 파일로 저장되어 향후 분석에 활용할 수 있습니다.
              </Typography>
            </CardContent>
            <CardActions>
              <Button 
                fullWidth 
                variant="outlined" 
                color="primary"
                onClick={() => navigate('/crawler')}
              >
                뉴스 수집하기
              </Button>
            </CardActions>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flexGrow: 1 }}>
              <Box display="flex" justifyContent="center" mb={2}>
                <CalculateIcon fontSize="large" color="primary" />
              </Box>
              <Typography variant="h5" component="h2" gutterBottom align="center">
                관련성 평가
              </Typography>
              <Typography variant="body1" color="text.secondary">
                수집된 뉴스 기사의 적합성을 OpenAI API를 사용하여 평가합니다.
                LLM을 통해 화장품 업계와의 연관성을 판단하고 카테고리를 분류합니다.
              </Typography>
            </CardContent>
            <CardActions>
              <Button 
                fullWidth 
                variant="outlined" 
                color="primary"
                onClick={() => navigate('/relevance')}
              >
                관련성 평가하기
              </Button>
            </CardActions>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flexGrow: 1 }}>
              <Box display="flex" justifyContent="center" mb={2}>
                <TableViewIcon fontSize="large" color="primary" />
              </Box>
              <Typography variant="h5" component="h2" gutterBottom align="center">
                결과 확인
              </Typography>
              <Typography variant="body1" color="text.secondary">
                수집 및 평가된 뉴스 기사의 결과를 확인하고 분석합니다.
                카테고리별 통계를 시각화하고 CSV 파일로 다운로드할 수 있습니다.
              </Typography>
            </CardContent>
            <CardActions>
              <Button 
                fullWidth 
                variant="outlined" 
                color="primary"
                onClick={() => navigate('/results')}
              >
                결과 확인하기
              </Button>
            </CardActions>
          </Card>
        </Grid>
      </Grid>

      {/* 주요 특징 섹션 */}
      <Paper sx={{ p: 3, borderRadius: 2 }}>
        <Typography variant="h5" gutterBottom>
          주요 특징
        </Typography>
        <List>
          <ListItem>
            <ListItemIcon>
              <CheckCircleOutlineIcon color="success" />
            </ListItemIcon>
            <ListItemText 
              primary="키워드 기반 뉴스 크롤링" 
              secondary="다양한 키워드로 네이버 뉴스 검색 결과를 자동으로 수집합니다." 
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <CheckCircleOutlineIcon color="success" />
            </ListItemIcon>
            <ListItemText 
              primary="LLM 기반 관련성 평가" 
              secondary="OpenAI API를 활용하여 뉴스 기사의 적합성과 카테고리를 자동으로 분류합니다." 
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <CheckCircleOutlineIcon color="success" />
            </ListItemIcon>
            <ListItemText 
              primary="데이터 시각화" 
              secondary="수집된 데이터를 다양한 차트로 시각화하여 분석을 용이하게 합니다." 
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <CheckCircleOutlineIcon color="success" />
            </ListItemIcon>
            <ListItemText 
              primary="CSV 파일 내보내기" 
              secondary="분석 결과를 CSV 파일로 내보내 엑셀 등에서 활용할 수 있습니다." 
            />
          </ListItem>
        </List>
      </Paper>
    </Box>
  );
};

export default HomePage;
