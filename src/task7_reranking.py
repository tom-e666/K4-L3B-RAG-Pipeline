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


if __name__ == "__main__":
    print("Weighted RRF implementation ready.")

