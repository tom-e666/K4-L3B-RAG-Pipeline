"""Chat page and source rendering."""

from __future__ import annotations

from typing import Any

import streamlit as st


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
            title = metadata.get("title") or metadata.get("source") or f"Tài liệu {index}"
            source_name = metadata.get("source") or "Không rõ tên tệp"
            url = metadata.get("url")
            method = source.get("retrieval_method") or "unknown"
            score = source.get("score")
            score_text = f" · điểm {float(score):.3f}" if isinstance(score, (int, float)) else ""
            link = f'<a href="{url}" target="_blank">Mở nguồn</a>' if url else "Nguồn nội bộ"
            st.markdown(
                f'<div class="source-card"><div class="source-title">{index}. {title}</div>'
                f'<div class="source-meta">{source_name} · {method}{score_text} · {link}</div></div>',
                unsafe_allow_html=True,
            )


def render_chat_page() -> None:
    st.markdown(
        '<section class="hero"><div class="eyebrow">AI20K · Tra cứu tài liệu chính thức</div>'
        '<h1>Trợ lý AI Thực Chiến</h1>'
        '<p>Hỏi về chương trình, lộ trình học và quy định. Câu trả lời luôn đi kèm nguồn để bạn kiểm tra.</p></section>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("### Trợ lý AI Thực Chiến")
        st.caption("Tra cứu thông tin chương trình từ tài liệu chính thức")
        top_k = st.slider("Số nguồn sử dụng", min_value=3, max_value=10, value=5)
        if st.button("＋ Cuộc trò chuyện mới", use_container_width=True):
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
        cols = st.columns(len(suggestions))
        for col, suggestion in zip(cols, suggestions):
            if col.button(suggestion, use_container_width=True):
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
            safe_refusal = not answer or result.get("retrieval_source") == "none"
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
        except Exception as exc:
            response_box.error("Không thể kết nối tới bộ máy RAG lúc này. Nội dung câu hỏi vẫn được giữ lại.")
            st.caption(f"Chi tiết kỹ thuật: {exc}")
