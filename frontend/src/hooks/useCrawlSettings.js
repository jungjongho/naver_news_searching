import { CRAWLER_CONFIG, VALIDATION_RULES, MESSAGES } from '../config/crawlerConfig';

/**
 * 크롤링 설정 관리 훅
 */
export const useCrawlSettings = (
  maxNewsPerKeyword,
  setMaxNewsPerKeyword,
  dateFilterType,
  setDateFilterType,
  days,
  setDays,
  startDate,
  setStartDate,
  endDate,
  setEndDate
) => {

  // 최대 뉴스 수 변경 핸들러
  const handleMaxNewsChange = (e) => {
    const value = e.target.value;
    
    // 빈 값일 때는 그대로 두기 (사용자가 입력 중일 수 있음)
    if (value === '') {
      setMaxNewsPerKeyword('');
      return;
    }
    
    const numValue = parseInt(value);
    const { MIN, MAX } = VALIDATION_RULES.MAX_NEWS;
    
    // 유효한 숫자이고 범위 내일 때만 업데이트
    if (!isNaN(numValue) && numValue >= MIN && numValue <= MAX) {
      setMaxNewsPerKeyword(numValue);
    }
  };

  // blur 이벤트에서 최소값 보장
  const handleMaxNewsBlur = () => {
    if (maxNewsPerKeyword === '' || maxNewsPerKeyword < VALIDATION_RULES.MAX_NEWS.MIN) {
      setMaxNewsPerKeyword(VALIDATION_RULES.MAX_NEWS.MIN);
    }
  };

  // 날짜 필터 타입 변경
  const handleDateFilterTypeChange = (e) => {
    setDateFilterType(e.target.value);
  };

  // 일수 변경 핸들러
  const handleDaysChange = (e) => {
    const value = parseInt(e.target.value);
    const { MIN, MAX } = VALIDATION_RULES.DAYS;
    
    if (!isNaN(value) && value >= MIN && value <= MAX) {
      setDays(value);
    }
  };

  // 시작 날짜 변경
  const handleStartDateChange = (e) => {
    setStartDate(e.target.value);
  };

  // 종료 날짜 변경
  const handleEndDateChange = (e) => {
    setEndDate(e.target.value);
  };

  // 설정 검증
  const validateSettings = () => {
    // 날짜 범위 검증
    if (dateFilterType === 'range') {
      if (!startDate || !endDate) {
        return MESSAGES.ERROR.INVALID_DATE_RANGE;
      }
      
      if (new Date(startDate) > new Date(endDate)) {
        return MESSAGES.ERROR.START_DATE_AFTER_END;
      }
    }
    
    return null; // 검증 통과
  };

  // 최종 설정값 계산
  const getFinalSettings = () => {
    const finalMaxNews = maxNewsPerKeyword === '' || maxNewsPerKeyword < 1 
      ? CRAWLER_CONFIG.DEFAULT_MAX_NEWS 
      : maxNewsPerKeyword;

    return {
      maxNewsPerKeyword: finalMaxNews,
      dateFilterType,
      days,
      startDate,
      endDate,
    };
  };

  // 표시용 최대 뉴스 수 계산
  const getDisplayMaxNews = () => {
    return maxNewsPerKeyword === '' || maxNewsPerKeyword < 1 
      ? CRAWLER_CONFIG.DEFAULT_MAX_NEWS 
      : maxNewsPerKeyword;
  };

  // 날짜 범위 설명 텍스트 생성
  const getDateRangeDescription = () => {
    if (dateFilterType === 'range') {
      return MESSAGES.HELP.DATE_RANGE_DESCRIPTION(startDate, endDate);
    } else {
      return MESSAGES.HELP.DAYS_DESCRIPTION(days);
    }
  };

  return {
    // 이벤트 핸들러
    handleMaxNewsChange,
    handleMaxNewsBlur,
    handleDateFilterTypeChange,
    handleDaysChange,
    handleStartDateChange,
    handleEndDateChange,
    
    // 유틸리티 함수
    validateSettings,
    getFinalSettings,
    getDisplayMaxNews,
    getDateRangeDescription,
  };
};
