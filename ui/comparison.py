"""Comparison dashboard page: One Query → Multiple Retrieval Techniques → Side-by-side Analysis."""

from __future__ import annotations
import time
from typing import Any
import streamlit as st

from ui.components.query_flow import render_query_flow
from ui.components.comparison_cards import (
    render_summary_metrics,
    render_side_by_side_cards,
    render_ranking_comparison_table,
    render_document_overlap_matrix,
    render_technique_explanations,
)

AVAILABLE_TECHNIQUES = [
    "Dense Retrieval",
    "BM25 (Lexical)",
    "Hybrid Search",
    "Hybrid + Reranker",
]


def run_single_technique(name: str, query: str, top_k: int) -> dict[str, Any]:
    """Execute a single retrieval technique safely and measure real latency."""
    t0 = time.perf_counter()
    try:
        from src.task5_semantic_search import semantic_search
        from src.task6_lexical_search import lexical_search
        from src.task7_reranking import rerank_rrf

        if name == "Dense Retrieval":
            docs = semantic_search(query, top_k=top_k)
        elif name == "BM25 (Lexical)":
            docs = lexical_search(query, top_k=top_k)
        elif name == "Hybrid Search":
            # Simple combined union of Dense and BM25
            dense = semantic_search(query, top_k=top_k)
            sparse = lexical_search(query, top_k=top_k)
            seen = set()
            docs = []
            for i in range(max(len(dense), len(sparse))):
                if i < len(dense) and dense[i]["id"] not in seen:
                    seen.add(dense[i]["id"])
                    c = dict(dense[i])
                    c["retrieval_method"] = "hybrid"
                    docs.append(c)
                if i < len(sparse) and sparse[i]["id"] not in seen:
                    seen.add(sparse[i]["id"])
                    c = dict(sparse[i])
                    c["retrieval_method"] = "hybrid"
                    docs.append(c)
                if len(docs) >= top_k:
                    break
            docs = docs[:top_k]
        elif name == "Hybrid + Reranker":
            dense = semantic_search(query, top_k=top_k * 2)
            sparse = lexical_search(query, top_k=top_k * 2)
            docs = rerank_rrf([dense, sparse], top_k=top_k, k=60)
        else:
            raise ValueError(f"Technique {name} not supported")

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        top_score = docs[0]["score"] if docs else None

        return {
            "technique": name,
            "latency_ms": elapsed_ms,
            "documents": docs,
            "top_score": top_score,
            "status": "success",
        }
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return {
            "technique": name,
            "latency_ms": elapsed_ms,
            "documents": [],
            "top_score": None,
            "status": "failed",
            "error": str(exc),
        }


def render_comparison_page(comp_top_k: int = 5) -> None:
    """Render the dedicated retrieval comparison dashboard."""
    header_html = (
        '<div style="margin-bottom: 1.4rem;">'
        '<div style="font-size: 0.74rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #2563EB; margin-bottom: 4px;">'
        'RETRIEVAL STRATEGY BENCHMARKING'
        '</div>'
        '<h1 style="font-size: 2.1rem; font-weight: 800; color: #0F172A; margin: 0 0 0.35rem 0; letter-spacing: -0.025em;">'
        'So sánh các kỹ thuật Retrieval'
        '</h1>'
        '<p style="font-size: 0.96rem; color: #64748B; margin: 0; line-height: 1.5;">'
        'Chạy cùng một câu hỏi qua nhiều chiến lược retrieval để so sánh trực quan chất lượng kết quả, độ trễ và độ bao phủ tài liệu.'
        '</p>'
        '</div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)

    # Technique selection chips
    st.markdown("<div style='font-size: 0.8rem; font-weight: 700; color: #475569; margin-bottom: 6px;'>CHỌN CHIẾN LƯỢC SO SÁNH:</div>", unsafe_allow_html=True)
    chip_cols = st.columns(4)
    selected_techs = []

    # Store checkbox states in session state
    for idx, tech in enumerate(AVAILABLE_TECHNIQUES):
        with chip_cols[idx]:
            state_key = f"chk_tech_{idx}"
            if state_key not in st.session_state:
                st.session_state[state_key] = True
            is_checked = st.checkbox(tech, value=st.session_state[state_key], key=state_key)
            if is_checked:
                selected_techs.append(tech)

    if not selected_techs:
        st.warning("Vui lòng chọn ít nhất một chiến lược retrieval để bắt đầu so sánh.")
        selected_techs = AVAILABLE_TECHNIQUES[:2]

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Query input container
    query_col, btn_col = st.columns([5, 1])
    with query_col:
        query_val = st.session_state.get("comparison_query_input", "")
        comp_query = st.text_input(
            "Nhập câu hỏi cần so sánh",
            value=query_val,
            placeholder="Nhập câu hỏi cần so sánh (ví dụ: Điều kiện tham gia chương trình AI20K là gì?)...",
            label_visibility="collapsed",
            key="comp_text_input",
        )
    with btn_col:
        run_btn = st.button("So sánh →", type="primary", use_container_width=True)

    # Example query suggestions
    example_queries = [
        "Điều kiện tham gia chương trình AI20K là gì?",
        "Lộ trình 5 giai đoạn cuộc thi Hackathon gồm những mốc nào?",
        "Ban tổ chức yêu cầu những deliverables nào cho Demo Day?",
        "Thời hạn nộp báo cáo Mentor Duty để được cộng XP là khi nào?",
    ]
    st.markdown("<div style='font-size: 0.76rem; color: #94A3B8; margin-top: 4px;'>Gợi ý câu hỏi:</div>", unsafe_allow_html=True)
    sugg_cols = st.columns(len(example_queries))
    for s_idx, eq in enumerate(example_queries):
        with sugg_cols[s_idx]:
            if st.button(eq, key=f"btn_comp_sugg_{s_idx}", use_container_width=True):
                st.session_state.comparison_query_input = eq
                comp_query = eq
                run_btn = True
                st.rerun()

    # Trigger comparison run
    if run_btn and comp_query.strip():
        progress_bar = st.progress(0.0)
        status_box = st.empty()

        results = {}
        total_steps = len(selected_techs)

        for s_idx, t_name in enumerate(selected_techs):
            status_box.markdown(f"**Đang thực thi:** *{t_name}*...")
            res = run_single_technique(t_name, comp_query.strip(), top_k=comp_top_k)
            results[t_name] = res
            progress_bar.progress((s_idx + 1) / total_steps)

        status_box.empty()
        progress_bar.empty()

        st.session_state.comparison_results = results
        st.session_state.last_compared_query = comp_query.strip()

    # Render results if available
    saved_results = st.session_state.get("comparison_results")
    last_query = st.session_state.get("last_compared_query")

    if saved_results and last_query:
        st.markdown("<hr style='margin: 1.5rem 0; border: none; border-top: 1px solid #E2E8F0;' />", unsafe_allow_html=True)

        # 1. Summary Metrics
        render_summary_metrics(saved_results, last_query)

        st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

        # 2. Side-by-side Result Cards
        st.markdown("### 📊 Kết quả truy xuất song song (Side-by-side Results)")
        st.caption(f"Dữ liệu top {comp_top_k} đoạn trích truy xuất theo từng kỹ thuật cho câu hỏi: *\"{last_query}\"*")
        render_side_by_side_cards(saved_results)

        st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

        # 3. Document Overlap Matrix
        render_document_overlap_matrix(saved_results)

        st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

        # 4. Ranking Comparison Table
        render_ranking_comparison_table(saved_results)

        st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

        # 5. Technical Query Flow Diagram
        render_query_flow()

        st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

        # 6. Educational Technique Explanations
        render_technique_explanations()
    else:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        render_query_flow()
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        render_technique_explanations()

