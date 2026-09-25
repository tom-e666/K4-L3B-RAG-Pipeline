"""Chat page and conversation flow for Trợ lý AI Thực Chiến."""

from __future__ import annotations
from typing import Any
import streamlit as st

from ui.components.hero import render_hero
from ui.components.message import render_message


def normalize_message(message: Any) -> dict[str, Any]:
    """Support both list-style and dict-style chat history."""
    if isinstance(message, dict):
        return message
    if isinstance(message, (list, tuple)) and len(message) >= 2:
        return {"role": message[0], "content": message[1]}
    return {"role": "assistant", "content": str(message)}


def render_chat_page(top_k: int = 5) -> None:
    """Render the polished AI20K chat interface."""
    # Top hero section
    render_hero(
        eyebrow="AI20K • RAG KNOWLEDGE ASSISTANT",
        title="Trợ lý AI Thực Chiến",
        subtitle="Tra cứu chương trình, lộ trình học và quy định từ tài liệu chính thức.",
        badges=["Hybrid Retrieval", "Citation Enabled", "Knowledge Base Ready"],
    )

    suggestions = [
        "Điều kiện tham gia chương trình AI20K là gì?",
        "Lộ trình 5 giai đoạn cuộc thi Hackathon gồm những mốc nào?",
        "Quy định về nộp 10 deliverables Demo Day ra sao?",
    ]

    messages = [normalize_message(item) for item in st.session_state.get("messages", [])]

    # Empty state with suggestions
    if not messages:
        st.markdown(
            """
            <div class="empty-state">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">🤖</div>
                <h3 style="font-size: 1.15rem; font-weight: 700; color: #0F172A; margin-bottom: 0.25rem;">
                    Bắt đầu với một câu hỏi
                </h3>
                <div style="font-size: 0.88rem; color: #64748B; max-width: 500px; margin: 0 auto 1.2rem auto;">
                    Trợ lý sẽ truy xuất từ bộ tài liệu chính thức (sổ tay, quy chế, tin tức) trước khi sinh câu trả lời kèm nguồn minh chứng.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        cols = st.columns(len(suggestions))
        for col, suggestion in zip(cols, suggestions):
            if col.button(suggestion, use_container_width=True):
                st.session_state.pending_query = suggestion
                st.rerun()

    # Render conversation history
    for message in messages:
        role = message.get("role", "assistant")
        content = message.get("content", "")
        sources = message.get("sources") or []
        safe_refusal = message.get("safe_refusal", False)
        render_message(role, content, sources=sources, safe_refusal=safe_refusal)

    # Sticky bottom chat input
    query = st.chat_input("Hỏi về chương trình AI Thực Chiến...")
    query = query or st.session_state.pop("pending_query", None)
    query = query.strip() if isinstance(query, str) else query

    if not query:
        return

    # Add user message to state
    st.session_state.messages.append({"role": "user", "content": query})
    render_message("user", query)

    # Assistant response box
    with st.chat_message("assistant", avatar="🤖"):
        response_box = st.empty()
        with st.spinner("Đang truy xuất tài liệu và tổng hợp câu trả lời…"):
            try:
                from src.task10_generation import generate_with_citation

                result = generate_with_citation(query, top_k=top_k)
                answer = str(result.get("answer") or "").strip()
                sources = result.get("sources") or []
                safe_refusal = not answer or result.get("retrieval_source") == "none" or "không thể xác minh" in answer.lower()

                if not answer:
                    answer = "Chưa tìm thấy câu trả lời từ tài liệu hiện có."

                # Update message state
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                        "safe_refusal": safe_refusal,
                    }
                )
                response_box.empty()
                st.rerun()

            except Exception as exc:
                response_box.error(f"Không thể kết nối tới bộ máy RAG lúc này: {exc}")
