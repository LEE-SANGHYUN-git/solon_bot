from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.schemas.summarize import SummarizeRequest, SummarizeResponse, ErrorResponse
from app.services.gemini_service import summarize_text
from app.core.config import settings

import google.generativeai as genai

router = APIRouter()


@router.post(
    "/summarize",
    response_model=SummarizeResponse,
    status_code=status.HTTP_200_OK,
    summary="텍스트 요약",
    description="입력된 텍스트를 Gemini API를 사용하여 요약합니다.",
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
        503: {"model": ErrorResponse, "description": "Gemini API 오류"},
    },
)
async def summarize(req: SummarizeRequest) -> SummarizeResponse:
    """
    텍스트 요약 엔드포인트.

    - **text**: 요약할 원문 텍스트 (50~50,000자)
    - **style**: 요약 스타일 (bullet / paragraph / tldr)
    - **max_length**: 요약 결과 최대 글자 수 (기본 300)
    - **language**: 요약 언어 (ko / en)
    - **custom_prompt**: 추가 지시사항 (선택)
    """
    try:
        summary = await summarize_text(req)
    except genai.types.BlockedPromptException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="입력 텍스트가 안전 정책에 의해 차단되었습니다.",
        )
    except genai.types.StopCandidateException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Gemini API 응답 오류: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"요약 처리 중 오류가 발생했습니다: {str(e)}",
        )

    original_len = len(req.text)
    summary_len = len(summary)
    compression = round(summary_len / original_len, 4) if original_len > 0 else 0.0

    return SummarizeResponse(
        summary=summary,
        original_length=original_len,
        summary_length=summary_len,
        compression_ratio=compression,
        model=settings.GEMINI_MODEL,
        style=req.style,
    )
