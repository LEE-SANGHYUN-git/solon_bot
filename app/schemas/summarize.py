from pydantic import BaseModel, Field
from typing import Literal, Optional


class SummarizeRequest(BaseModel):
    """텍스트 요약 요청 스키마."""

    text: str = Field(
        ...,
        min_length=50,
        max_length=50_000,
        description="요약할 원문 텍스트 (최소 50자, 최대 50,000자)",
        examples=["인공지능(AI)은 컴퓨터 시스템이 인간의 지능을 모방하여 학습, 추론, 문제 해결 등의 작업을 수행하는 기술입니다..."],
    )
    style: Literal["bullet", "paragraph", "tldr"] = Field(
        default="bullet",
        description="요약 스타일: bullet(글머리 기호) | paragraph(단락) | tldr(한 줄 요약)",
    )
    max_length: int = Field(
        default=300,
        ge=50,
        le=2000,
        description="요약 결과의 최대 글자 수",
    )
    language: Literal["ko", "en"] = Field(
        default="ko",
        description="요약 언어: ko(한국어) | en(영어)",
    )
    custom_prompt: Optional[str] = Field(
        default=None,
        max_length=500,
        description="(선택) 추가 지시사항 (예: '전문 용어를 쉽게 설명해줘')",
    )


class SummarizeResponse(BaseModel):
    """텍스트 요약 응답 스키마."""

    summary: str = Field(description="요약된 텍스트")
    original_length: int = Field(description="원문 글자 수")
    summary_length: int = Field(description="요약 결과 글자 수")
    compression_ratio: float = Field(description="압축률 (0~1, 낮을수록 더 많이 압축)")
    model: str = Field(description="사용된 Gemini 모델명")
    style: str = Field(description="적용된 요약 스타일")


class ErrorResponse(BaseModel):
    """에러 응답 스키마."""

    error: str
    detail: Optional[str] = None
