import React from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Stack,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';

import { KEYWORD_CATEGORIES } from '../../config/crawlerConfig';

const KeywordInput = ({
  keywords,
  newKeyword,
  selectedCategory,
  onNewKeywordChange,
  onKeywordInputKeyPress,
  onAddKeyword,
  onCategorySelect,
  onDeleteKeyword,
  onSaveKeywords,
  onClearAllKeywords,
}) => {
  return (
    <Box>
      {/* 키워드 입력 */}
      <Box sx={{ mb: 2 }}>
        <TextField
          fullWidth
          label="키워드 입력"
          variant="outlined"
          value={newKeyword}
          onChange={onNewKeywordChange}
          onKeyPress={onKeywordInputKeyPress}
          InputProps={{
            endAdornment: (
              <Button
                variant="contained"
                color="primary"
                onClick={onAddKeyword}
                startIcon={<AddIcon />}
                disabled={newKeyword.trim() === ''}
              >
                추가
              </Button>
            ),
          }}
        />
      </Box>
      
      {/* 추천 키워드 카테고리 */}
      <Box sx={{ mb: 3 }}>
        <FormControl fullWidth variant="outlined">
          <InputLabel>추천 키워드 카테고리</InputLabel>
          <Select
            value={selectedCategory}
            onChange={onCategorySelect}
            label="추천 키워드 카테고리"
          >
            <MenuItem value="">
              <em>카테고리 선택</em>
            </MenuItem>
            {KEYWORD_CATEGORIES.map((category) => (
              <MenuItem key={category.name} value={category.name}>
                {category.name} ({category.keywords.length}개)
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>
      
      {/* 선택된 키워드 표시 */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle1" gutterBottom>
          선택된 키워드 ({keywords.length}개)
        </Typography>
        {keywords.length > 0 ? (
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {keywords.map((keyword, index) => (
              <Chip
                key={index}
                label={keyword}
                onDelete={() => onDeleteKeyword(index)}
                color="primary"
                variant="outlined"
                sx={{ mb: 1 }}
              />
            ))}
          </Stack>
        ) : (
          <Typography variant="body2" color="text.secondary">
            아직 선택된 키워드가 없습니다. 키워드를 입력하거나 추천 카테고리를 선택해주세요.
          </Typography>
        )}
      </Box>
      
      {/* 키워드 관리 버튼 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
        <Button
          variant="outlined"
          color="primary"
          onClick={onSaveKeywords}
          disabled={keywords.length === 0}
        >
          키워드 저장
        </Button>
        
        <Button
          variant="contained"
          color="primary"
          onClick={onClearAllKeywords}
          disabled={keywords.length === 0}
        >
          모두 지우기
        </Button>
      </Box>
    </Box>
  );
};

export default KeywordInput;
