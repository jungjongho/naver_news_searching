#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

from app.models.schemas import PromptTemplate, PromptCreateRequest, PromptUpdateRequest
from app.core.config import settings

logger = logging.getLogger(__name__)


class PromptService:
    """
    프롬프트 템플릿 관리 서비스
    JSON 파일 기반으로 프롬프트를 저장하고 관리합니다.
    """
    
    def __init__(self):
        self.prompts_file = os.path.join(settings.RESULTS_PATH, "prompts.json")
        self._ensure_prompts_file()
        self._load_default_prompts()
    
    def _ensure_prompts_file(self):
        """프롬프트 파일이 존재하지 않으면 생성"""
        if not os.path.exists(self.prompts_file):
            os.makedirs(os.path.dirname(self.prompts_file), exist_ok=True)
            with open(self.prompts_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
    
    def _load_default_prompts(self):
        """기본 프롬프트 템플릿 로드"""
        try:
            prompts = self.get_all_prompts()
            if not prompts:
                # 기본 프롬프트 생성
                default_prompt = PromptCreateRequest(
                    name="코스맥스 뉴스 관련성 분석 (기본)",
                    description="코스맥스 관련 뉴스 기사의 관련성을 분석하는 기본 프롬프트입니다.",
                    batch_prompt="""코스맥스 뉴스 관련성 분석. 각 기사를 다음 기준으로 분류:

1=자사언급: 코스맥스 직접 언급
2=업계관련: 화장품/뷰티 업계 동향, 경쟁사, 기술, 규제
3=건기식펫푸드: 건강기능식품, 펫푸드 관련
4=기타: 관련성 낮음

JSON 배열로 응답:
[{{"id":1,"relevant":true,"category":"자사언급","confidence":0.9,"reason":"간단한이유"}}]

기사들:
{articles}""",
                    single_prompt="""코스맥스 관련성 분석.

분류: 1=자사언급, 2=업계관련, 3=건기식펫푸드, 4=기타

JSON 응답:
{{"relevant":true,"category":"분류","confidence":0.8,"reason":"이유"}}

제목: {title}
내용: {content}""",
                    system_message="JSON 형식으로만 응답하세요."
                )
                self.create_prompt(default_prompt)
                logger.info("기본 프롬프트 템플릿이 생성되었습니다.")
        except Exception as e:
            logger.error(f"기본 프롬프트 로드 중 오류: {str(e)}")
    
    def _load_prompts(self) -> List[Dict[str, Any]]:
        """JSON 파일에서 프롬프트 목록 로드"""
        try:
            with open(self.prompts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"프롬프트 파일 로드 실패: {str(e)}")
            return []
    
    def _save_prompts(self, prompts: List[Dict[str, Any]]) -> bool:
        """JSON 파일에 프롬프트 목록 저장"""
        try:
            with open(self.prompts_file, 'w', encoding='utf-8') as f:
                json.dump(prompts, f, ensure_ascii=False, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"프롬프트 파일 저장 실패: {str(e)}")
            return False
    
    def get_all_prompts(self) -> List[PromptTemplate]:
        """모든 프롬프트 템플릿 조회"""
        try:
            prompts_data = self._load_prompts()
            prompts = []
            for prompt_data in prompts_data:
                try:
                    prompt = PromptTemplate(**prompt_data)
                    prompts.append(prompt)
                except Exception as e:
                    logger.warning(f"프롬프트 파싱 오류: {str(e)}")
                    continue
            return prompts
        except Exception as e:
            logger.error(f"프롬프트 목록 조회 실패: {str(e)}")
            return []
    
    def get_prompt_by_id(self, prompt_id: str) -> Optional[PromptTemplate]:
        """ID로 프롬프트 템플릿 조회"""
        try:
            prompts = self.get_all_prompts()
            for prompt in prompts:
                if prompt.id == prompt_id:
                    return prompt
            return None
        except Exception as e:
            logger.error(f"프롬프트 조회 실패: {str(e)}")
            return None
    
    def get_active_prompt(self) -> Optional[PromptTemplate]:
        """활성화된 프롬프트 템플릿 조회"""
        try:
            prompts = self.get_all_prompts()
            for prompt in prompts:
                if prompt.is_active:
                    return prompt
            
            # 활성화된 프롬프트가 없으면 첫 번째 프롬프트를 반환
            if prompts:
                return prompts[0]
            
            return None
        except Exception as e:
            logger.error(f"활성 프롬프트 조회 실패: {str(e)}")
            return None
    
    def create_prompt(self, request: PromptCreateRequest) -> Optional[PromptTemplate]:
        """새 프롬프트 템플릿 생성"""
        try:
            prompts_data = self._load_prompts()
            
            # 새 프롬프트 생성
            prompt_id = str(uuid.uuid4())
            now = datetime.now()
            
            prompt_data = {
                "id": prompt_id,
                "name": request.name,
                "description": request.description,
                "batch_prompt": request.batch_prompt,
                "single_prompt": request.single_prompt,
                "system_message": request.system_message or "JSON 형식으로만 응답하세요.",
                "is_active": False,  # 새로 생성된 프롬프트는 기본적으로 비활성
                "created_at": now.isoformat(),
                "updated_at": now.isoformat()
            }
            
            prompts_data.append(prompt_data)
            
            if self._save_prompts(prompts_data):
                return PromptTemplate(**prompt_data)
            else:
                return None
                
        except Exception as e:
            logger.error(f"프롬프트 생성 실패: {str(e)}")
            return None
    
    def update_prompt(self, prompt_id: str, request: PromptUpdateRequest) -> Optional[PromptTemplate]:
        """프롬프트 템플릿 수정"""
        try:
            prompts_data = self._load_prompts()
            
            for i, prompt_data in enumerate(prompts_data):
                if prompt_data.get("id") == prompt_id:
                    # 기존 데이터 업데이트
                    if request.name is not None:
                        prompt_data["name"] = request.name
                    if request.description is not None:
                        prompt_data["description"] = request.description
                    if request.batch_prompt is not None:
                        prompt_data["batch_prompt"] = request.batch_prompt
                    if request.single_prompt is not None:
                        prompt_data["single_prompt"] = request.single_prompt
                    if request.system_message is not None:
                        prompt_data["system_message"] = request.system_message
                    if request.is_active is not None:
                        # 새로운 프롬프트를 활성화하는 경우, 다른 프롬프트들은 비활성화
                        if request.is_active:
                            for other_prompt in prompts_data:
                                other_prompt["is_active"] = False
                        prompt_data["is_active"] = request.is_active
                    
                    prompt_data["updated_at"] = datetime.now().isoformat()
                    
                    if self._save_prompts(prompts_data):
                        return PromptTemplate(**prompt_data)
                    else:
                        return None
            
            return None  # 프롬프트를 찾지 못함
            
        except Exception as e:
            logger.error(f"프롬프트 수정 실패: {str(e)}")
            return None
    
    def delete_prompt(self, prompt_id: str) -> bool:
        """프롬프트 템플릿 삭제"""
        try:
            prompts_data = self._load_prompts()
            
            for i, prompt_data in enumerate(prompts_data):
                if prompt_data.get("id") == prompt_id:
                    prompts_data.pop(i)
                    return self._save_prompts(prompts_data)
            
            return False  # 프롬프트를 찾지 못함
            
        except Exception as e:
            logger.error(f"프롬프트 삭제 실패: {str(e)}")
            return False
    
    def activate_prompt(self, prompt_id: str) -> bool:
        """특정 프롬프트를 활성화 (다른 프롬프트들은 비활성화)"""
        try:
            prompts_data = self._load_prompts()
            found = False
            
            for prompt_data in prompts_data:
                if prompt_data.get("id") == prompt_id:
                    prompt_data["is_active"] = True
                    prompt_data["updated_at"] = datetime.now().isoformat()
                    found = True
                else:
                    prompt_data["is_active"] = False
            
            if found:
                return self._save_prompts(prompts_data)
            else:
                return False
                
        except Exception as e:
            logger.error(f"프롬프트 활성화 실패: {str(e)}")
            return False
    
    def duplicate_prompt(self, prompt_id: str, new_name: Optional[str] = None) -> Optional[PromptTemplate]:
        """프롬프트 템플릿 복제"""
        try:
            original_prompt = self.get_prompt_by_id(prompt_id)
            if not original_prompt:
                return None
            
            # 복제 요청 생성
            duplicate_request = PromptCreateRequest(
                name=new_name or f"{original_prompt.name} (복사본)",
                description=f"복사본: {original_prompt.description}" if original_prompt.description else None,
                batch_prompt=original_prompt.batch_prompt,
                single_prompt=original_prompt.single_prompt,
                system_message=original_prompt.system_message
            )
            
            return self.create_prompt(duplicate_request)
            
        except Exception as e:
            logger.error(f"프롬프트 복제 실패: {str(e)}")
            return None
