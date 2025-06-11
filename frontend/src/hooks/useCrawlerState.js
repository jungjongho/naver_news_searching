import { useState, useEffect } from 'react';
import { CRAWLER_CONFIG } from '../config/crawlerConfig';
import { storage } from '../utils/helpers';

/**
 * 크롤러 상태 관리 훅
 */
export const useCrawlerState = () => {
  // 키워드 관련 상태
  const [keywords, setKeywords] = useState([]);
  const [newKeyword, setNewKeyword] = useState('');
  const [savedKeywords, setSavedKeywords] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  
  // 크롤링 설정 상태
  const [maxNewsPerKeyword, setMaxNewsPerKeyword] = useState(CRAWLER_CONFIG.DEFAULT_MAX_NEWS);
  const [dateFilterType, setDateFilterType] = useState(CRAWLER_CONFIG.DEFAULT_DATE_FILTER_TYPE);
  const [days, setDays] = useState(CRAWLER_CONFIG.DEFAULT_DAYS);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  
  // UI 상태
  const [loading, setLoading] = useState(false);
  const [alert, setAlert] = useState({ open: false, type: 'info', message: '' });

  // 초기 데이터 로드
  useEffect(() => {
    loadSavedData();
  }, []);

  const loadSavedData = () => {
    const { STORAGE_KEYS } = CRAWLER_CONFIG;
    
    // 저장된 키워드 로드
    const saved = storage.get(STORAGE_KEYS.SAVED_KEYWORDS, []);
    setSavedKeywords(saved);
    
    // 마지막 설정 로드
    const lastKeywords = storage.get(STORAGE_KEYS.LAST_KEYWORDS, []);
    const lastMaxNews = storage.get(STORAGE_KEYS.LAST_MAX_NEWS, CRAWLER_CONFIG.DEFAULT_MAX_NEWS);
    const lastDateFilterType = storage.get(STORAGE_KEYS.LAST_DATE_FILTER_TYPE, CRAWLER_CONFIG.DEFAULT_DATE_FILTER_TYPE);
    const lastDays = storage.get(STORAGE_KEYS.LAST_DAYS, CRAWLER_CONFIG.DEFAULT_DAYS);
    const lastStartDate = storage.get(STORAGE_KEYS.LAST_START_DATE, '');
    const lastEndDate = storage.get(STORAGE_KEYS.LAST_END_DATE, '');
    
    if (lastKeywords.length > 0) {
      setKeywords(lastKeywords);
    }
    setMaxNewsPerKeyword(lastMaxNews);
    setDateFilterType(lastDateFilterType);
    setDays(lastDays);
    setStartDate(lastStartDate);
    setEndDate(lastEndDate);
  };

  const saveCurrentSettings = () => {
    const { STORAGE_KEYS } = CRAWLER_CONFIG;
    const finalMaxNews = maxNewsPerKeyword === '' || maxNewsPerKeyword < 1 ? 
      CRAWLER_CONFIG.DEFAULT_MAX_NEWS : maxNewsPerKeyword;
    
    storage.set(STORAGE_KEYS.LAST_KEYWORDS, keywords);
    storage.set(STORAGE_KEYS.LAST_MAX_NEWS, finalMaxNews);
    storage.set(STORAGE_KEYS.LAST_DATE_FILTER_TYPE, dateFilterType);
    storage.set(STORAGE_KEYS.LAST_DAYS, days);
    storage.set(STORAGE_KEYS.LAST_START_DATE, startDate);
    storage.set(STORAGE_KEYS.LAST_END_DATE, endDate);
  };

  const showAlert = (type, message) => {
    setAlert({ open: true, type, message });
    setTimeout(() => {
      setAlert(prev => ({ ...prev, open: false }));
    }, 3000);
  };

  const closeAlert = () => {
    setAlert(prev => ({ ...prev, open: false }));
  };

  return {
    // 상태
    keywords,
    newKeyword,
    savedKeywords,
    selectedCategory,
    maxNewsPerKeyword,
    dateFilterType,
    days,
    startDate,
    endDate,
    loading,
    alert,
    
    // 상태 설정 함수
    setKeywords,
    setNewKeyword,
    setSavedKeywords,
    setSelectedCategory,
    setMaxNewsPerKeyword,
    setDateFilterType,
    setDays,
    setStartDate,
    setEndDate,
    setLoading,
    
    // 유틸리티 함수
    saveCurrentSettings,
    loadSavedData,
    showAlert,
    closeAlert,
  };
};
