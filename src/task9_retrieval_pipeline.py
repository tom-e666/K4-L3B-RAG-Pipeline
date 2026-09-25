
"""
Task 9 — Retrieval pipeline hoàn chỉnh.

Luồng xử lý:
    1. Chạy semantic_search và lexical_search.
    2. Fuse hai danh sách bằng RRF đúng một lần.
    3. Lấy best cosine score gốc từ dense results.
    4. Nếu score dưới threshold, thử PageIndex fallback.
    5. Nếu fallback lỗi, trả hybrid results thay vì crash.

Không so sánh threshold với RRF score vì hai thang đo khác nhau.
"""

import os
from dotenv import load_dotenv

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank_rrf, weighted_rrf
from .task8_pageindex_vectorless import pageindex_search

load_dotenv()

def _parse_float(val: str | None, default: float) -> float:
    if not val or not val.strip():
        return default
    try:
        return float(val.strip())
    except ValueError:
        return default


SCORE_THRESHOLD = _parse_float(os.getenv("SCORE_THRESHOLD"), 0.3)
DEFAULT_TOP_K = 5

# DENSE_WEIGHT & BM25_WEIGHT đọc từ .env (Mặc định 1.0/1.0 là bản Thường)
DENSE_WEIGHT = _parse_float(os.getenv("DENSE_WEIGHT"), 1.0)
BM25_WEIGHT = _parse_float(os.getenv("BM25_WEIGHT"), 1.0)



def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """Trả về hybrid hoặc pageindex SearchResult."""
    dense = semantic_search(query, top_k=top_k * 2)
    sparse = lexical_search(query, top_k=top_k * 2)

    if use_reranking:
        if DENSE_WEIGHT != 1.0 or BM25_WEIGHT != 1.0:
            hybrid = weighted_rrf(
                dense,
                sparse,
                dense_weight=DENSE_WEIGHT,
                bm25_weight=BM25_WEIGHT,
                top_k=top_k,
            )
        else:
            hybrid = rerank_rrf([dense, sparse], top_k=top_k)
    else:
        hybrid = dense[:top_k]

    best_dense_score = dense[0]["score"] if dense else 0.0
    if best_dense_score < score_threshold:
        try:
            fallback = pageindex_search(query, top_k=top_k)
            if fallback:
                return fallback
        except Exception:
            pass
    return hybrid[:top_k]



if __name__ == "__main__":
    for result in retrieve("test query", top_k=3):
        print(result)
