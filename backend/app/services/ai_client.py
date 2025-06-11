#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AI 클라이언트 팩토리 및 관리
- LLM API 호출 로그 기능 추가
"""

import logging
from typing import Dict, Any, Optional, Protocol
from openai import OpenAI
import anthropic
from app.common.exceptions import APIKeyError, AnalysisError

logger = logging.getLogger(__name__)


class AIClient(Protocol):
    """AI 클라이언트 인터페이스"""
    
    def analyze(self, prompt: str, **kwargs) -> str:
        """텍스트 분석"""
        ...


class OpenAIClient:
    """OpenAI 클라이언트 래퍼"""
    
    MODEL_MAPPING = {
        'gpt-4.1': 'gpt-4.1',
        'gpt-4.1-mini': 'gpt-4.1-mini',
        'gpt-4.1-nano': 'gpt-4.1-nano',
        'gpt-3.5-turbo': 'gpt-3.5-turbo',
        'gpt-4': 'gpt-4',
        'gpt-4o': 'gpt-4o',
        'gpt-4o-mini': 'gpt-4o-mini',
        'gpt-4-turbo': 'gpt-4-turbo-preview',
    }
    
    def __init__(self, api_key: str):
        try:
            self.client = OpenAI(api_key=api_key, timeout=30.0)
            # API 키 유효성 검증
            logger.info("OpenAI API 키 유효성 검증 중...")
            models = self.client.models.list()
            logger.info(f"OpenAI 클라이언트 초기화 완료 - 사용 가능한 모델 수: {len(models.data)}")
        except Exception as e:
            logger.error(f"OpenAI 클라이언트 초기화 실패: {str(e)}")
            raise APIKeyError(f"OpenAI API 키가 유효하지 않습니다: {str(e)}")
    
    def analyze(self, prompt: str, model: str = "gpt-4.1-nano", batch_size: int = 1, **kwargs) -> str:
        """텍스트 분석"""
        import datetime
        import os
        
        try:
            actual_model = self.MODEL_MAPPING.get(model, model)
            logger.info(f"OpenAI 분석 시작 - 요청 모델: {model}, 실제 모델: {actual_model}")
            
            # 배치 크기에 따른 동적 max_tokens 설정 (증가)
            if batch_size > 1:
                default_max_tokens = min(batch_size * 1500 + 3000, 40000)  # 배치 처리용 (증가)
            else:
                default_max_tokens = 3000  # 단일 처리용 (증가)
            
            # LLM 호출 로그 기록
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"\n\n{'='*80}\n"
            log_entry += f"[{timestamp}] LLM API 호출\n"
            log_entry += f"{'='*80}\n"
            log_entry += f"모델: {actual_model}\n"
            log_entry += f"프롬프트 길이: {len(prompt)}문자\n"
            log_entry += f"배치 크기: {batch_size}\n"
            log_entry += f"max_tokens: {kwargs.get('max_tokens', default_max_tokens)}\n"
            log_entry += f"\n--- 프롬프트 내용 ---\n"
            log_entry += prompt
            log_entry += f"\n--- 프롬프트 끝 ---\n"
            
            response = self.client.chat.completions.create(
                model=actual_model,
                messages=[
                    {"role": "system", "content": "당신은 화장품 업계 전문 분석가입니다. 반드시 유효한 JSON 형식으로만 응답하세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=kwargs.get('temperature', 0.1),
                max_tokens=kwargs.get('max_tokens', default_max_tokens)
            )
            
            result = response.choices[0].message.content.strip()
            logger.info(f"OpenAI 분석 완료 - 응답 길이: {len(result)}문자")
            logger.debug(f"OpenAI 응답 내용: {result}")
            
            # LLM 응답 로그 기록
            log_entry += f"\n--- LLM 응답 ---\n"
            log_entry += result
            log_entry += f"\n--- 응답 끝 ---\n"
            log_entry += f"응답 길이: {len(result)}문자\n"
            
            # 로그 파일에 기록
            try:
                # 백엔드 폴더에 log.txt 파일 생성
                backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                log_file_path = os.path.join(backend_dir, "llm_log.txt")
                
                with open(log_file_path, "a", encoding="utf-8") as f:
                    f.write(log_entry)
                    f.flush()  # 즉시 파일에 쓰기
                
                logger.debug(f"LLM 로그 기록: {log_file_path}")
                
            except Exception as log_error:
                logger.warning(f"LLM 로그 기록 실패: {log_error}")
            
            return result
            
        except Exception as e:
            logger.error(f"OpenAI 분석 실패 - 모델: {model}, 오류: {str(e)}")
            
            # 오류도 로그에 기록
            try:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                error_log = f"\n\n{'='*80}\n"
                error_log += f"[{timestamp}] LLM API 오류\n"
                error_log += f"{'='*80}\n"
                error_log += f"오류: {str(e)}\n"
                
                backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                log_file_path = os.path.join(backend_dir, "llm_log.txt")
                
                with open(log_file_path, "a", encoding="utf-8") as f:
                    f.write(error_log)
                    f.flush()
                    
            except Exception as log_error:
                logger.warning(f"LLM 오류 로그 기록 실패: {log_error}")
            
            raise AnalysisError(f"OpenAI 분석 중 오류가 발생했습니다: {str(e)}")


class AnthropicClient:
    """Anthropic Claude 클라이언트 래퍼"""
    
    MODEL_MAPPING = {
        'claude-instant-1': 'claude-instant-1',
        'claude-2': 'claude-2',
        'claude-3-sonnet': 'claude-3-sonnet-20240229',
        'claude-3-opus': 'claude-3-opus-20240229'
    }
    
    def __init__(self, api_key: str):
        try:
            self.client = anthropic.Anthropic(api_key=api_key)
            logger.info("Anthropic 클라이언트 초기화 완료")
        except Exception as e:
            logger.error(f"Anthropic 클라이언트 초기화 실패: {str(e)}")
            raise APIKeyError(f"Anthropic API 키가 유효하지 않습니다: {str(e)}")
    
    def analyze(self, prompt: str, model: str = "claude-instant-1", **kwargs) -> str:
        """텍스트 분석"""
        try:
            actual_model = self.MODEL_MAPPING.get(model, model)
            
            response = self.client.messages.create(
                model=actual_model,
                max_tokens=kwargs.get('max_tokens', 500),
                temperature=kwargs.get('temperature', 0.1),
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Anthropic 분석 실패: {str(e)}")
            raise AnalysisError(f"Anthropic 분석 중 오류가 발생했습니다: {str(e)}")


class AIClientFactory:
    """AI 클라이언트 팩토리"""
    
    @staticmethod
    def create_client(model: str, api_key: str) -> AIClient:
        """모델에 따라 적절한 클라이언트 생성"""
        if model.startswith("gpt"):
            return OpenAIClient(api_key)
        elif model.startswith("claude"):
            return AnthropicClient(api_key)
        else:
            raise AnalysisError(f"지원하지 않는 모델입니다: {model}")
    
    @staticmethod
    def get_available_models() -> Dict[str, list]:
        """사용 가능한 모델 목록 반환"""
        return {
            "openai": list(OpenAIClient.MODEL_MAPPING.keys()),
            "anthropic": list(AnthropicClient.MODEL_MAPPING.keys())
        }
