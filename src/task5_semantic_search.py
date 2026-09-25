"""
Task 5 — Semantic search.

Embed query bằng chính hàm của Task 4, query ChromaDB và đổi cosine distance
thành similarity. Output phải theo SearchResult, sort giảm dần và không quá top_k.
"""

import logging
import os
import numpy as np
from dotenv import load_dotenv

from .task4_chunking_indexing import embed_texts, get_collection


logger = logging.getLogger(__name__)

load_dotenv()

# USE_HYDE đọc từ .env (Mặc định False để tuân thủ contract tests gốc)
USE_HYDE = os.getenv("USE_HYDE", "false").lower() in {"true", "1", "yes"}

HYDE_PROMPT = """Hãy viết một đoạn văn ngắn (khoảng 2-4 câu) giả định chứa thông tin/câu trả lời cho câu hỏi dưới đây.
Đoạn văn này chỉ dùng làm ngữ cảnh tìm kiếm tài liệu, không cần xác minh thực tế.
"""


def generate_hypothetical_document(query: str) -> str:
    """Sinh văn bản giả định (Hypothetical Document) qua LLM."""
    try:
        from .task7_reranking import call_llm

        hypothetical_text = call_llm(HYDE_PROMPT, f"Câu hỏi: {query}")
        return hypothetical_text.strip() if hypothetical_text else ""
    except Exception as exc:
        logger.warning("HyDE generation failed: %s. Falling back to raw query.", exc)
        return ""


def _l2_normalize(vec: np.ndarray) -> np.ndarray:
    """Chuẩn hóa vector theo L2 norm."""
    norm = np.linalg.norm(vec)
    if norm > 0:
        return vec / norm
    return vec


def _semantic_search(query: str, top_k: int, use_hyde: bool) -> list[dict]:
    """Run dense retrieval with an explicit HyDE choice."""
    query_vector = None
    hyde_used = False

    if use_hyde:
        try:
            hypo_doc = generate_hypothetical_document(query)
            if hypo_doc:
                vectors = embed_texts([query, hypo_doc])
                if len(vectors) == 2 and len(vectors[0]) > 0:
                    vec_query = np.array(vectors[0], dtype=np.float32)
                    vec_hypo = np.array(vectors[1], dtype=np.float32)

                    # Tính trung bình cộng và L2-normalize
                    avg_vec = (vec_query + vec_hypo) / 2.0
                    norm_vec = _l2_normalize(avg_vec)
                    query_vector = norm_vec.tolist()
                    hyde_used = True
                    logger.info("HyDE activated for semantic search query.")
        except Exception as exc:
            logger.warning("HyDE process failed: %s. Reverting to raw query.", exc)

    if query_vector is None:
        query_vector = embed_texts([query])[0]

    response = get_collection().query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    results = []
    if response["ids"] and response["ids"][0]:
        for item_id, content, metadata, distance in zip(
            response["ids"][0],
            response["documents"][0],
            response["metadatas"][0],
            response["distances"][0],
        ):
            meta = dict(metadata) if metadata else {}
            if hyde_used:
                meta["hyde_used"] = True

            results.append({
                "id": item_id,
                "content": content,
                "score": max(0.0, 1.0 - distance),
                "metadata": meta,
                "retrieval_method": "dense",
            })

    return sorted(results, key=lambda item: item["score"], reverse=True)[:top_k]


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """Return dense results using the configured HyDE setting."""
    return _semantic_search(query, top_k, USE_HYDE)


def semantic_search_raw(query: str, top_k: int = 10) -> list[dict]:
    """Return dense results from the original query for A/B comparison."""
    return _semantic_search(query, top_k, False)


if __name__ == "__main__":
    for result in semantic_search("test query", top_k=3):
        print(result)

