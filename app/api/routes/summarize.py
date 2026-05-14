from asyncio import TimeoutError as AsyncTimeoutError

from fastapi import APIRouter, HTTPException, status

from app.schemas.summarize import ChatRequest, ChatResponse, ErrorResponse
from app.services.gemini_service import chat_reply

import google.generativeai as genai

router = APIRouter()


@router.post(
    "/summarize",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="카카오봇 메시지 처리",
    description="MessengerBot R에서 전송한 메시지를 Gemini API로 처리하고 답장을 반환합니다.",
    responses={
        400: {"model": ErrorResponse, "description": "안전 정책 차단"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
        503: {"model": ErrorResponse, "description": "Gemini API 오류"},
    },
)
async def summarize(req: ChatRequest) -> ChatResponse:
    """
    카카오봇 메시지 처리 엔드포인트.

    - **room**: 채팅방 이름
    - **sender**: 보낸 사람 이름
    - **message**: 메시지 내용 (`__ping__` 입력 시 연결 확인용 pong 응답)
    - **isGroup**: 단체 채팅방 여부
    """
    try:
        reply = await chat_reply(req)
    except AsyncTimeoutError:
        return ChatResponse(reply="⏱️ 응답 생성에 60초가 넘게 걸렸어요. 잠시 후 다시 시도해주세요.")
    except genai.types.BlockedPromptException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="입력 메시지가 안전 정책에 의해 차단되었습니다.",
        )
    except genai.types.StopCandidateException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Gemini API 응답 오류: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"메시지 처리 중 오류가 발생했습니다: {str(e)}",
        )

    return ChatResponse(reply=reply)
