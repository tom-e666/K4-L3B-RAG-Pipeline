"""Chat page and source rendering."""

from __future__ import annotations

import html
import logging
import re
from pathlib import Path
from typing import Any

import streamlit as st


STANDARDIZED_DIR = Path(__file__).resolve().parent.parent / "data" / "standardized"
logger = logging.getLogger(__name__)


@st.cache_data
def source_metadata(filename: str) -> dict[str, str]:
    """Recover public source title and URL omitted from indexed metadata."""
    safe_name = Path(filename).name
    for kind in ("legal", "news"):
        path = STANDARDIZED_DIR / kind / safe_name
        if path.is_file():
            content = path.read_text(encoding="utf-8")
            header = content.split("---", 2)[1] if content.startswith("---") else ""
            result = {}
            for key in ("title", "url"):
                match = re.search(rf"^{key}:\s*[\"']?(.+?)[\"']?\s*$", header, re.M)
                if match:
                    result[key] = match.group(1).strip().strip('"\'')
            return result
    return {}


def normalize_message(message: Any) -> dict[str, Any]:
    """Support both the old list-style and current dict-style history."""
    if isinstance(message, dict):
        return message
    if isinstance(message, (list, tuple)) and len(message) >= 2:
        return {"role": message[0], "content": message[1]}
    return {"role": "assistant", "content": str(message)}


def render_sources(sources: list[dict[str, Any]]) -> None:
    if not sources:
        return
    with st.expander(f"Nguồn tham khảo ({len(sources)})", expanded=False):
        for index, source in enumerate(sources, 1):
            metadata = source.get("metadata") or {}
            source_name = metadata.get("source") or "Không rõ tên tệp"
            original = source_metadata(source_name)
            title = original.get("title") or metadata.get("title") or source_name
            url = metadata.get("url") or original.get("url")
            method = source.get("retrieval_method") or "unknown"
            score = source.get("score")
            score_text = f" · điểm {float(score):.3f}" if isinstance(score, (int, float)) else ""
            link = (
                f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">Mở tài liệu gốc</a>'
                if isinstance(url, str) and url.startswith(("https://", "http://")) else "Tài liệu trong repo"
            )
            st.markdown(
                f'<div class="source-card"><div class="source-title">{index}. {html.escape(title)}</div>'
                f'<div class="source-meta">{html.escape(source_name)} · {html.escape(method)}{score_text} · {link}</div></div>',
                unsafe_allow_html=True,
            )


def render_chat_page() -> None:
    st.markdown(
        '<section class="hero"><div class="eyebrow">AI20K · Tra cứu tài liệu chính thức</div>'
        '<h1>Trợ lý AI Thực Chiến</h1>'
        '<p>Hỏi về chương trình, lộ trình học và quy định. Xem các đoạn tài liệu được truy xuất dưới mỗi câu trả lời.</p></section>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("### Trợ lý AI Thực Chiến")
        st.caption("Tra cứu từ tài liệu AI20K đã lập chỉ mục")
        st.markdown(
            '<span class="pipeline-badge">DeepSeek</span>'
            '<span class="pipeline-badge">Hybrid search</span>'
            '<span class="pipeline-badge">Citation</span>',
            unsafe_allow_html=True,
        )
        top_k = st.slider("Số đoạn tài liệu", min_value=3, max_value=10, value=5,
                          help="Số đoạn tối đa dùng để tạo câu trả lời.")
        if st.button("＋ Cuộc trò chuyện mới", type="primary", width="stretch"):
            st.session_state.messages = []
            st.rerun()

    suggestions = [
        "Điều kiện tham gia chương trình là gì?",
        "Lộ trình học gồm những giai đoạn nào?",
        "Quy định về bài tập và đánh giá ra sao?",
    ]
    messages = [normalize_message(item) for item in st.session_state.get("messages", [])]
    if not messages:
        st.markdown(
            '<div class="empty-state"><h3>Bắt đầu với một câu hỏi</h3>'
            '<div>Trợ lý sẽ tìm trong bộ tài liệu AI20K trước khi trả lời.</div></div>',
            unsafe_allow_html=True,
        )
        st.caption("Gợi ý câu hỏi")
        for index, suggestion in enumerate(suggestions):
            if st.button(suggestion, key=f"suggestion-{index}", width="stretch"):
                st.session_state.pending_query = suggestion
                st.rerun()

    for message in messages:
        role = message.get("role", "assistant")
        with st.chat_message(role, avatar="🧑" if role == "user" else "🤖"):
            content = message.get("content", "")
            if content:
                st.markdown(content)
            elif role == "assistant":
                st.warning("Chatbot chưa có câu trả lời cho câu hỏi này.")
            if role == "assistant":
                if message.get("safe_refusal"):
                    st.markdown(
                        '<div class="answer-note">Thông tin này chưa được xác minh từ bộ tài liệu hiện có.</div>',
                        unsafe_allow_html=True,
                    )
                render_sources(message.get("sources") or [])

    query = st.chat_input("Nhập câu hỏi về chương trình AI Thực Chiến…")
    query = query or st.session_state.pop("pending_query", None)
    query = query.strip() if isinstance(query, str) else query
    if not query:
        return

    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(query)
    with st.chat_message("assistant", avatar="🤖"):
        response_box = st.empty()
        try:
            # Lazy import keeps the UI shell usable while backend dependencies are installed.
            from src.task10_generation import generate_with_citation

            with st.spinner("Đang tìm trong tài liệu và soạn câu trả lời…"):
                result = generate_with_citation(query, top_k=top_k)
            answer = str(result.get("answer") or "").strip()
            sources = result.get("sources") or []
            safe_refusal = (
                not answer
                or result.get("retrieval_source") == "none"
                or "không thể xác minh" in answer.lower()
            )
            if answer:
                response_box.markdown(answer)
            else:
                response_box.warning("Chưa tìm thấy câu trả lời từ tài liệu hiện có.")
            if safe_refusal:
                st.markdown(
                    '<div class="answer-note">Đây là trạng thái không đủ bằng chứng trong tài liệu; '
                    'vui lòng thử diễn đạt câu hỏi cụ thể hơn.</div>',
                    unsafe_allow_html=True,
                )
            render_sources(sources)
            st.session_state.messages.append(
                {"role": "assistant", "content": answer, "sources": sources, "safe_refusal": safe_refusal}
            )
        except Exception:
            logger.exception("Chat request failed")
            response_box.error("Không thể kết nối tới bộ máy RAG lúc này. Nội dung câu hỏi vẫn được giữ lại.")
