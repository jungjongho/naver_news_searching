# naver_api_service.py에 추가할 개선된 search_news 메서드

def search_news_improved(self, keyword: str, max_news: int = 100, sort: str = "date", days: int = 30, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
    """개선된 네이버 뉴스 검색 (상세 디버깅 포함)"""
    logger.info(f"Searching news for keyword: {keyword}")
    
    # 날짜 범위 설정
    start_date_obj = None
    end_date_obj = None
    
    if start_date:
        try:
            start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            logger.warning(f"잘못된 시작 날짜 형식: {start_date}")
    
    if end_date:
        try:
            end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59)
        except ValueError:
            logger.warning(f"잘못된 종료 날짜 형식: {end_date}")
    
    # 날짜 범위가 설정되지 않았으면 days 파라미터 사용
    if not start_date_obj and not end_date_obj:
        today = datetime.datetime.now()
        start_date_obj = today - datetime.timedelta(days=days)
    
    encoded_query = quote(keyword)
    all_news = []
    
    display = min(100, max_news)
    
    for start in range(1, min(1001, max_news + 1), display):
        remaining = max_news - len(all_news)
        if remaining <= 0:
            break
        
        current_display = min(display, remaining)
        url = f"https://openapi.naver.com/v1/search/news.json?query={encoded_query}&display={current_display}&start={start}&sort={sort}"
        
        try:
            res = requests.get(url, headers=self.headers)
            
            # 상세한 응답 로깅
            logger.info(f"API 응답 상태: {res.status_code}")
            
            if res.status_code == 429:
                logger.error("API 호출 한도 초과 - 잠시 후 다시 시도하세요")
                break
            elif res.status_code == 401:
                logger.error("API 키 인증 실패")
                break
            elif res.status_code == 403:
                logger.error("API 접근 권한 없음")
                break
            elif res.status_code != 200:
                logger.error(f"API 요청 실패: {res.status_code}, 응답: {res.text}")
                break
            
            res.raise_for_status()
            
            data = res.json()
            items = data.get("items", [])
            total = data.get("total", 0)
            
            logger.info(f"키워드 '{keyword}': 총 {total}개 중 {len(items)}개 반환")
            
            if not items:
                logger.warning(f"키워드 '{keyword}'에 대한 검색 결과가 없습니다")
                break
            
            for item in items:
                processed_item = self._process_news_item(item, keyword, start_date_obj, end_date_obj)
                if processed_item:
                    all_news.append(processed_item)
                elif processed_item is None and 'pubDate' in item:
                    # 날짜 범위를 벗어났으면 검색 종료 (정렬이 날짜순인 경우)
                    if sort == "date":
                        break
            
            if len(items) < current_display or len(all_news) >= max_news:
                break
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API 요청 오류: {str(e)}")
            break
    
    logger.info(f"Found {len(all_news)} news items for keyword: {keyword}")
    
    # 결과가 없을 때 더 상세한 정보 제공
    if not all_news:
        logger.warning(f"키워드 '{keyword}'에 대한 뉴스를 찾을 수 없습니다. 다음을 확인해보세요:")
        logger.warning("1. API 할당량 초과 여부")
        logger.warning("2. 키워드 철자 확인")
        logger.warning("3. 날짜 범위 확대 (현재: 최근 30일)")
    
    return all_news
