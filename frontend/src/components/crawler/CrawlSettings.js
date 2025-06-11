import React from 'react';
import {
  Box,
  TextField,
  Typography,
  Divider,
  FormControl,
  FormControlLabel,
  Radio,
  RadioGroup,
  Grid,
} from '@mui/material';

import { CRAWLER_CONFIG, VALIDATION_RULES, MESSAGES } from '../../config/crawlerConfig';

const CrawlSettings = ({
  maxNewsPerKeyword,
  dateFilterType,
  days,
  startDate,
  endDate,
  onMaxNewsChange,
  onMaxNewsBlur,
  onDateFilterTypeChange,
  onDaysChange,
  onStartDateChange,
  onEndDateChange,
  getDateRangeDescription,
}) => {
  return (
    <Box>
      {/* 최대 뉴스 수 설정 */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="subtitle1" gutterBottom>
          키워드당 최대 뉴스 수
        </Typography>
        <TextField
          fullWidth
          variant="outlined"
          type="number"
          value={maxNewsPerKeyword}
          onChange={onMaxNewsChange}
          onBlur={onMaxNewsBlur}
          inputProps={{
            min: VALIDATION_RULES.MAX_NEWS.MIN,
            max: VALIDATION_RULES.MAX_NEWS.MAX,
            step: 1
          }}
          helperText={MESSAGES.HELP.MAX_NEWS}
          sx={{ mb: 2 }}
        />
        <Typography variant="body2" color="text.secondary">
          {MESSAGES.HELP.MAX_NEWS_RECOMMENDATION}
        </Typography>
      </Box>
      
      <Divider sx={{ mb: 3 }} />
      
      {/* 날짜 필터링 설정 */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="subtitle1" gutterBottom>
          날짜 필터링
        </Typography>
        
        <FormControl component="fieldset" sx={{ mb: 3 }}>
          <RadioGroup
            value={dateFilterType}
            onChange={onDateFilterTypeChange}
            row
          >
            <FormControlLabel 
              value="days" 
              control={<Radio />} 
              label="최근 일수 지정" 
            />
            <FormControlLabel 
              value="range" 
              control={<Radio />} 
              label="날짜 범위 지정" 
            />
          </RadioGroup>
        </FormControl>
        
        {dateFilterType === 'days' ? (
          <Box>
            <TextField
              fullWidth
              variant="outlined"
              type="number"
              label="최근 며 일"
              value={days}
              onChange={onDaysChange}
              inputProps={{
                min: VALIDATION_RULES.DAYS.MIN,
                max: VALIDATION_RULES.DAYS.MAX,
                step: 1
              }}
              helperText={MESSAGES.HELP.DAYS_RANGE}
              sx={{ mb: 2 }}
            />
            <Typography variant="body2" color="text.secondary">
              {getDateRangeDescription()}
            </Typography>
          </Box>
        ) : (
          <Box>
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  variant="outlined"
                  type="date"
                  label="시작 날짜"
                  value={startDate}
                  onChange={onStartDateChange}
                  InputLabelProps={{
                    shrink: true,
                  }}
                  inputProps={{
                    max: new Date().toISOString().split('T')[0]
                  }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  variant="outlined"
                  type="date"
                  label="종료 날짜"
                  value={endDate}
                  onChange={onEndDateChange}
                  InputLabelProps={{
                    shrink: true,
                  }}
                  inputProps={{
                    max: new Date().toISOString().split('T')[0],
                    min: startDate || undefined
                  }}
                />
              </Grid>
            </Grid>
            <Typography variant="body2" color="text.secondary">
              {getDateRangeDescription()}
            </Typography>
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default CrawlSettings;
