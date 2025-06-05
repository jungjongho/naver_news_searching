# 진행 상황 확인 스크립트

import os
import json
from datetime import datetime

progress_dir = "/Users/mac/Desktop/jongho_project/jongho_service/naver_news_searching/backend/results/progress"

print(f"Progress directory: {progress_dir}")
print(f"Directory exists: {os.path.exists(progress_dir)}")

if os.path.exists(progress_dir):
    files = os.listdir(progress_dir)
    print(f"Progress files: {files}")
    
    for file in files:
        if file.endswith('_progress.json'):
            file_path = os.path.join(progress_dir, file)
            print(f"\n=== {file} ===")
            print(f"Last modified: {datetime.fromtimestamp(os.path.getmtime(file_path))}")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"Current: {data.get('current', 0)}")
                    print(f"Total: {data.get('total', 0)}")
                    print(f"Stage: {data.get('stage', '')}")
                    print(f"Stats: {data.get('stats', {})}")
            except Exception as e:
                print(f"Error reading file: {e}")
