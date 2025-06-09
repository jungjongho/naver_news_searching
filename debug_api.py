#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
from urllib.parse import quote

def debug_naver_api():
    """네이버 API 상세 디버깅"""
    
    # API 키
    NAVER_CLIENT_ID = "dqtlNY89P26n73fnmQyU"
    NAVER_CLIENT_SECRET = "STF_9nBdOK"
    
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    
    # 여러 키워드로 테스트
    test_keywords = ["화장품", "삼성", "애플", "코스맥스", "뷰티"]
    
    for keyword in test_keywords:
        print(f"\n=== '{keyword}' 키워드 테스트 ===")
        
        encoded_query = quote(keyword)
        url = f"https://openapi.naver.com/v1/search/news.json?query={encoded_query}&display=10&start=1&sort=date"
        
        try:
            response = requests.get(url, headers=headers)
            
            print(f"상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                total = data.get('total', 0)
                items_count = len(data.get('items', []))
                
                print(f"검색 결과 총 개수: {total}")
                print(f"반환된 항목 수: {items_count}")
                
                if items_count > 0:
                    first_item = data['items'][0]
                    print(f"첫 번째 기사: {first_item.get('title', '').replace('<b>', '').replace('</b>', '')}")
                    print(f"발행일: {first_item.get('pubDate', '')}")
                else:
                    print("❌ 검색 결과가 없습니다!")
                    
            elif response.status_code == 429:
                print("❌ API 호출 한도 초과!")
            elif response.status_code == 401:
                print("❌ API 키 인증 실패!")
            elif response.status_code == 403:
                print("❌ 접근 권한 없음!")
            else:
                print(f"❌ API 요청 실패: {response.status_code}")
                print(f"응답 내용: {response.text}")
                
        except Exception as e:
            print(f"❌ 오류 발생: {str(e)}")
        
        print("-" * 50)

if __name__ == "__main__":
    debug_naver_api()
