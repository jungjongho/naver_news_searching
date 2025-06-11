#!/bin/bash
# 리팩토링 적용 스크립트

echo "🚀 네이버 뉴스 검색 프로젝트 리팩토링 적용 시작..."

# 현재 디렉토리 확인
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ 오류: 프로젝트 루트 디렉토리에서 실행해주세요."
    exit 1
fi

# 백업 디렉토리 생성
echo "📦 기존 파일 백업 중..."
mkdir -p backup/$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backup/$(date +%Y%m%d_%H%M%S)"

# 백엔드 백업
cp backend/app/services/naver_api_service.py $BACKUP_DIR/naver_api_service_backup.py 2>/dev/null || echo "기존 파일 없음"
cp backend/app/api/endpoints/crawler.py $BACKUP_DIR/crawler_backup.py 2>/dev/null || echo "기존 파일 없음"

# 프론트엔드 백업
cp frontend/src/pages/CrawlerPage.js $BACKUP_DIR/CrawlerPage_backup.js 2>/dev/null || echo "기존 파일 없음"

echo "✅ 백업 완료: $BACKUP_DIR"

# 점진적 적용 옵션 제공
echo ""
echo "적용 방식을 선택해주세요:"
echo "1) 점진적 적용 (기존 코드와 병행, 권장)"
echo "2) 전체 교체 (기존 코드 완전 대체)"
read -p "선택 (1 또는 2): " choice

case $choice in
    1)
        echo "📝 점진적 적용 모드..."
        
        # 새로운 리팩토링된 서비스들은 이미 별도 파일로 생성됨
        echo "✅ 리팩토링된 파일들이 생성되었습니다."
        echo "   - backend/app/services/naver_api_service_refactored.py"
        echo "   - backend/app/api/endpoints/crawler_refactored.py"
        echo "   - frontend/src/pages/CrawlerPageRefactored.js"
        echo ""
        echo "📋 다음 단계:"
        echo "1. 백엔드: main.py에서 새로운 라우터 추가"
        echo "2. 프론트엔드: App.js에서 새로운 라우트 추가"
        echo "3. 테스트 후 기존 파일과 교체"
        ;;
    2)
        echo "🔄 전체 교체 모드..."
        
        # 백엔드 교체
        if [ -f "backend/app/services/naver_api_service_refactored.py" ]; then
            mv backend/app/services/naver_api_service.py backend/app/services/naver_api_service_old.py
            mv backend/app/services/naver_api_service_refactored.py backend/app/services/naver_api_service.py
            echo "✅ 백엔드 서비스 교체 완료"
        fi
        
        if [ -f "backend/app/api/endpoints/crawler_refactored.py" ]; then
            mv backend/app/api/endpoints/crawler.py backend/app/api/endpoints/crawler_old.py
            mv backend/app/api/endpoints/crawler_refactored.py backend/app/api/endpoints/crawler.py
            echo "✅ 백엔드 엔드포인트 교체 완료"
        fi
        
        # 프론트엔드 교체
        if [ -f "frontend/src/pages/CrawlerPageRefactored.js" ]; then
            mv frontend/src/pages/CrawlerPage.js frontend/src/pages/CrawlerPage_old.js
            mv frontend/src/pages/CrawlerPageRefactored.js frontend/src/pages/CrawlerPage.js
            echo "✅ 프론트엔드 페이지 교체 완료"
        fi
        
        echo "⚠️  주의: import 경로를 확인하고 서버를 재시작해주세요."
        ;;
    *)
        echo "❌ 잘못된 선택입니다."
        exit 1
        ;;
esac

echo ""
echo "🎉 리팩토링 적용 완료!"
echo ""
echo "📋 확인 사항:"
echo "- 백엔드 서버 재시작"
echo "- 프론트엔드 개발 서버 재시작"
echo "- API 호출 테스트"
echo "- 기능 동작 확인"
echo ""
echo "📁 백업 위치: $BACKUP_DIR"
echo "🔧 문제 발생 시 백업 파일로 롤백 가능"
