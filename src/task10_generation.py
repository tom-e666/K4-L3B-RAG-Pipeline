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


USE_MMR = os.getenv("USE_MMR", "false").lower() in {"true", "1", "yes"}


def mmr_context_packing(
    query: str,
    chunks: list[dict],
    top_k: int = 5,
    *,
    lambda_param: float = 0.7,
) -> list[dict]:
    """Tối ưu chọn lọc context đa dạng theo Maximal Marginal Relevance (MMR).
    
    Formula: MMR(d) = λ * sim(q, d) - (1 - λ) * max_{s ∈ selected} sim(d, s)
    """
    if not chunks or len(chunks) <= 1:
        return chunks[:top_k]

    try:
        import numpy as np
        from .task4_chunking_indexing import embed_texts

        texts_to_embed = [query] + [c["content"] for c in chunks]
        embeddings = embed_texts(texts_to_embed)

        if len(embeddings) != len(texts_to_embed):
            return chunks[:top_k]

        q_emb = np.array(embeddings[0], dtype=np.float32)
        doc_embs = [np.array(e, dtype=np.float32) for e in embeddings[1:]]

        def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
            na, nb = np.linalg.norm(a), np.linalg.norm(b)
            if na == 0 or nb == 0:
                return 0.0
            return float(np.dot(a, b) / (na * nb))

        query_sims = [_cosine_sim(q_emb, d_emb) for d_emb in doc_embs]

        unselected_indices = list(range(len(chunks)))
        selected_indices = []

        # Giữ chunk tốt nhất ở vị trí đầu
        best_idx = 0
        selected_indices.append(best_idx)
        unselected_indices.remove(best_idx)

        target_count = min(top_k, len(chunks))
        while len(selected_indices) < target_count and unselected_indices:
            best_mmr_score = -float("inf")
            best_next_idx = unselected_indices[0]

            for idx in unselected_indices:
                sim_q_d = query_sims[idx]
                max_sim_s_d = max(
                    _cosine_sim(doc_embs[idx], doc_embs[sel_idx])
                    for sel_idx in selected_indices
                )
                mmr_score = lambda_param * sim_q_d - (1.0 - lambda_param) * max_sim_s_d

                if mmr_score > best_mmr_score:
                    best_mmr_score = mmr_score
                    best_next_idx = idx

            selected_indices.append(best_next_idx)
            unselected_indices.remove(best_next_idx)

        return [chunks[i] for i in selected_indices]

    except Exception as exc:
        logger.warning("MMR context packing failed: %s. Returning default candidates.", exc)
        return chunks[:top_k]


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Trả về GenerationResult kèm grounding & citation verification."""
    try:
        fetch_k = top_k * 2 if USE_MMR else top_k
        chunks = retrieve(query, top_k=fetch_k)
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
        if USE_MMR:
            selected_chunks = mmr_context_packing(query, chunks, top_k=top_k, lambda_param=0.7)
        else:
            selected_chunks = chunks[:top_k]

        reordered = reorder_for_llm(selected_chunks)
        context = format_context(reordered)
        user_message = f"Context:\n{context}\n\nQuestion: {query}"
        answer = call_llm(SYSTEM_PROMPT, user_message)

        # Grounding & Citation verification
        if not verify_citations(answer, len(reordered)):
            logger.warning("Citation verification failed. Returning safe refusal.")
            return {
                "answer": SAFE_REFUSAL_ANSWER,
                "sources": selected_chunks,
                "retrieval_source": selected_chunks[0]["retrieval_method"],
            }

        return {
            "answer": answer,
            "sources": selected_chunks,
            "retrieval_source": selected_chunks[0]["retrieval_method"],
        }
    except Exception as exc:
        logger.error(f"Generation failed: {exc}")
        return {
            "answer": SAFE_REFUSAL_ANSWER,
            "sources": chunks[:top_k],
            "retrieval_source": chunks[0]["retrieval_method"] if chunks else "none",
        }


if __name__ == "__main__":
    print(generate_with_citation("test query"))


