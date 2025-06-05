#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class NewsItem(BaseModel):
    """
    단일 뉴스 아이템을 나타내는 스키마
    """
    title: str
    url: str = Field(..., alias="link")
    date: str = Field(..., alias="pubDate")
    content: str = Field(..., alias="description")
    source: Optional[str] = None
    keyword: Optional[str] = None
    is_relevant: Optional[bool] = False
    relevance_reason: Optional[str] = ""
    category: Optional[str] = "기타"
    highlights: Optional[List[str]] = []
    
    class Config:
        populate_by_name = True


class CrawlerRequest(BaseModel):
    """
    뉴스 크롤링 요청 스키마
    """
    keywords: List[str] = Field(..., description="검색할 키워드 목록")
    max_news_per_keyword: Optional[int] = Field(100, description="키워드당 최대 뉴스 건수")
    sort: Optional[str] = Field("date", description="정렬 방식 (date:최신순, sim:정확도순)")
    days: Optional[int] = Field(30, description="최근 몇 일 간의 뉴스를 검색할지 설정")
    start_date: Optional[str] = Field(None, description="검색 시작 날짜 (YYYY-MM-DD 형식)")
    end_date: Optional[str] = Field(None, description="검색 종료 날짜 (YYYY-MM-DD 형식)")


class CrawlerResponse(BaseModel):
    """
    뉴스 크롤링 응답 스키마
    """
    success: bool = Field(..., description="크롤링 성공 여부")
    message: str = Field(..., description="응답 메시지")
    file_path: Optional[str] = Field(None, description="결과 파일 경로")
    download_path: Optional[str] = Field(None, description="다운로드 폴더에 저장된 파일 경로")
    item_count: Optional[int] = Field(None, description="총 뉴스 항목 수")
    keywords: Optional[List[str]] = Field(None, description="검색한 키워드 목록")
    errors: Optional[Dict[str, str]] = Field(None, description="오류 정보")


class RelevanceRequest(BaseModel):
    """
    관련성 평가 요청 스키마
    """
    file_path: str = Field(..., description="평가할 CSV 파일 경로")
    api_key: str = Field(..., description="OpenAI 또는 Claude API 키")
    model: Optional[str] = Field("gpt-4.1-nano", description="사용할 LLM 모델 (gpt-4.1-nano, gpt-4.1-mini, gpt-4.1, gpt-4o-mini, gpt-3.5-turbo 등)")
    prompt_id: Optional[str] = Field(None, description="사용할 프롬프트 ID")


class RelevanceResponse(BaseModel):
    """
    관련성 평가 응답 스키마
    """
    success: bool = Field(..., description="평가 성공 여부")
    message: str = Field(..., description="응답 메시지")
    file_path: Optional[str] = Field(None, description="결과 파일 경로")
    stats: Optional[Dict[str, Any]] = Field(None, description="평가 통계 정보")
    errors: Optional[Dict[str, str]] = Field(None, description="오류 정보")
    session_id: Optional[str] = Field(None, description="세션 ID")


class FileListResponse(BaseModel):
    """
    파일 목록 응답 스키마
    """
    files: List[Dict[str, Any]] = Field(..., description="파일 목록 (경로, 크기, 날짜 등)")


class DownloadLinkResponse(BaseModel):
    """
    파일 다운로드 링크 응답 스키마
    """
    success: bool = Field(..., description="성공 여부")
    download_link: str = Field(..., description="다운로드 링크")
    file_name: str = Field(..., description="파일명")


class PromptTemplate(BaseModel):
    """
    통합 프롬프트 템플릿 스키마
    """
    id: Optional[str] = Field(None, description="프롬프트 ID")
    name: str = Field(..., description="프롬프트 이름")
    description: Optional[str] = Field(None, description="프롬프트 설명")
    
    # 통합 프롬프트 구성 요소
    role_definition: str = Field(..., description="역할 정의")
    detailed_instructions: str = Field(..., description="상세 지침")
    few_shot_examples: str = Field(..., description="Few-shot 예시")
    cot_process: str = Field(..., description="Chain of Thought - 단계별 사고 과정")
    base_prompt: str = Field(..., description="기본 프롬프트")
    
    system_message: Optional[str] = Field(None, description="시스템 메시지")
    is_active: bool = Field(True, description="활성 상태")
    created_at: Optional[datetime] = Field(None, description="생성 시간")
    updated_at: Optional[datetime] = Field(None, description="수정 시간")

    class Config:
        populate_by_name = True
    
    def get_compiled_prompt(self) -> str:
        """
        모든 구성 요소를 하나의 프롬프트로 컴파일
        """
        return f"""## 역할 정의
{self.role_definition}

## 상세 지침
{self.detailed_instructions}

## Few-shot 예시
{self.few_shot_examples}

## 단계별 사고 과정 (Chain of Thought)
{self.cot_process}

## 기본 프롬프트
{self.base_prompt}"""


class PromptCreateRequest(BaseModel):
    """
    통합 프롬프트 생성 요청 스키마
    """
    name: str = Field(..., description="프롬프트 이름")
    description: Optional[str] = Field(None, description="프롬프트 설명")
    
    # 통합 프롬프트 구성 요소
    role_definition: str = Field(..., description="역할 정의")
    detailed_instructions: str = Field(..., description="상세 지침")
    few_shot_examples: str = Field(..., description="Few-shot 예시")
    cot_process: str = Field(..., description="Chain of Thought - 단계별 사고 과정")
    base_prompt: str = Field(..., description="기본 프롬프트")
    
    system_message: Optional[str] = Field(None, description="시스템 메시지")


class PromptUpdateRequest(BaseModel):
    """
    통합 프롬프트 수정 요청 스키마
    """
    name: Optional[str] = Field(None, description="프롬프트 이름")
    description: Optional[str] = Field(None, description="프롬프트 설명")
    
    # 통합 프롬프트 구성 요소
    role_definition: Optional[str] = Field(None, description="역할 정의")
    detailed_instructions: Optional[str] = Field(None, description="상세 지침")
    few_shot_examples: Optional[str] = Field(None, description="Few-shot 예시")
    cot_process: Optional[str] = Field(None, description="Chain of Thought - 단계별 사고 과정")
    base_prompt: Optional[str] = Field(None, description="기본 프롬프트")
    
    system_message: Optional[str] = Field(None, description="시스템 메시지")
    is_active: Optional[bool] = Field(None, description="활성 상태")


class PromptListResponse(BaseModel):
    """
    프롬프트 목록 응답 스키마
    """
    prompts: List[PromptTemplate] = Field(..., description="프롬프트 목록")
    total: int = Field(..., description="총 프롬프트 수")


class PromptResponse(BaseModel):
    """
    프롬프트 응답 스키마
    """
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    prompt: Optional[PromptTemplate] = Field(None, description="프롬프트 데이터")
    errors: Optional[Dict[str, str]] = Field(None, description="오류 정보")
