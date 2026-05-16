import asyncio
import re
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

import google.generativeai as genai
from app.core.config import settings
from app.schemas.summarize import ChatRequest


# Gemini 클라이언트 초기화
genai.configure(api_key=settings.GEMINI_API_KEY)

PING_MESSAGE = "__ping__"
GEMINI_TIMEOUT_SEC = 60  # 봇 스크립트 TIMEOUT_MS(60000)와 동일

# 메시지에서 URL을 감지하는 정규식
URL_PATTERN = re.compile(r"https?://[^\s]+")


# ── URL 크롤링 ───────────────────────────────────────────────────────────────

async def fetch_page(url: str) -> tuple[str, str, str]:
    """
    URL 페이지를 가져와 (제목, 본문 텍스트, 사이트명)을 반환한다.
    단축 URL은 follow_redirects=True 로 최종 페이지까지 따라간다.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # 제목
    title = soup.title.string.strip() if soup.title else "제목 없음"

    # 본문 정제 (불필요한 태그 제거 후 텍스트 추출)
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    lines = [line.strip() for line in soup.get_text(separator="\n").splitlines()]
    content = "\n".join(line for line in lines if len(line) > 20)[:6000]

    # 사이트명: 리다이렉트 후 최종 도메인 기준
    final_domain = urlparse(str(resp.url)).netloc.replace("www.", "")
    site_name = final_domain.split(".")[0]

    return title, content, site_name


# ── 프롬프트 빌더 ────────────────────────────────────────────────────────────

def build_url_prompt(url: str, title: str, content: str, site_name: str) -> str:
    """URL 요약 프롬프트 — 지정 형식으로 출력하도록 지시한다."""
    return f"""아래 웹페이지를 분석해서 다음 형식으로 정확히 요약해줘.

[페이지 정보]
- URL: {url}
- 사이트명: {site_name}
- 제목: {title}

[페이지 내용]
{content}

[출력 형식 — 아래를 반드시 그대로 따라줘. 다른 말은 절대 붙이지 마.]

👉[{title}] 에 대한 사이트 요약입니다.

이모지 핵심 내용 1 (1~2문장으로 간결하게)
이모지 핵심 내용 2 (1~2문장으로 간결하게)
이모지 핵심 내용 3 (1~2문장으로 간결하게)

[규칙]
- 핵심 내용은 반드시 3개만 출력해줘.
- 각 항목은 1~2문장으로 간결하게, 핵심만 담아줘.
- 페이지에서 가장 중요한 정보 3가지를 우선순위 순으로 선정해줘.
- 각 항목 앞에 내용에 어울리는 이모지를 붙여줘.
  이모지 예시: 📈(성과/수치) 💡(아이디어/기능) ⚠️(주의/이슈) 📘(학습/가이드) 🧠(AI/기술) 🎯(목표/전략)
- URL은 출력하지 마. 링크 없이 텍스트만 출력해줘.
"""



def build_chat_prompt(req: ChatRequest) -> str:
    """일반 채팅 프롬프트."""
    room_ctx = f"단체 채팅방 '{req.room}'" if req.isGroup else f"개인 채팅방 '{req.room}'"
    return f"""너는 카카오톡 AI 어시스턴트야. 친절하고 간결하게 한국어로 답변해줘.

[대화 정보]
- 채팅방: {room_ctx}
- 발신자: {req.sender}

[사용자 메시지]
{req.message}

[답변 조건]
- 질문의 내용과 복잡도에 맞게 충분히 자세하게 답변해줘.
- 불필요한 인사말이나 맺음말은 생략해줘.
- 답변 텍스트만 출력해줘 (안내 문구 없이).
"""


# ── 메인 함수 ────────────────────────────────────────────────────────────────

async def chat_reply(req: ChatRequest) -> str | None:
    """카카오봇 메시지를 처리하고 Gemini 답장을 반환한다.
    URL이 없는 메시지는 None을 반환하여 응답하지 않는다.
    """

    # 핑 처리
    if req.message.strip() == PING_MESSAGE:
        return "pong"

    # URL이 없으면 무응답
    url_match = URL_PATTERN.search(req.message)
    if not url_match:
        return None

    url = url_match.group().rstrip(")")  # 괄호 끝 문자 제거 방지
    try:
        title, content, site_name = await fetch_page(url)
        prompt = build_url_prompt(url, title, content, site_name)
    except Exception:
        # 페이지 가져오기 실패 시 무응답
        return None

    model = genai.GenerativeModel(model_name=settings.GEMINI_MODEL)
    response = await asyncio.wait_for(
        model.generate_content_async(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=3096,
            ),
        ),
        timeout=GEMINI_TIMEOUT_SEC,
    )

    return response.text.strip()
