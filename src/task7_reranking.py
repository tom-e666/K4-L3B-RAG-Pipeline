"""
Task 7 — Reciprocal Rank Fusion.

RRF gộp nhiều bảng xếp hạng mà không cộng trực tiếp cosine score với BM25
score. Công thức: RRF(d) = sum(1 / (k + rank)), rank bắt đầu từ 1.

Lưu ý: RRF score chỉ phản ánh thứ hạng, không dùng để quyết định fallback.

-> Dùng Jina hoặc self host hoặc bất cứ công cụ nào bạn quen
"""


def weighted_rrf(
    dense_results: list[dict],
    bm25_results: list[dict],
    *,
    dense_weight: float = 1.0,
    bm25_weight: float = 1.0,
    top_k: int = 5,
    k: int = 60,
) -> list[dict]:
    """Fuse dense search và bm25 search kết quả bằng Weighted RRF.
    
    Công thức: RRF_score(d) = dense_weight / (k + rank_dense) + bm25_weight / (k + rank_bm25)
    """
    scores: dict[str, float] = {}
    items: dict[str, dict] = {}

    for rank, item in enumerate(dense_results, 1):
        item_id = item["id"]
        scores[item_id] = scores.get(item_id, 0.0) + (dense_weight / (k + rank))
        items[item_id] = item

    for rank, item in enumerate(bm25_results, 1):
        item_id = item["id"]
        scores[item_id] = scores.get(item_id, 0.0) + (bm25_weight / (k + rank))
        if item_id not in items:
            items[item_id] = item

    # Sắp xếp giảm dần theo score; nếu bằng score thì tie-break bằng id ổn định
    sorted_ids = sorted(scores.keys(), key=lambda item_id: (-scores[item_id], item_id))

    results = []
    for item_id in sorted_ids[:top_k]:
        result = items[item_id].copy()
        result["score"] = scores[item_id]
        result["retrieval_method"] = "hybrid"
        results.append(result)
    return results


def rerank_rrf(
    ranked_lists: list[list[dict]],
    top_k: int = 5,
    k: int = 60,
) -> list[dict]:
    """Fuse nhiều ranked lists và trả hybrid SearchResult theo contract chuẩn."""
    if not ranked_lists:
        return []

    if len(ranked_lists) == 2:
        return weighted_rrf(
            ranked_lists[0],
            ranked_lists[1],
            dense_weight=1.0,
            bm25_weight=1.0,
            top_k=top_k,
            k=k,
        )

    scores: dict[str, float] = {}
    items: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            item_id = item["id"]
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
            if item_id not in items:
                items[item_id] = item

    sorted_ids = sorted(scores.keys(), key=lambda item_id: (-scores[item_id], item_id))
    results = []
    for item_id in sorted_ids[:top_k]:
        result = items[item_id].copy()
        result["score"] = scores[item_id]
        result["retrieval_method"] = "hybrid"
        results.append(result)
    return results


import json
import logging

logger = logging.getLogger(__name__)

LISTWISE_RERANK_PROMPT = """Bạn là hệ thống xếp hạng tài liệu chuyên sâu cho RAG.
Nhiệm vụ: Dựa vào câu hỏi (Query) và danh sách các đoạn tài liệu (Candidate Documents), hãy xếp hạng lại các tài liệu theo mức độ liên quan từ CAO nhất đến THẤP nhất để trả lời cho câu hỏi.

Quy tắc:
1. Đánh giá tính liên quan trực tiếp của nội dung tài liệu đối với câu hỏi.
2. Trả về ĐÚNG 1 ĐỐI TƯỢNG JSON với key "ranked_ids" chứa danh sách ID của các tài liệu đã được sắp xếp.
3. Không giải thích thêm, chỉ trả về JSON hợp lệ.

Ví dụ định dạng trả về:
{"ranked_ids": ["doc_id_1", "doc_id_2", "doc_id_3"]}
"""


def call_llm(system_prompt: str, user_message: str) -> str:
    from .task10_generation import call_llm as _call_llm
    return _call_llm(system_prompt, user_message)


def llm_listwise_rerank(
    query: str,
    chunks: list[dict],
    top_k: int = 5,
    *,
    max_content_length: int = 300,
) -> list[dict]:
    """Rerank lại danh sách candidate chunks bằng LLM Listwise Reranking.
    
    Yêu cầu:
    - Candidate set candidate_k = min(15, top_k * 3).
    - Prompt chỉ chứa candidate ID, title, source và content rút gọn.
    - Trả về JSON {"ranked_ids": [...]}.
    - Validate JSON: ID thuộc candidate set, unique; append ID chưa xuất hiện để đủ top_k.
    - Fallback: trả về candidates top-k nếu có lỗi/timeout.
    """
    if not chunks:
        return []

    candidate_k = min(15, top_k * 3)
    candidates = chunks[:candidate_k]
    candidate_map = {item["id"]: item for item in candidates}

    # Chuẩn bị nội dung rút gọn gửi tới LLM
    doc_entries = []
    for item in candidates:
        title = item.get("metadata", {}).get("title", "")
        source = item.get("metadata", {}).get("source", "")
        snippet = item.get("content", "")[:max_content_length].replace("\n", " ")
        doc_entries.append(
            f"ID: {item['id']}\nTitle: {title}\nSource: {source}\nSnippet: {snippet}"
        )

    candidates_text = "\n---\n".join(doc_entries)
    user_message = f"Query: {query}\n\nCandidate Documents:\n{candidates_text}"

    try:
        raw_response = call_llm(LISTWISE_RERANK_PROMPT, user_message)

        clean_text = raw_response.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        parsed = json.loads(clean_text)
        ranked_ids = parsed.get("ranked_ids", [])

        # Validate: ID thuộc candidate set & unique
        valid_ranked_ids = []
        seen = set()
        for doc_id in ranked_ids:
            if doc_id in candidate_map and doc_id not in seen:
                valid_ranked_ids.append(doc_id)
                seen.add(doc_id)

        # Append các candidate ID chưa xuất hiện để bảo toàn dữ liệu
        for item in candidates:
            if item["id"] not in seen:
                valid_ranked_ids.append(item["id"])
                seen.add(item["id"])

        reranked_results = []
        for rank, doc_id in enumerate(valid_ranked_ids[:top_k], 1):
            res = candidate_map[doc_id].copy()
            res["score"] = max(0.01, round(1.0 - (rank - 1) * 0.05, 4))
            res["retrieval_method"] = "hybrid"
            reranked_results.append(res)

        return reranked_results

    except Exception as exc:
        logger.warning("LLM listwise rerank error: %s. Returning default candidates.", exc)
        fallback_results = []
        for item in candidates[:top_k]:
            res = item.copy()
            res["retrieval_method"] = "hybrid"
            fallback_results.append(res)
        return fallback_results


if __name__ == "__main__":
    print("Weighted RRF & LLM Listwise Rerank ready.")



