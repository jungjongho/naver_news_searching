import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
  IconButton,
} from '@mui/material';
import KeyboardArrowRightIcon from '@mui/icons-material/KeyboardArrowRight';

const SavedKeywords = ({ savedKeywords, onLoadSavedKeyword }) => {
  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          저장된 키워드
        </Typography>
        
        {savedKeywords.length > 0 ? (
          <List dense>
            {savedKeywords.map((keyword, index) => (
              <ListItem
                key={index}
                secondaryAction={
                  <IconButton
                    edge="end"
                    onClick={() => onLoadSavedKeyword(keyword)}
                    size="small"
                  >
                    <KeyboardArrowRightIcon />
                  </IconButton>
                }
              >
                <ListItemText primary={keyword} />
              </ListItem>
            ))}
          </List>
        ) : (
          <Typography variant="body2" color="text.secondary">
            저장된 키워드가 없습니다. 자주 사용하는 키워드를 저장하면 빠르게 접근할 수 있습니다.
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};

export default SavedKeywords;
