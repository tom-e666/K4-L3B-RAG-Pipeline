"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 5. BM25 phù hợp với từ khóa chính xác, mã tài
liệu và tên riêng. Output phải theo SearchResult và sort score giảm dần.
"""

from rank_bm25 import BM25Okapi
from .task4_chunking_indexing import get_collection


def load_corpus() -> list[dict]:
    """Lấy corpus chunks từ ChromaDB để đảm bảo đồng nhất với Task 5."""
    try:
        collection = get_collection()
        data = collection.get(include=["documents", "metadatas"])
        if not data or not data.get("ids"):
            return []
        items = []
        for chunk_id, doc, meta in zip(
            data["ids"], data["documents"], data["metadatas"]
        ):
            clean_meta = dict(meta)
            if clean_meta.get("url") == "":
                clean_meta["url"] = None
            items.append(
                {
                    "id": chunk_id,
                    "content": doc,
                    "metadata": clean_meta,
                }
            )
        return items
    except Exception:
        return []


def build_bm25_index(corpus: list[dict]):
    """Tạo BM25 index từ cùng corpus chunks của Task 4."""
    if not corpus:
        return None
    tokenized = [item["content"].lower().split() for item in corpus]
    return BM25Okapi(tokenized)


CORPUS: list[dict] = load_corpus()
BM25_INDEX = build_bm25_index(CORPUS) if CORPUS else None


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    global CORPUS, BM25_INDEX
    if top_k <= 0:
        return []

    if not CORPUS:
        CORPUS = load_corpus()
        if CORPUS:
            BM25_INDEX = build_bm25_index(CORPUS)

    if not CORPUS:
        return []

    bm25 = BM25_INDEX
    if bm25 is None or len(getattr(bm25, "doc_len", [])) != len(CORPUS):
        bm25 = build_bm25_index(CORPUS)

    tokens = query.lower().split()
    if not tokens:
        return []

    scores = bm25.get_scores(tokens)
    indices = sorted(
        range(len(CORPUS)),
        key=lambda index: (-float(scores[index]), index),
    )[:top_k]

    results = []
    for index in indices:
        item = CORPUS[index]
        results.append(
            {
                "id": item["id"],
                "content": item["content"],
                "score": float(scores[index]),
                "metadata": item["metadata"],
                "retrieval_method": "bm25",
            }
        )
    return results


if __name__ == "__main__":
    for result in lexical_search("học bổng tuyển sinh", top_k=3):
        print(result)
