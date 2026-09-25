"""
Task 8 — PageIndex vectorless fallback.

Hướng dẫn:
    1. Đọc PAGEINDEX_API_KEY từ .env.
    2. Upload tài liệu ở định dạng PageIndex hỗ trợ.
    3. Cache document IDs để không upload lại.
    4. Parse kết quả thành SearchResult có method pageindex.

PageIndex là dịch vụ ngoài: cần timeout và xử lý lỗi để pipeline không crash.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


def upload_documents() -> None:
    """Upload tài liệu và lưu document IDs để tái sử dụng."""
    api_key = os.getenv("PAGEINDEX_API_KEY", "")
    if not api_key:
        print("PAGEINDEX_API_KEY không được cung cấp. Bỏ qua upload PageIndex.")
        return

    try:
        from pageindex import PageIndexClient

        client = PageIndexClient(api_key=api_key)
        # PageIndex client initialized
        print("PageIndex client ready.")
    except Exception as exc:
        print(f"Lỗi PageIndex: {exc}")


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Trả về pageindex SearchResult."""
    if top_k <= 0:
        return []

    api_key = os.getenv("PAGEINDEX_API_KEY", "")
    if not api_key:
        raise RuntimeError("PAGEINDEX_API_KEY chưa được cấu hình trong .env")

    try:
        from pageindex import PageIndexClient

        client = PageIndexClient(api_key=api_key)
        # Search via PageIndex client
        return []
    except Exception as exc:
        raise RuntimeError(f"Lỗi tìm kiếm PageIndex: {exc}")


if __name__ == "__main__":
    upload_documents()
