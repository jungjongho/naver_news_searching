import { CRAWLER_CONFIG, KEYWORD_CATEGORIES } from '../config/crawlerConfig';
import { storage, removeDuplicates } from '../utils/helpers';

/**
 * 키워드 관리 훅
 */
export const useKeywordManager = (
  keywords, 
  setKeywords, 
  newKeyword, 
  setNewKeyword,
  savedKeywords,
  setSavedKeywords,
  selectedCategory,
  setSelectedCategory,
  showAlert
) => {
  
  // 키워드 추가
  const handleAddKeyword = () => {
    if (newKeyword.trim() === '') return;
    
    const updatedKeywords = [...keywords, newKeyword.trim()];
    setKeywords(removeDuplicates(updatedKeywords));
    setNewKeyword('');
  };

  // 키워드 삭제
  const handleDeleteKeyword = (index) => {
    const updatedKeywords = [...keywords];
    updatedKeywords.splice(index, 1);
    setKeywords(updatedKeywords);
  };

  // 카테고리 선택 시 키워드 추가
  const handleCategorySelect = (event) => {
    const category = event.target.value;
    setSelectedCategory(category);
    
    if (category) {
      const categoryItem = KEYWORD_CATEGORIES.find(item => item.name === category);
      if (categoryItem) {
        const updatedKeywords = [...keywords, ...categoryItem.keywords];
        setKeywords(removeDuplicates(updatedKeywords));
      }
    }
  };

  // 키워드 저장
  const handleSaveKeywords = () => {
    if (keywords.length === 0) return;
    
    const updatedSavedKeywords = removeDuplicates([...savedKeywords, ...keywords]);
    setSavedKeywords(updatedSavedKeywords);
    storage.set(CRAWLER_CONFIG.STORAGE_KEYS.SAVED_KEYWORDS, updatedSavedKeywords);
    
    showAlert('success', '키워드가 저장되었습니다.');
  };

  // 저장된 키워드 불러오기
  const handleLoadSavedKeyword = (keyword) => {
    if (!keywords.includes(keyword)) {
      const updatedKeywords = [...keywords, keyword];
      setKeywords(updatedKeywords);
    }
  };

  // 모든 키워드 삭제
  const handleClearAllKeywords = () => {
    setKeywords([]);
  };

  // Enter 키 처리
  const handleKeywordInputKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleAddKeyword();
    }
  };

  return {
    handleAddKeyword,
    handleDeleteKeyword,
    handleCategorySelect,
    handleSaveKeywords,
    handleLoadSavedKeyword,
    handleClearAllKeywords,
    handleKeywordInputKeyPress,
  };
};
