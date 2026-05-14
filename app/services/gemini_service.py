import google.generativeai as genai
from app.core.config import settings
from app.schemas.summarize import ChatRequest


# Gemini 클라이언트 초기화
genai.configure(api_key=settings.GEMINI_API_KEY)

PING_MESSAGE = "__ping__"


def build_prompt(req: ChatRequest) -> str:
    """카카오봇 메시지를 기반으로 Gemini 프롬프트를 생성한다."""
    room_ctx = f"단체 채팅방 '{req.room}'" if req.isGroup else f"개인 채팅방 '{req.room}'"

    prompt = f"""너는 카카오톡 AI 어시스턴트야. 친절하고 간결하게 한국어로 답변해줘.

[대화 정보]
- 채팅방: {room_ctx}
- 발신자: {req.sender}

[사용자 메시지]
{req.message}

[답변 조건]
- 200자 이내로 핵심만 간단히 답변해줘.
- 불필요한 인사말이나 맺음말은 생략해줘.
- 답변 텍스트만 출력해줘 (안내 문구 없이).
"""
    return prompt


async def chat_reply(req: ChatRequest) -> str:
    """Gemini API를 호출하여 카카오봇 답장 텍스트를 반환한다."""
    # 핑 처리 — Gemini 호출 없이 즉시 응답
    if req.message.strip() == PING_MESSAGE:
        return "pong"

    model = genai.GenerativeModel(model_name=settings.GEMINI_MODEL)
    prompt = build_prompt(req)

    response = await model.generate_content_async(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.7,
            max_output_tokens=512,
        ),
    )

    return response.text.strip()
