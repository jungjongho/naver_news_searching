#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AI 클라이언트 팩토리 및 관리
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
            self.client.models.list()
            logger.info("OpenAI 클라이언트 초기화 완료")
        except Exception as e:
            logger.error(f"OpenAI 클라이언트 초기화 실패: {str(e)}")
            raise APIKeyError(f"OpenAI API 키가 유효하지 않습니다: {str(e)}")
    
    def analyze(self, prompt: str, model: str = "gpt-4.1-nano", **kwargs) -> str:
        """텍스트 분석"""
        try:
            actual_model = self.MODEL_MAPPING.get(model, model)
            
            response = self.client.chat.completions.create(
                model=actual_model,
                messages=[
                    {"role": "system", "content": "당신은 화장품 업계 전문 분석가입니다. 반드시 유효한 JSON 형식으로만 응답하세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=kwargs.get('temperature', 0.1),
                max_tokens=kwargs.get('max_tokens', 500)
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI 분석 실패: {str(e)}")
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
