// 크롤러 관련 설정 및 상수

export const CRAWLER_CONFIG = {
  // 최대값 제한
  MAX_NEWS_PER_KEYWORD: 1000,
  MIN_NEWS_PER_KEYWORD: 1,
  MAX_KEYWORDS: 50,
  MAX_KEYWORD_LENGTH: 100,
  MAX_DAYS: 365,
  MIN_DAYS: 1,
  
  // 기본값
  DEFAULT_MAX_NEWS: 100,
  DEFAULT_DAYS: 30,
  DEFAULT_SORT: 'date',
  DEFAULT_DATE_FILTER_TYPE: 'days',
  
  // 로컬스토리지 키
  STORAGE_KEYS: {
    SAVED_KEYWORDS: 'savedKeywords',
    LAST_KEYWORDS: 'lastKeywords',
    LAST_MAX_NEWS: 'lastMaxNews',
    LAST_DATE_FILTER_TYPE: 'lastDateFilterType',
    LAST_DAYS: 'lastDays',
    LAST_START_DATE: 'lastStartDate',
    LAST_END_DATE: 'lastEndDate',
  },
  
  // 추천값
  RECOMMENDED_MAX_NEWS: [50, 100, 200, 300, 500],
  RECOMMENDED_DAYS: [7, 30, 90, 180, 365],
};

// 추천 키워드 카테고리
export const KEYWORD_CATEGORIES = [
  {
    name: '화장품',
    keywords: [
      '코스맥스', '코스맥스엔비티', '콜마', 'HK이노엔', 
      '아모레퍼시픽', 'LG생활건강', '올리브영', '화장품', '뷰티'
    ],
  },
  {
    name: '건강기능식품',
    keywords: ['건강기능식품', '펫푸드', '마이크로바이옴', '식품의약품안전처'],
  },
];

// 날짜 필터 타입
export const DATE_FILTER_TYPES = {
  DAYS: 'days',
  RANGE: 'range',
};

// 정렬 옵션
export const SORT_OPTIONS = {
  DATE: 'date',
  RELEVANCE: 'sim',
};

// 검증 규칙
export const VALIDATION_RULES = {
  KEYWORD: {
    MIN_LENGTH: 1,
    MAX_LENGTH: 100,
    INVALID_CHARS: /[<>:"/\\|?*]/,
  },
  MAX_NEWS: {
    MIN: 1,
    MAX: 1000,
  },
  DAYS: {
    MIN: 1,
    MAX: 365,
  },
};

// 메시지
export const MESSAGES = {
  SUCCESS: {
    KEYWORDS_SAVED: '키워드가 저장되었습니다.',
    CRAWL_COMPLETE: (count) => `${count}개의 뉴스 기사를 성공적으로 수집했습니다.`,
    DOWNLOAD_SAVED: (path) => `결과 파일이 다운로드 폴더에 자동으로 저장되었습니다: ${path}`,
  },
  ERROR: {
    NO_KEYWORDS: '최소 1개 이상의 키워드를 입력해주세요.',
    INVALID_DATE_RANGE: '날짜 범위를 선택할 때는 시작 날짜와 종료 날짜를 모두 입력해주세요.',
    START_DATE_AFTER_END: '시작 날짜는 종료 날짜보다 이전이어야 합니다.',
    CRAWL_FAILED: (message) => `뉴스 수집에 실패했습니다: ${message}`,
    UNEXPECTED_ERROR: (message) => `오류가 발생했습니다: ${message}`,
  },
  HELP: {
    MAX_NEWS: '1부터 1000까지 입력 가능합니다. (네이버 API 제한)',
    MAX_NEWS_RECOMMENDATION: '권장값: 100-300개 (너무 많으면 처리 시간이 오래 걸릴 수 있습니다)',
    DAYS_RANGE: '1부터 365일까지 설정 가능합니다.',
    DAYS_DESCRIPTION: (days) => `최근 ${days}일 내의 뉴스를 검색합니다.`,
    DATE_RANGE_DESCRIPTION: (start, end) => 
      start && end ? `${start}부터 ${end}까지의 뉴스를 검색합니다.` : '시작 날짜와 종료 날짜를 모두 선택해주세요.',
  },
};
