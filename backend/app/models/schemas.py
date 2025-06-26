#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import List, Optional, Dict, Any, Union
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
    session_id: Optional[str] = Field(None, description="세션 ID (진행률 추적용)")
    batch_size: Optional[int] = Field(10, description="배치 처리 크기 (기본값: 10)")
    use_batch_processing: Optional[bool] = Field(True, description="배치 처리 사용 여부 (기본값: True)")


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
    name: str = Field(..., min_length=1, description="프롬프트 이름 (필수)")
    description: Optional[str] = Field("", description="프롬프트 설명")
    
    # 통합 프롬프트 구성 요소
    role_definition: str = Field(..., min_length=1, description="역할 정의 (필수)")
    detailed_instructions: str = Field("", description="상세 지침")
    few_shot_examples: str = Field("", description="Few-shot 예시")
    cot_process: str = Field("", description="Chain of Thought - 단계별 사고 과정")
    base_prompt: str = Field(..., min_length=1, description="기본 프롬프트 (필수)")
    
    system_message: Optional[str] = Field("정확한 JSON 형식으로만 응답하세요.", description="시스템 메시지")


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


class DeduplicationRequest(BaseModel):
    """
    GPT 임베딩 기반 중복 제거 요청 스키마
    """
    file_path: str = Field(..., description="중복 제거할 파일 경로")
    api_key: str = Field(..., description="OpenAI API 키")
    similarity_threshold: Optional[float] = Field(0.85, description="임베딩 유사도 임계값 (0.85-0.95 권장)")
    batch_size: Optional[int] = Field(50, description="임베딩 생성 배치 크기")
    session_id: Optional[str] = Field(None, description="세션 ID (진행률 추적용)")
    embedding_model: Optional[str] = Field("text-embedding-3-small", description="사용할 임베딩 모델")


class DeduplicationResponse(BaseModel):
    """
    중복 제거 응답 스키마
    """
    success: bool = Field(..., description="중복 제거 성공 여부")
    message: str = Field(..., description="응답 메시지")
    file_path: Optional[str] = Field(None, description="결과 파일 경로")
    download_path: Optional[str] = Field(None, description="다운로드 폴더에 저장된 파일 경로")
    stats: Optional[Dict[str, Any]] = Field(None, description="중복 제거 통계 정보")
    session_id: Optional[str] = Field(None, description="세션 ID")
    errors: Optional[Dict[str, str]] = Field(None, description="오류 정보")


class DuplicateGroup(BaseModel):
    """
    중복 그룹 정보
    """
    group_id: int = Field(..., description="그룹 ID")
    representative_title: str = Field(..., description="대표 제목")
    articles: List[Dict[str, Any]] = Field(..., description="그룹에 속한 기사들")
    similarity_scores: List[float] = Field(..., description="유사도 점수들")
    count: int = Field(..., description="그룹 내 기사 수")

class EmbeddingDeduplicationRequest(BaseModel):
    """
    GPT 임베딩 기반 중복 제거 요청 스키마
    """
    file_path: str = Field(..., description="중복 제거할 파일 경로")
    api_key: str = Field(..., description="OpenAI API 키")
    similarity_threshold: Optional[float] = Field(0.85, description="임베딩 유사도 임계값 (0.85-0.95 권장)")
    batch_size: Optional[int] = Field(50, description="임베딩 생성 배치 크기")
    session_id: Optional[str] = Field(None, description="세션 ID (진행률 추적용)")
    embedding_model: Optional[str] = Field("text-embedding-3-small", description="사용할 임베딩 모델")


class AutoDeduplicationRequest(BaseModel):
    """
    자동 중복 제거 요청 스키마 (데이터 크기에 따라 방식 자동 선택)
    """
    file_path: str = Field(..., description="중복 제거할 파일 경로")
    api_key: Optional[str] = Field(None, description="OpenAI API 키 (임베딩 방식 사용시 필요)")
    tfidf_threshold: Optional[float] = Field(0.70, description="TF-IDF 유사도 임계값")
    embedding_threshold: Optional[float] = Field(0.85, description="임베딩 유사도 임계값")
    batch_size: Optional[int] = Field(50, description="배치 처리 크기")
    session_id: Optional[str] = Field(None, description="세션 ID (진행률 추적용)")
    force_method: Optional[str] = Field(None, description="강제 방식 선택 (tfidf, embedding)")


class DeduplicationMethodInfo(BaseModel):
    """
    중복 제거 방식 정보
    """
    name: str = Field(..., description="방식 이름")
    description: str = Field(..., description="방식 설명")
    pros: List[str] = Field(..., description="장점 목록")
    cons: List[str] = Field(..., description="단점 목록")
    recommended_threshold: str = Field(..., description="권장 임계값 범위")
    cost: str = Field(..., description="비용 정보")


class DeduplicationMethodsResponse(BaseModel):
    """
    중복 제거 방식 목록 응답
    """
    methods: Dict[str, DeduplicationMethodInfo] = Field(..., description="사용 가능한 방식들")
    recommendations: Dict[str, str] = Field(..., description="상황별 권장사항")


# 기존 DeduplicationResponse에 추가할 필드들 (기존 코드 수정용)
class EnhancedDeduplicationResponse(DeduplicationResponse):
    """
    강화된 중복 제거 응답 스키마
    """
    method_used: Optional[str] = Field(None, description="사용된 중복 제거 방식")
    processing_details: Optional[Dict[str, Any]] = Field(None, description="처리 상세 정보")
    cost_info: Optional[Dict[str, Any]] = Field(None, description="비용 정보 (임베딩 사용시)")
    performance_metrics: Optional[Dict[str, Any]] = Field(None, description="성능 지표")