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

import logging
import os
import re

from dotenv import load_dotenv

from .task9_retrieval_pipeline import retrieve

logger = logging.getLogger(__name__)

load_dotenv()

TOP_K = 5
TOP_P = 0.9
TEMPERATURE = 0.3

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
LLM_MODEL = os.getenv("LLM_MODEL") or ("gemini-3.5-flash-lite" if LLM_PROVIDER == "gemini" else "gpt-4o-mini")

SAFE_REFUSAL_ANSWER = "Tôi không thể xác minh thông tin này từ nguồn hiện có."

SYSTEM_PROMPT = """Bạn là trợ lý AI trả lời câu hỏi dựa trên tài liệu.
Quy tắc bắt buộc:
1. Trả lời CHỈ dựa trên thông tin có trong phần Context dưới đây. CẤM tự ý suy đoán hoặc dùng kiến thức bên ngoài context.
2. Mỗi khẳng định trong câu trả lời PHẢI kèm trích dẫn dạng [Document X] tương ứng với tài liệu nguồn (ví dụ: [Document 1]).
3. Nếu Context không chứa đủ thông tin để trả lời, hãy trả lời chính xác: "Tôi không thể xác minh thông tin này từ nguồn hiện có."
"""


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Đưa chunks quan trọng về đầu và cuối context."""
    # TODO: Implement document reordering.
    #
    if len(chunks) <= 2:
        return list(chunks)
    front = chunks[::2]
    back = chunks[1::2]
    return front + back[::-1]


def format_context(chunks: list[dict]) -> str:
    """Tạo context có title và source label."""
    # TODO: Format chunks để LLM tạo citation kiểm chứng được.
    
    parts = []
    for index, chunk in enumerate(chunks, 1):
        metadata = chunk["metadata"]
        parts.append(
            f"[Document {index} | Title: {metadata['title']} | "
            f"Source: {metadata['source']}]\n{chunk['content']}"
        )
    return "\n\n---\n\n".join(parts)


def verify_citations(answer: str, num_documents: int) -> bool:
    """Kiểm tra tính hợp lệ của Grounding và Citations trong câu trả lời.
    
    Quy tắc:
    - Nếu answer là safe refusal -> hợp lệ.
    - Nếu answer rỗng -> không hợp lệ.
    - Trích xuất tất cả nhãn [Document X]:
      + Phải có ít nhất 1 citation nếu không phải refusal.
      + Mọi chỉ số X phải thỏa mãn 1 <= X <= num_documents.
    """
    if not answer or not answer.strip():
        return False

    clean_answer = answer.strip().lower()
    if "không thể xác minh thông tin" in clean_answer or "không đủ thông tin" in clean_answer:
        return True

    # Trích xuất các số thứ tự Document X
    matches = re.findall(r"\[document\s+(\d+)\]", answer, re.IGNORECASE)
    if not matches:
        logger.warning("Grounding verification failed: No [Document X] citation found in answer.")
        return False

    for doc_num_str in matches:
        doc_num = int(doc_num_str)
        if doc_num < 1 or doc_num > num_documents:
            logger.warning(
                f"Citation verification failed: [Document {doc_num}] out of bounds (1..{num_documents})."
            )
            return False

    return True


def call_llm(system_prompt: str, user_message: str) -> str:
    """Gọi OpenAI, Gemini hoặc Anthropic theo cấu hình."""
    # TODO: Dispatch theo LLM_PROVIDER.
    #
    # - openai    -> OPENAI_API_KEY
    # - gemini    -> GEMINI_API_KEY
    # - anthropic -> ANTHROPIC_API_KEY
    #
    # Dùng LLM_MODEL và trả về text thuần cho cả ba nhánh.
    if LLM_PROVIDER == "openai":
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("BASE_URL")
        client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}],
            temperature=TEMPERATURE,
            max_tokens=1024,
        )
        return completion.choices[0].message.content
    if LLM_PROVIDER == "gemini":
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=TEMPERATURE,
                max_output_tokens=1024,
            ),
        )
        return response.text
    if LLM_PROVIDER == "anthropic":
        from anthropic import Anthropic
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model=LLM_MODEL,
            max_tokens=1024,
            temperature=TEMPERATURE,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_message}
                    ],
                }
            ],
        )
        return response.content[0].text

    raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Trả về GenerationResult."""
    # TODO: Implement end-to-end generation.
    
        chunks = retrieve(query, top_k=top_k)
    except Exception as exc:
        logger.error(f"Retrieve error: {exc}")
        chunks = []

    if not chunks:
        return {
            "answer": SAFE_REFUSAL_ANSWER,
            "sources": [],
            "retrieval_source": "none",
        }

    try:
        reordered = reorder_for_llm(chunks)
        context = format_context(reordered)
        user_message = f"Context:\n{context}\n\nQuestion: {query}"
        answer = call_llm(SYSTEM_PROMPT, user_message)

        # Grounding & Citation verification
        if not verify_citations(answer, len(reordered)):
            logger.warning("Citation verification failed. Returning safe refusal.")
            return {
                "answer": SAFE_REFUSAL_ANSWER,
                "sources": chunks,
                "retrieval_source": chunks[0]["retrieval_method"],
            }

        return {
            "answer": answer,
            "sources": chunks,
            "retrieval_source": chunks[0]["retrieval_method"],
        }
    except Exception as exc:
        logger.error(f"Generation failed: {exc}")
        return {
            "answer": SAFE_REFUSAL_ANSWER,
            "sources": chunks,
            "retrieval_source": chunks[0]["retrieval_method"] if chunks else "none",
        }


if __name__ == "__main__":
    print(generate_with_citation("test query"))

