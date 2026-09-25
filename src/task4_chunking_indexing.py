"""
Task 4 — Chunking, embedding và indexing.

Hướng dẫn:
    1. Đọc toàn bộ Markdown trong data/standardized/.
    2. Chia văn bản bằng strategy đã chọn.
    3. Embed chunks bằng một provider duy nhất.
    4. Upsert vào ChromaDB với cosine distance.

Mỗi document/chunk phải theo docs/MODULE_CONTRACTS.md. ID cần ổn định để
chạy lại pipeline không tạo dữ liệu trùng. Task 5 phải dùng chung embed_texts().
"""

import os
import re
import json
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"
CACHE_FILE = Path(__file__).parent.parent / "data" / "embedded_chunks_cache.json"

# Giải thích lựa chọn tham số trong báo cáo nhóm.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "gemini").lower()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL") or (
    "gemini-embedding-001" if EMBEDDING_PROVIDER == "gemini" else "BAAI/bge-m3"
)
EMBEDDING_DIM = 3072 if "gemini" in EMBEDDING_MODEL else 1024

COLLECTION_NAME = "rag_documents"

_ST_MODEL = None


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Dispatch embedding theo EMBEDDING_PROVIDER trong .env."""
    if not texts:
        return []

    provider = os.getenv("EMBEDDING_PROVIDER", EMBEDDING_PROVIDER).lower()
    model_name = os.getenv("EMBEDDING_MODEL", EMBEDDING_MODEL)

    if provider == "gemini":
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY không được tìm thấy trong môi trường hoặc file .env")
        client = genai.Client(api_key=api_key)
        embeddings: list[list[float]] = []
        batch_size = 10
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            max_retries = 8
            for attempt in range(max_retries):
                try:
                    response = client.models.embed_content(
                        model=model_name,
                        contents=batch,
                    )
                    for item in response.embeddings:
                        embeddings.append(list(item.values))
                    if len(texts) > batch_size:
                        time.sleep(1)
                    break
                except Exception as exc:
                    err_str = str(exc)
                    if attempt < max_retries - 1:
                        wait_sec = 8
                        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                            wait_sec = 25
                            m = re.search(r"retryDelay': '(\d+)s'", err_str) or re.search(r"retry in (\d+)", err_str)
                            if m:
                                wait_sec = int(m.group(1)) + 2
                            print(f"Rate limit (429). Chờ {wait_sec}s trước khi thử lại batch {i//batch_size + 1}...")
                        else:
                            print(f"Lỗi mạng ({type(exc).__name__}). Thử lại sau {wait_sec}s...")
                        time.sleep(wait_sec)
                    else:
                        raise exc
        return embeddings

    elif provider == "openai":
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("BASE_URL")
        client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
        embeddings = []
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            res = client.embeddings.create(model=model_name, input=batch)
            embeddings.extend([item.embedding for item in res.data])
        return embeddings

    else:
        # Provider local (SentenceTransformer)
        global _ST_MODEL
        if _ST_MODEL is None:
            from sentence_transformers import SentenceTransformer

            _ST_MODEL = SentenceTransformer(model_name)
        return _ST_MODEL.encode(texts).tolist()


def get_collection():
    """Mở Chroma collection dùng cosine distance."""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def load_documents() -> list[dict]:
    """Đọc Markdown và trả về danh sách Document."""
    documents = []
    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        if path.name.startswith("."):
            continue
        text = path.read_text(encoding="utf-8")
        doc_type = "legal" if "legal" in path.parts else "news"
        title = path.stem
        source = path.name
        url = None

        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                frontmatter_text = parts[1]
                content = parts[2].strip()
                import yaml

                try:
                    meta = yaml.safe_load(frontmatter_text)
                    if isinstance(meta, dict):
                        title = meta.get("title") or title
                        source = meta.get("source") or source
                        doc_type = meta.get("doc_type") or doc_type
                        url = meta.get("url") or meta.get("source_url") or None
                except Exception:
                    pass
            else:
                content = text
        else:
            content = text

        documents.append(
            {
                "id": path.relative_to(STANDARDIZED_DIR).as_posix(),
                "content": content,
                "metadata": {
                    "source": str(source),
                    "title": str(title),
                    "doc_type": str(doc_type),
                    "url": str(url) if url else None,
                },
            }
        )
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia Document thành chunks có id và chunk_index."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    for document in documents:
        splits = splitter.split_text(document["content"])
        for index, text in enumerate(splits):
            if not text.strip():
                continue
            chunks.append(
                {
                    "id": f"{document['id']}::chunk-{index}",
                    "content": text.strip(),
                    "metadata": {
                        **document["metadata"],
                        "chunk_index": index,
                    },
                }
            )
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Thêm embedding vào từng chunk (có lưu cache sau mỗi batch)."""
    if not chunks:
        return []

    cache = {}
    if CACHE_FILE.exists():
        try:
            cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            cache = {}

    missing_chunks = [c for c in chunks if c["id"] not in cache]
    if missing_chunks:
        print(f"Cần embed {len(missing_chunks)} chunks (đã có trong cache: {len(chunks) - len(missing_chunks)})...")
        batch_size = 10
        for i in range(0, len(missing_chunks), batch_size):
            batch = missing_chunks[i : i + batch_size]
            texts = [c["content"] for c in batch]
            vectors = embed_texts(texts)
            for c, vec in zip(batch, vectors):
                cache[c["id"]] = vec
            try:
                CACHE_FILE.write_text(json.dumps(cache), encoding="utf-8")
                print(f"Đã lưu tiến độ: {len(cache)}/{len(chunks)} chunks.")
            except Exception:
                pass
            time.sleep(1)
    else:
        print(f"Toàn bộ {len(chunks)} chunks đã có sẵn trong cache!")

    for chunk in chunks:
        chunk["embedding"] = cache[chunk["id"]]
    return chunks


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert chunks vào ChromaDB."""
    if not chunks:
        print("⚠️ Không có chunks nào để index. Kiểm tra lại thư mục dữ liệu markdown (data/standardized).")
        return
    collection = get_collection()

    cleaned_metadatas = []
    for chunk in chunks:
        meta = dict(chunk["metadata"])
        if meta.get("url") is None:
            meta["url"] = ""
        cleaned_metadatas.append(meta)

    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        batch_meta = cleaned_metadatas[i : i + batch_size]
        collection.upsert(
            ids=[c["id"] for c in batch],
            documents=[c["content"] for c in batch],
            embeddings=[c["embedding"] for c in batch],
            metadatas=batch_meta,
        )


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    print("Loading standardized documents...")
    documents = load_documents()
    print(f"Loaded {len(documents)} documents.")
    print("Chunking documents...")
    chunks = chunk_documents(documents)
    print(f"Created {len(chunks)} chunks.")
    print("Embedding chunks...")
    embedded_chunks = embed_chunks(chunks)
    print("Indexing to ChromaDB...")
    index_to_vectorstore(embedded_chunks)
    print(f"Successfully indexed {len(embedded_chunks)} chunks to ChromaDB.")


if __name__ == "__main__":
    run_pipeline()
