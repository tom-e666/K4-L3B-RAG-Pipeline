"""Sidebar navigation and controls component."""

from __future__ import annotations
import streamlit as st

NAV_OPTIONS = [
    "💬 Chat",
    "⚖ So sánh các kỹ thuật",
    "📊 Đánh giá A/B",
]


def render_sidebar() -> tuple[str, dict]:
    """Render modern sidebar and return selected page and options dict."""
    with st.sidebar:
        # Header Brand
        st.markdown(
            """
            <div class="sidebar-brand">
                <span class="brand-badge">VINUNI • AI20K</span>
                <h2 class="brand-title">TRỢ LÝ AI THỰC CHIẾN</h2>
                <p class="brand-subtitle">AI20K Knowledge Assistant</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption("CHẾ ĐỘ LÀM VIỆC")

        # Determine index from session state
        current_page = st.session_state.get("current_nav_page", NAV_OPTIONS[0])
        default_idx = (
            NAV_OPTIONS.index(current_page)
            if current_page in NAV_OPTIONS
            else 0
        )

        selected_page = st.radio(
            "Điều hướng",
            NAV_OPTIONS,
            index=default_idx,
            key="current_nav_page",
            label_visibility="collapsed",
        )

        st.markdown("<hr style='margin: 1.2rem 0; border: none; border-top: 1px solid #E2E8F0;' />", unsafe_allow_html=True)

        options = {}

        # Mode specific settings
        if "Chat" in selected_page:
            st.caption("CẤU HÌNH TRUY XUẤT")
            top_k = st.slider(
                "Số nguồn sử dụng",
                min_value=1,
                max_value=10,
                value=st.session_state.get("chat_top_k", 5),
                key="chat_top_k",
                help="Số đoạn trích (chunks) phù hợp nhất được gửi vào ngữ cảnh của LLM.",
            )
            options["top_k"] = top_k

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            if st.button("＋ Cuộc trò chuyện mới", use_container_width=True, type="secondary"):
                st.session_state.messages = []
                st.session_state.pop("pending_query", None)
                st.rerun()

        elif "So sánh" in selected_page:
            st.caption("THIẾT LẬP THỰC NGHIỆM")
            comp_top_k = st.slider(
                "Top-K tài liệu lấy ra",
                min_value=1,
                max_value=10,
                value=st.session_state.get("comp_top_k", 5),
                key="comp_top_k",
            )
            options["comp_top_k"] = comp_top_k

        elif "Đánh giá" in selected_page:
            st.caption("THÔNG TIN ĐÁNH GIÁ")
            st.markdown(
                """
                <div style="font-size: 0.8rem; color: #64748B; line-height: 1.45;">
                    So sánh A dense-only, B đầy đủ (HyDE + weighted RRF + listwise + MMR) và ablation trên 16 câu hỏi Golden Dataset.
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Footer info
        st.markdown(
            """
            <div style="margin-top: 2rem; font-size: 0.72rem; color: #94A3B8; text-align: center; border-top: 1px solid #F1F5F9; padding-top: 10px;">
                Lab 8 • RAG Pipeline Engineering<br/>Cohort 4 — Day 08
            </div>
            """,
            unsafe_allow_html=True,
        )

    return selected_page, options
