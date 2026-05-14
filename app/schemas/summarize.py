from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    """카카오봇 메시지 요청 스키마 (MessengerBot R 호환)."""

    room: str = Field(description="채팅방 이름")
    sender: str = Field(description="보낸 사람 이름")
    message: str = Field(description="메시지 내용")
    isGroup: bool = Field(default=False, description="단체 채팅방 여부")


class ChatResponse(BaseModel):
    """카카오봇 응답 스키마 — 봇이 { reply } 키를 파싱함."""

    reply: str = Field(description="봇이 카카오톡으로 전송할 답장 텍스트")


class ErrorResponse(BaseModel):
    """에러 응답 스키마."""

    error: str
    detail: Optional[str] = None
