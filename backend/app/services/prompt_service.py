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
    """통합 프롬프트 템플릿 관리 서비스"""
    
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
                self._create_default_prompts()
                logger.info("기본 프롬프트 템플릿이 생성되었습니다.")
        except Exception as e:
            logger.error(f"기본 프롬프트 로드 중 오류: {str(e)}")

    def _create_default_prompts(self):
        """기본 프롬프트 생성"""
        # 네이버 뉴스 스크랩 전문가 프롬프트
        news_scraping_prompt = PromptCreateRequest(
            name="네이버 뉴스 스크랩 전문가",
            description="네이버 뉴스 스크랩 업무 가이드에 기반한 프롬프트",
            role_definition="당신은 코스맥스의 전문 뉴스 큐레이터입니다.",
            detailed_instructions="""다음 기준에 따라 뉴스 기사를 분류하세요:
1. 자사언급기사: 코스맥스, 코스맥스엔비티 직접 언급
2. 업계관련기사: 화장품/뷰티 업계 관련
3. 건기식펫푸드관련기사: 건강기능식품, 펫푸드 관련
4. 기타: 위 범주에 해당하지 않는 내용""",
            few_shot_examples="""예시:
"코스맥스 신제품 출시" → 자사언급기사
"K뷰티 해외 진출" → 업계관련기사
"펫푸드 시장 성장" → 건기식펫푸드관련기사""",
            cot_process="1. 키워드 확인 2. 카테고리 매칭 3. 관련성 점수 계산 4. 최적 카테고리 선택",
            base_prompt="""다음 JSON 형식으로 응답하세요:
{{"category": "분류명", "confidence": 0.0-1.0, "keywords": ["키워드"]}}

제목: {title}
내용: {content}""",
            system_message="정확한 JSON 형식으로만 응답하세요."
        )
        
        # 간단한 분류 프롬프트
        simple_prompt = PromptCreateRequest(
            name="간단 뉴스 분류기",
            description="빠른 분류를 위한 간소화된 프롬프트",
            role_definition="당신은 뉴스 분류 전문가입니다.",
            detailed_instructions="4개 카테고리로 빠르게 분류하세요.",
            few_shot_examples="간단한 예시들",
            cot_process="빠른 분류 과정",
            base_prompt="기사를 분류하세요: {title} - {content}",
            system_message="간단하고 정확한 JSON으로 응답하세요."
        )
        
        # 프롬프트들 생성
        self.create_prompt(news_scraping_prompt)
        self.create_prompt(simple_prompt)
        
        # 첫 번째 프롬프트를 활성화
        prompts = self.get_all_prompts()
        if prompts:
            self.activate_prompt(prompts[0].id)
    
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
            
            prompt_id = str(uuid.uuid4())
            now = datetime.now()
            
            prompt_data = {
                "id": prompt_id,
                "name": request.name.strip(),
                "description": request.description or "",
                "role_definition": request.role_definition.strip(),
                "detailed_instructions": request.detailed_instructions or "",
                "few_shot_examples": request.few_shot_examples or "",
                "cot_process": request.cot_process or "",
                "base_prompt": request.base_prompt.strip(),
                "system_message": request.system_message or "정확한 JSON 형식으로만 응답하세요.",
                "is_active": False,
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
                    logger.info(f"프롬프트 수정 요청: {request.dict()}")
                    
                    # 기존 데이터 업데이트 - 빈 문자열도 허용
                    if request.name is not None:
                        prompt_data["name"] = request.name.strip() if request.name else ""
                    if request.description is not None:
                        prompt_data["description"] = request.description
                    if request.role_definition is not None:
                        prompt_data["role_definition"] = request.role_definition.strip() if request.role_definition else ""
                    if request.detailed_instructions is not None:
                        prompt_data["detailed_instructions"] = request.detailed_instructions
                    if request.few_shot_examples is not None:
                        prompt_data["few_shot_examples"] = request.few_shot_examples
                    if request.cot_process is not None:
                        prompt_data["cot_process"] = request.cot_process
                    if request.base_prompt is not None:
                        prompt_data["base_prompt"] = request.base_prompt.strip() if request.base_prompt else ""
                    if request.system_message is not None:
                        prompt_data["system_message"] = request.system_message
                    if request.is_active is not None:
                        if request.is_active:
                            for other_prompt in prompts_data:
                                other_prompt["is_active"] = False
                        prompt_data["is_active"] = request.is_active
                    
                    logger.info(f"수정 후 프롬프트 데이터: {prompt_data}")
                    
                    # 필수 필드 검증 - 수정 후에 확인
                    if not prompt_data.get("name") or not prompt_data.get("name").strip():
                        logger.error("프롬프트 이름은 필수입니다.")
                        return None
                    if not prompt_data.get("role_definition") or not prompt_data.get("role_definition").strip():
                        logger.error("역할 정의는 필수입니다.")
                        return None
                    if not prompt_data.get("base_prompt") or not prompt_data.get("base_prompt").strip():
                        logger.error("기본 프롬프트는 필수입니다.")
                        return None
                    
                    prompt_data["updated_at"] = datetime.now().isoformat()
                    
                    if self._save_prompts(prompts_data):
                        return PromptTemplate(**prompt_data)
                    else:
                        return None
            
            return None
            
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
            
            return False
            
        except Exception as e:
            logger.error(f"프롬프트 삭제 실패: {str(e)}")
            return False
    
    def activate_prompt(self, prompt_id: str) -> bool:
        """특정 프롬프트를 활성화"""
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
    
    def get_compiled_prompt(self, prompt_id: str, title: str = "", content: str = "") -> Optional[str]:
        """통합 프롬프트를 컴파일하여 실제 사용할 프롬프트 생성"""
        try:
            prompt = self.get_prompt_by_id(prompt_id)
            if not prompt:
                return None
            
            # 각 구성 요소를 조합하여 완전한 프롬프트 생성
            compiled_prompt = f"""## 역할 정의
{prompt.role_definition}

## 상세 지침
{prompt.detailed_instructions}

## Few-shot 예시
{prompt.few_shot_examples}

## 단계별 사고 과정
{prompt.cot_process}

## 기본 프롬프트
{prompt.base_prompt}"""
            
            # 제목과 내용이 제공된 경우 포맷팅
            if title or content:
                compiled_prompt = compiled_prompt.format(title=title, content=content)
            
            return compiled_prompt
            
        except Exception as e:
            logger.error(f"프롬프트 컴파일 실패: {str(e)}")
            return None
