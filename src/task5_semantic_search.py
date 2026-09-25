"""
Task 5 — Semantic search.

Embed query bằng chính hàm của Task 4, query ChromaDB và đổi cosine distance
thành similarity. Output phải theo SearchResult, sort giảm dần và không quá top_k.
"""

from .task4_chunking_indexing import embed_texts, get_collection


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về dense SearchResult theo score giảm dần."""
    if top_k <= 0:
        return []

    collection = get_collection()
    count = collection.count() if hasattr(collection, "count") else 10
    if count == 0:
        return []

    actual_k = min(top_k, count) if isinstance(count, int) and count > 0 else top_k
    query_vector = embed_texts([query])[0]
    response = collection.query(
        query_embeddings=[query_vector],
        n_results=actual_k,
        include=["documents", "metadatas", "distances"],
    )

    if not response or not response.get("ids") or not response["ids"][0]:
        return []

    results = []
    for item_id, content, metadata, distance in zip(
        response["ids"][0],
        response["documents"][0],
        response["metadatas"][0],
        response["distances"][0],
    ):
        clean_meta = dict(metadata)
        if clean_meta.get("url") == "":
            clean_meta["url"] = None

        results.append(
            {
                "id": item_id,
                "content": content,
                "score": max(0.0, 1.0 - float(distance)),
                "metadata": clean_meta,
                "retrieval_method": "dense",
            }
        )
    return sorted(results, key=lambda item: item["score"], reverse=True)[:top_k]


if __name__ == "__main__":
    for result in semantic_search("chương trình AI Thực Chiến", top_k=3):
        print(result)
