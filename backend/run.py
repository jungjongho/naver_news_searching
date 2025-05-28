#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uvicorn
import os
import sys

# 현재 디렉토리를 PYTHONPATH에 추가하여 어디서든 가져올 수 있게 함
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
