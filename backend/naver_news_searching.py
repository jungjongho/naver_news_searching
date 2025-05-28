import requests
import datetime
from urllib.parse import quote
import pandas as pd
import os
import sys
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def search_news(keyword):
    # .env 파일에서 API 키 로드
    CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
    CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')
    
    # API 키가 설정되어 있는지 확인
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError("NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET이 .env 파일에 설정되어 있지 않습니다.")

    # 검색어 및 날짜 조건
    today = datetime.datetime.now()
    three_days_ago = today - datetime.timedelta(days=3)

    # 인코딩된 키워드
    encoded_query = quote(keyword)

    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET
    }

    all_news = []
    for start in range(1, 1000, 100):  # 최대 1000개까지 가능
        url = f"https://openapi.naver.com/v1/search/news.json?query={encoded_query}&display=100&start={start}&sort=date"
        
        try:
            res = requests.get(url, headers=headers)
            res.raise_for_status()  # HTTP 오류 확인
            
            data = res.json()
            items = data.get("items", [])
            
            if not items:
                break
                
            for item in items:
                pub_date = datetime.datetime.strptime(item['pubDate'], "%a, %d %b %Y %H:%M:%S +0900")
                if pub_date >= three_days_ago:
                    # HTML 태그 제거
                    title = item['title'].replace("<b>", "").replace("</b>", "")
                    description = item['description'].replace("<b>", "").replace("</b>", "")
                    
                    all_news.append({
                        "title": title,
                        "link": item['link'],
                        "pubDate": pub_date,
                        "description": description
                    })
                else:
                    # 더 이전 뉴스가 나오기 시작하면 종료
                    return all_news
            
            # 날짜 조건에 맞는 뉴스만 수집 후, 100개 미만이면 다음 페이지 없음
            if len(items) < 100:
                break
                
        except requests.exceptions.RequestException as e:
            print(f"API 요청 오류: {e}")
            break
            
    return all_news

def save_to_excel(news_data, keyword):
    if not news_data:
        print("저장할 뉴스 데이터가 없습니다.")
        return
        
    # 현재 날짜를 파일명에 포함
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    file_name = f"{keyword}_news_{today_str}.xlsx"
    
    # 현재 스크립트 경로
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, file_name)
    
    # DataFrame 변환
    df = pd.DataFrame(news_data)
    
    # 날짜 포맷 변환
    df['pubDate'] = df['pubDate'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # 컬럼명 한글로 변경
    df.columns = ['제목', '링크', '발행일시', '내용']
    
    # 엑셀 파일로 저장
    try:
        df.to_excel(file_path, index=False, engine='openpyxl')
        # print(f"뉴스 데이터가 '{file_path}'에 성공적으로 저장되었습니다.")
        # print(f"총 {len(news_data)}개의 뉴스 기사가 저장되었습니다.")
        return file_path
    except Exception as e:
        print(f"엑셀 파일 저장 중 오류 발생: {e}")
        return None

def main():
    # 명령줄 인수로 키워드 받기 또는 기본값 사용
    if len(sys.argv) > 1:
        keyword = sys.argv[1]
    else:
        keyword = input("검색할 키워드를 입력하세요: ")
    
    print(f"'{keyword}' 키워드로 최근 3일간의 뉴스를 검색합니다...")
    
    try:
        # 뉴스 검색
        news_data = search_news(keyword)
        
        if news_data:
            print(f"총 {len(news_data)}개의 뉴스 기사를 찾았습니다.")
            
            # 엑셀로 저장
            save_to_excel(news_data, keyword)
        else:
            print(f"'{keyword}'에 대한 최근 3일간의 뉴스 기사를 찾을 수 없습니다.")
    except ValueError as e:
        print(f"오류: {e}")
        print("환경 변수 설정 방법:")
        print("1. 프로젝트 폴더에 .env 파일을 생성하세요.")
        print("2. 다음 내용을 추가하세요:")
        print("   NAVER_CLIENT_ID=발급받은클라이언트ID")
        print("   NAVER_CLIENT_SECRET=발급받은클라이언트시크릿")

if __name__ == "__main__":
    main()