#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging

from app.models.schemas import (
    PromptTemplate, PromptCreateRequest, PromptUpdateRequest, 
    PromptListResponse, PromptResponse
)
from app.services.prompt_service import PromptService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/prompts",
    tags=["prompts"],
    responses={404: {"description": "Not found"}},
)

prompt_service = PromptService()


@router.get("/", response_model=PromptListResponse)
async def get_all_prompts():
    """
    모든 통합 프롬프트 템플릿 조회
    """
    try:
        prompts = prompt_service.get_all_prompts()
        return PromptListResponse(
            prompts=prompts,
            total=len(prompts)
        )
    except Exception as e:
        logger.error(f"프롬프트 목록 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"프롬프트 목록 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/active", response_model=PromptResponse)
async def get_active_prompt():
    """
    현재 활성화된 통합 프롬프트 템플릿 조회
    """
    try:
        prompt = prompt_service.get_active_prompt()
        if not prompt:
            return PromptResponse(
                success=False,
                message="활성화된 프롬프트가 없습니다.",
                errors={"prompt_error": "No active prompt found"}
            )
        
        return PromptResponse(
            success=True,
            message="활성화된 프롬프트를 조회했습니다.",
            prompt=prompt
        )
    except Exception as e:
        logger.error(f"활성 프롬프트 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"활성 프롬프트 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt_by_id(prompt_id: str):
    """
    ID로 특정 통합 프롬프트 템플릿 조회
    """
    try:
        prompt = prompt_service.get_prompt_by_id(prompt_id)
        if not prompt:
            return PromptResponse(
                success=False,
                message="해당 ID의 프롬프트를 찾을 수 없습니다.",
                errors={"prompt_error": "Prompt not found"}
            )
        
        return PromptResponse(
            success=True,
            message="프롬프트를 조회했습니다.",
            prompt=prompt
        )
    except Exception as e:
        logger.error(f"프롬프트 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"프롬프트 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/", response_model=PromptResponse)
async def create_prompt(request: PromptCreateRequest):
    """
    새 통합 프롬프트 템플릿 생성
    """
    try:
        # 필수 필드 검증
        if not request.name or not request.name.strip():
            return PromptResponse(
                success=False,
                message="프롬프트 이름은 필수 입력항목입니다.",
                errors={"validation_error": "Name is required"}
            )
        if not request.role_definition or not request.role_definition.strip():
            return PromptResponse(
                success=False,
                message="역할 정의는 필수 입력항목입니다.",
                errors={"validation_error": "Role definition is required"}
            )
        if not request.base_prompt or not request.base_prompt.strip():
            return PromptResponse(
                success=False,
                message="기본 프롬프트는 필수 입력항목입니다.",
                errors={"validation_error": "Base prompt is required"}
            )
        
        prompt = prompt_service.create_prompt(request)
        if not prompt:
            return PromptResponse(
                success=False,
                message="프롬프트 생성에 실패했습니다.",
                errors={"creation_error": "Failed to create prompt"}
            )
        
        return PromptResponse(
            success=True,
            message="프롬프트가 성공적으로 생성되었습니다.",
            prompt=prompt
        )
    except Exception as e:
        logger.error(f"프롬프트 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"프롬프트 생성 중 오류가 발생했습니다: {str(e)}")


@router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(prompt_id: str, request: PromptUpdateRequest):
    """
    통합 프롬프트 템플릿 수정
    """
    try:
        # 현재 프롬프트 가져오기
        existing_prompt = prompt_service.get_prompt_by_id(prompt_id)
        if not existing_prompt:
            return PromptResponse(
                success=False,
                message="해당 ID의 프롬프트를 찾을 수 없습니다.",
                errors={"not_found": "Prompt not found"}
            )
        
        # 필수 필드 검증 - 업데이트 요청에 필드가 없으면 기존 값 유지
        final_name = request.name if request.name is not None else existing_prompt.name
        final_role_definition = request.role_definition if request.role_definition is not None else existing_prompt.role_definition
        final_base_prompt = request.base_prompt if request.base_prompt is not None else existing_prompt.base_prompt
        
        logger.info(f"최종 검증 값들: name='{final_name}', role_definition='{final_role_definition}', base_prompt='{final_base_prompt}'")
        
        # 필수 필드 검증
        validation_errors = []
        if not final_name or not final_name.strip():
            validation_errors.append("이름")
        if not final_role_definition or not final_role_definition.strip():
            validation_errors.append("역할 정의")
        if not final_base_prompt or not final_base_prompt.strip():
            validation_errors.append("기본 프롬프트")
            
        if validation_errors:
            error_message = f"다음 필드는 필수입니다: {', '.join(validation_errors)}"
            logger.error(f"검증 실패: {error_message}")
            return PromptResponse(
                success=False,
                message=error_message,
                errors={"validation_error": f"Required fields missing: {validation_errors}"}
            )
        
        prompt = prompt_service.update_prompt(prompt_id, request)
        if not prompt:
            return PromptResponse(
                success=False,
                message="프롬프트 수정에 실패했습니다.",
                errors={"update_error": "Failed to update prompt"}
            )
        
        return PromptResponse(
            success=True,
            message="프롬프트가 성공적으로 수정되었습니다.",
            prompt=prompt
        )
    except Exception as e:
        logger.error(f"프롬프트 수정 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"프롬프트 수정 중 오류가 발생했습니다: {str(e)}")


@router.delete("/{prompt_id}", response_model=PromptResponse)
async def delete_prompt(prompt_id: str):
    """
    프롬프트 템플릿 삭제
    """
    try:
        success = prompt_service.delete_prompt(prompt_id)
        if not success:
            return PromptResponse(
                success=False,
                message="해당 ID의 프롬프트를 찾을 수 없거나 삭제에 실패했습니다.",
                errors={"deletion_error": "Failed to delete prompt"}
            )
        
        return PromptResponse(
            success=True,
            message="프롬프트가 성공적으로 삭제되었습니다."
        )
    except Exception as e:
        logger.error(f"프롬프트 삭제 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"프롬프트 삭제 중 오류가 발생했습니다: {str(e)}")


@router.post("/activate/{prompt_id}", response_model=PromptResponse)
async def activate_prompt(prompt_id: str):
    """
    특정 프롬프트를 활성화 (다른 프롬프트들은 비활성화)
    """
    try:
        success = prompt_service.activate_prompt(prompt_id)
        if not success:
            return PromptResponse(
                success=False,
                message="해당 ID의 프롬프트를 찾을 수 없거나 활성화에 실패했습니다.",
                errors={"activation_error": "Failed to activate prompt"}
            )
        
        # 활성화된 프롬프트 정보 반환
        prompt = prompt_service.get_prompt_by_id(prompt_id)
        return PromptResponse(
            success=True,
            message="프롬프트가 성공적으로 활성화되었습니다.",
            prompt=prompt
        )
    except Exception as e:
        logger.error(f"프롬프트 활성화 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"프롬프트 활성화 중 오류가 발생했습니다: {str(e)}")


@router.post("/duplicate/{prompt_id}", response_model=PromptResponse)
async def duplicate_prompt(prompt_id: str, new_name: Optional[str] = Query(None)):
    """
    통합 프롬프트 템플릿 복제
    """
    try:
        prompt = prompt_service.duplicate_prompt(prompt_id, new_name)
        if not prompt:
            return PromptResponse(
                success=False,
                message="해당 ID의 프롬프트를 찾을 수 없거나 복제에 실패했습니다.",
                errors={"duplication_error": "Failed to duplicate prompt"}
            )
        
        return PromptResponse(
            success=True,
            message="프롬프트가 성공적으로 복제되었습니다.",
            prompt=prompt
        )
    except Exception as e:
        logger.error(f"프롬프트 복제 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"프롬프트 복제 중 오류가 발생했습니다: {str(e)}")


@router.get("/preview/{prompt_id}")
async def preview_prompt(prompt_id: str, 
                        sample_title: str = Query("샘플 제목"), 
                        sample_content: str = Query("샘플 내용")):
    """
    통합 프롬프트 미리보기 - 샘플 데이터로 실제 프롬프트가 어떻게 생성되는지 확인
    """
    try:
        prompt = prompt_service.get_prompt_by_id(prompt_id)
        if not prompt:
            raise HTTPException(status_code=404, detail="프롬프트를 찾을 수 없습니다.")
        
        # 통합 프롬프트 컴파일 및 미리보기
        compiled_prompt = prompt_service.get_compiled_prompt(prompt_id, sample_title, sample_content)
        
        return {
            "success": True,
            "prompt_name": prompt.name,
            "system_message": prompt.system_message,
            "role_definition": prompt.role_definition,
            "detailed_instructions": prompt.detailed_instructions,
            "few_shot_examples": prompt.few_shot_examples,
            "cot_process": prompt.cot_process,
            "base_prompt": prompt.base_prompt,
            "compiled_prompt_preview": compiled_prompt
        }
        
    except Exception as e:
        logger.error(f"프롬프트 미리보기 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"프롬프트 미리보기 중 오류가 발생했습니다: {str(e)}")


@router.get("/compile/{prompt_id}")
async def compile_prompt(prompt_id: str, 
                        title: str = Query(""), 
                        content: str = Query("")):
    """
    통합 프롬프트를 컴파일하여 실제 사용할 프롬프트 생성
    """
    try:
        compiled_prompt = prompt_service.get_compiled_prompt(prompt_id, title, content)
        if not compiled_prompt:
            raise HTTPException(status_code=404, detail="프롬프트를 찾을 수 없습니다.")
        
        return {
            "success": True,
            "compiled_prompt": compiled_prompt
        }
        
    except Exception as e:
        logger.error(f"프롬프트 컴파일 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"프롬프트 컴파일 중 오류가 발생했습니다: {str(e)}")
