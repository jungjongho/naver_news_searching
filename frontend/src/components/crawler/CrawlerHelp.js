import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import { CheckCircle } from '@mui/icons-material';

const CrawlerHelp = () => {
  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          도움말
        </Typography>
        
        <List dense>
          <ListItem>
            <ListItemIcon>
              <HelpOutlineIcon color="primary" fontSize="small" />
            </ListItemIcon>
            <ListItemText
              primary="여러 키워드 검색"
              secondary="다양한 키워드를 동시에 검색할 수 있습니다. 각 키워드는 독립적으로 검색됩니다."
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <HelpOutlineIcon color="primary" fontSize="small" />
            </ListItemIcon>
            <ListItemText
              primary="최대 뉴스 수"
              secondary="키워드당 최대 뉴스 수를 자유롭게 입력할 수 있습니다. 1부터 1000까지 가능합니다."
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <HelpOutlineIcon color="primary" fontSize="small" />
            </ListItemIcon>
            <ListItemText
              primary="추천 카테고리"
              secondary="미리 정의된 추천 카테고리를 사용하여 빠르게 키워드를 추가할 수 있습니다."
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <HelpOutlineIcon color="primary" fontSize="small" />
            </ListItemIcon>
            <ListItemText
              primary="날짜 필터링"
              secondary="최근 일수 또는 직접 날짜 범위를 지정하여 원하는 기간의 뉴스만 검색할 수 있습니다."
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <CheckCircle color="success" fontSize="small" />
            </ListItemIcon>
            <ListItemText
              primary="결과 저장"
              secondary="크롤링 결과는 자동으로 저장되며, 다운로드 폴더에도 복사됩니다. '결과 목록' 페이지에서도 확인할 수 있습니다."
            />
          </ListItem>
        </List>
      </CardContent>
    </Card>
  );
};

export default CrawlerHelp;
