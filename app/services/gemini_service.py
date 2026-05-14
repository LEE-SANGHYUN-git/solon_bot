import google.generativeai as genai
from app.core.config import settings
from app.schemas.summarize import SummarizeRequest


# Gemini 클라이언트 초기화
genai.configure(api_key=settings.GEMINI_API_KEY)


STYLE_INSTRUCTIONS = {
    "bullet": "핵심 내용을 3~5개의 글머리 기호(•)로 정리해줘. 각 항목은 한 문장으로 작성해.",
    "paragraph": "자연스러운 단락 형식으로 핵심 내용을 요약해줘.",
    "tldr": "TL;DR 형식으로 한 문장 또는 두 문장으로 핵심만 요약해줘.",
}

LANGUAGE_INSTRUCTIONS = {
    "ko": "반드시 한국어로 답변해줘.",
    "en": "Please respond in English only.",
}


def build_prompt(req: SummarizeRequest) -> str:
    """요청 옵션에 따른 프롬프트 생성."""
    style_inst = STYLE_INSTRUCTIONS.get(req.style, STYLE_INSTRUCTIONS["bullet"])
    lang_inst = LANGUAGE_INSTRUCTIONS.get(req.language, LANGUAGE_INSTRUCTIONS["ko"])
    custom = f"\n추가 지시사항: {req.custom_prompt}" if req.custom_prompt else ""

    prompt = f"""다음 텍스트를 요약해줘.

[요약 조건]
- {style_inst}
- 요약 결과는 {req.max_length}자 이내로 작성해줘.
- {lang_inst}{custom}
- 원문에 없는 내용을 추가하지 마.
- 요약 결과만 출력해줘 (안내 문구 없이).

[원문]
{req.text}
"""
    return prompt


async def summarize_text(req: SummarizeRequest) -> str:
    """Gemini API를 호출하여 텍스트를 요약한다."""
    model = genai.GenerativeModel(model_name=settings.GEMINI_MODEL)
    prompt = build_prompt(req)

    response = await model.generate_content_async(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.3,       # 낮은 온도 → 일관성 있는 요약
            max_output_tokens=1024,
        ),
    )

    return response.text.strip()
