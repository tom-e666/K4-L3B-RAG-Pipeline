"""
Task 10 — Generation có citation.

Hướng dẫn:
    1. Retrieve top-k chunks.
    2. Reorder để giảm lost-in-the-middle.
    3. Format context kèm title và source.
    4. Gọi provider được chọn trong .env.
    5. Trả answer, sources và retrieval_source.

Nếu context không đủ hoặc provider lỗi, trả safe refusal; không bịa thông tin.
"""

import os
import re
import time
from dotenv import load_dotenv

from .task9_retrieval_pipeline import retrieve

load_dotenv()

TOP_K = 5
TOP_P = 0.9
TEMPERATURE = 0.3

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
LLM_MODEL = os.getenv("LLM_MODEL") or (
    "gemini-2.5-flash" if LLM_PROVIDER == "gemini" else "gpt-4o-mini"
)

SYSTEM_PROMPT = """Bạn là trợ lý giải đáp thắc mắc về chương trình Đào tạo Nhân tài AI Thực chiến Tập đoàn Vingroup (AI20K).
Chỉ trả lời dựa trên context được cung cấp.
Mỗi khẳng định hoặc thông tin quan trọng cần kèm citation (ví dụ: [Source: tên_file, Title: tiêu_đề]).
Nếu thông tin không có trong context hoặc context không đủ bằng chứng, hãy lịch sự từ chối: 'Tôi không thể xác minh thông tin này từ nguồn hiện có.'"""

SAFE_REFUSAL_ANSWER = "Tôi không thể xác minh thông tin này từ nguồn hiện có."


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Đưa chunks quan trọng về đầu và cuối context (tránh lost-in-the-middle)."""
    if len(chunks) <= 2:
        return list(chunks)
    front = chunks[::2]
    back = chunks[1::2]
    return front + back[::-1]


def format_context(chunks: list[dict]) -> str:
    """Tạo context có title và source label rõ ràng cho citation."""
    parts = []
    for index, chunk in enumerate(chunks, 1):
        metadata = chunk.get("metadata", {})
        title = metadata.get("title", f"Document {index}")
        source = metadata.get("source", "Unknown source")
        parts.append(
            f"[Document {index} | Title: {title} | Source: {source}]\n{chunk['content']}"
        )
    return "\n\n---\n\n".join(parts)


def call_llm(system_prompt: str, user_message: str) -> str:
    """Gọi OpenAI, Gemini hoặc Anthropic theo cấu hình trong .env."""
    provider = os.getenv("LLM_PROVIDER", LLM_PROVIDER).lower()
    model = os.getenv("LLM_MODEL", LLM_MODEL)

    if provider == "openai":
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("BASE_URL")
        client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=TEMPERATURE,
            max_tokens=1024,
        )
        return completion.choices[0].message.content or ""

    elif provider == "gemini":
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        max_retries = 8
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=user_message,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=TEMPERATURE,
                        max_output_tokens=1024,
                    ),
                )
                return response.text or ""
            except Exception as exc:
                err_str = str(exc)
                if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str) and attempt < max_retries - 1:
                    wait_sec = 25
                    m = re.search(r"retryDelay': '(\d+)s'", err_str) or re.search(r"retry in (\d+)", err_str)
                    if m:
                        wait_sec = int(m.group(1)) + 2
                    print(f"Gemini generation rate limit (429). Chờ {wait_sec}s trước khi thử lại...")
                    time.sleep(wait_sec)
                else:
                    raise exc
        return ""

    elif provider == "anthropic":
        from anthropic import Anthropic

        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            temperature=TEMPERATURE,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text or ""

    else:
        raise ValueError(f"Không hỗ trợ LLM_PROVIDER={provider}")


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Trả về GenerationResult."""
    try:
        chunks = retrieve(query, top_k=top_k)
    except Exception:
        chunks = []

    if not chunks:
        return {
            "answer": SAFE_REFUSAL_ANSWER,
            "sources": [],
            "retrieval_source": "none",
        }

    reordered = reorder_for_llm(chunks)
    context = format_context(reordered)
    user_message = f"Dưới đây là các đoạn trích từ tài liệu:\n\n{context}\n\nCâu hỏi: {query}\nHãy trả lời câu hỏi trên dựa trên các tài liệu trên."

    try:
        answer = call_llm(SYSTEM_PROMPT, user_message)
        if not answer or not answer.strip():
            answer = SAFE_REFUSAL_ANSWER
    except Exception as exc:
        print(f"Lỗi gọi LLM: {exc}")
        answer = SAFE_REFUSAL_ANSWER

    first_method = chunks[0].get("retrieval_method", "hybrid")
    retrieval_source = "pageindex" if first_method == "pageindex" else "hybrid"

    return {
        "answer": answer.strip(),
        "sources": chunks,
        "retrieval_source": retrieval_source,
    }


if __name__ == "__main__":
    test_query = "Điều kiện tham gia chương trình AI Thực Chiến là gì?"
    result = generate_with_citation(test_query, top_k=3)
    print("Answer:\n", result["answer"])
    print("\nSources count:", len(result["sources"]))
    print("Retrieval source:", result["retrieval_source"])
