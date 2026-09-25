"""Components for rendering comparison metrics, side-by-side cards, ranking table, and overlap matrix."""

from __future__ import annotations
import html
from typing import Any
import streamlit as st
from .message import prettify_source_name


def render_summary_metrics(results: dict[str, dict[str, Any]], query: str) -> None:
    """Render top summary metric cards with real operational statistics."""
    col1, col2, col3, col4 = st.columns(4)

    active_techs = len(results)
    valid_lats = [r["latency_ms"] for r in results.values() if r.get("status") == "success" and isinstance(r.get("latency_ms"), (int, float))]
    lowest_lat = min(valid_lats) if valid_lats else 0
    total_docs = sum(len(r.get("documents", [])) for r in results.values() if r.get("status") == "success")

    with col1:
        c1_html = (
            f'<div class="metric-card">'
            f'<span class="metric-label">Chiến lược</span>'
            f'<span class="metric-value">{active_techs}</span>'
            f'<span class="metric-subtext">Retrieval techniques</span>'
            f'</div>'
        )
        st.markdown(c1_html, unsafe_allow_html=True)

    with col2:
        c2_html = (
            f'<div class="metric-card">'
            f'<span class="metric-label">Độ trễ thấp nhất</span>'
            f'<span class="metric-value" style="color: #059669;">{int(round(lowest_lat))} <span style="font-size: 0.85rem;">ms</span></span>'
            f'<span class="metric-subtext">Real measured latency</span>'
            f'</div>'
        )
        st.markdown(c2_html, unsafe_allow_html=True)

    with col3:
        c3_html = (
            f'<div class="metric-card">'
            f'<span class="metric-label">Tổng trích đoạn</span>'
            f'<span class="metric-value" style="color: #2563EB;">{total_docs}</span>'
            f'<span class="metric-subtext">Total retrieved chunks</span>'
            f'</div>'
        )
        st.markdown(c3_html, unsafe_allow_html=True)

    with col4:
        c4_html = (
            f'<div class="metric-card">'
            f'<span class="metric-label">Tính nhất quán</span>'
            f'<span class="metric-value" style="color: #10B981; font-size: 1.25rem; padding-top: 4px;">Same input ✓</span>'
            f'<span class="metric-subtext">Single unified query</span>'
            f'</div>'
        )
        st.markdown(c4_html, unsafe_allow_html=True)

    # Subtle disclaimer on non-comparable raw scores (Task 7)
    note_html = (
        f'<div style="font-size: 0.76rem; color: #64748B; margin-top: 0.5rem; margin-bottom: 0.2rem;">'
        f'ℹ️ <b>Lưu ý về điểm số:</b> Điểm số giữa các kỹ thuật sử dụng thang đo khác nhau '
        f'(Dense: Cosine similarity [0–1], BM25: TF-IDF score [0–∞), RRF: Thứ hạng đảo [0–0.033]) '
        f'và không nên so sánh trực tiếp độ lớn điểm số giữa các cột.'
        f'</div>'
    )
    st.markdown(note_html, unsafe_allow_html=True)


def render_side_by_side_cards(results: dict[str, dict[str, Any]]) -> None:
    """Render side-by-side technique result cards with clear document rows."""
    tech_keys = list(results.keys())
    if not tech_keys:
        return

    # Find the truly fastest method based on real measured latency (Task 6)
    valid_techniques = [
        r for r in results.values()
        if r.get("status") == "success" and isinstance(r.get("latency_ms"), (int, float))
    ]
    fastest_tech_name = (
        min(valid_techniques, key=lambda x: x["latency_ms"])["technique"]
        if valid_techniques
        else None
    )

    for i in range(0, len(tech_keys), 2):
        cols = st.columns(2)
        for c_idx, k_idx in enumerate([i, i + 1]):
            if k_idx < len(tech_keys):
                t_name = tech_keys[k_idx]
                data = results[t_name]
                with cols[c_idx]:
                    if data.get("status") != "success":
                        err_msg = html.escape(str(data.get("error", "Không thể hoàn thành truy xuất")))
                        fail_html = (
                            f'<div class="technique-card" style="border-color: #FCA5A5;">'
                            f'<div class="technique-header">'
                            f'<div class="technique-name">⚠ {html.escape(t_name)}</div>'
                            f'<span class="latency-badge" style="background:#FEE2E2; color:#B91C1C;">Failed</span>'
                            f'</div>'
                            f'<div style="color: #B91C1C; font-size: 0.85rem; padding: 0.5rem 0;">'
                            f'Lỗi: {err_msg}'
                            f'</div>'
                            f'</div>'
                        )
                        st.markdown(fail_html, unsafe_allow_html=True)
                        continue

                    lat = data.get("latency_ms", 0)
                    is_fastest = (t_name == fastest_tech_name and len(valid_techniques) > 1)
                    lat_class = "latency-badge latency-fast" if is_fastest else "latency-badge"
                    lat_text = f"{int(round(lat))} ms • Nhanh nhất" if is_fastest else f"{int(round(lat))} ms"

                    docs = data.get("documents", [])
                    doc_count = len(docs)
                    top_score = data.get("top_score")
                    score_str = f"{float(top_score):.3f}" if isinstance(top_score, (int, float)) else "N/A"

                    # Generate clean document rows without multi-line indentation (Task 3, 4, 8)
                    docs_rows = []
                    for rank, doc in enumerate(docs[:5], 1):
                        meta = doc.get("metadata") or {}
                        raw_source = meta.get("source") or "Tài liệu"
                        title = meta.get("title") or raw_source
                        friendly = prettify_source_name(raw_source, title)
                        doc_score = doc.get("score")
                        d_score_str = f"{float(doc_score):.3f}" if isinstance(doc_score, (int, float)) else "N/A"

                        escaped_title = html.escape(str(title))
                        escaped_friendly = html.escape(str(friendly))
                        escaped_source = html.escape(str(raw_source))

                        row_html = (
                            f'<div class="doc-item-row">'
                            f'<div class="doc-item-left">'
                            f'<div class="doc-title-line">'
                            f'<span class="doc-rank">#{rank}</span>'
                            f'<span class="doc-name" title="{escaped_title}">{escaped_friendly}</span>'
                            f'</div>'
                            f'<div class="doc-sub-line">'
                            f'<span class="doc-source-file">{escaped_source}</span>'
                            f'</div>'
                            f'</div>'
                            f'<div class="doc-item-right">'
                            f'<span class="doc-score">{d_score_str}</span>'
                            f'</div>'
                            f'</div>'
                        )
                        docs_rows.append(row_html)

                    docs_html = "".join(docs_rows) if docs_rows else "<div style='color:#94A3B8; font-size:0.8rem; padding: 0.5rem;'>Không tìm thấy tài liệu phù hợp.</div>"

                    card_html = (
                        f'<div class="technique-card">'
                        f'<div class="technique-header">'
                        f'<div class="technique-name">{html.escape(t_name)}</div>'
                        f'<span class="{lat_class}">{lat_text}</span>'
                        f'</div>'
                        f'<div class="technique-meta-bar">'
                        f'<span>Tài liệu tìm thấy: <b style="color:#0F172A;">{doc_count}</b></span>'
                        f'<span>Top score: <b class="score-highlight">{score_str}</b></span>'
                        f'</div>'
                        f'<div class="doc-list-container">{docs_html}</div>'
                        f'</div>'
                    )
                    st.markdown(card_html, unsafe_allow_html=True)

                    with st.expander(f"Xem chi tiết trích đoạn ({t_name})", expanded=False):
                        for r_idx, doc in enumerate(docs, 1):
                            meta = doc.get("metadata") or {}
                            st.caption(f"**#{r_idx}. {meta.get('title') or meta.get('source')}** — Score: `{doc.get('score', 'N/A')}`")
                            st.text(doc.get("content", "").strip()[:350] + "…")


def render_ranking_comparison_table(results: dict[str, dict[str, Any]]) -> None:
    """Render table showing how the same documents rank differently across methods."""
    st.markdown("### 🏆 Thứ hạng tài liệu giữa các kỹ thuật")
    st.caption("Quan sát sự dịch chuyển thứ hạng của cùng một tài liệu khi áp dụng các chiến lược retrieval khác nhau.")

    tech_names = [k for k, v in results.items() if v.get("status") == "success"]
    if not tech_names:
        st.info("Chưa có kết quả để lập bảng xếp hạng.")
        return

    # Collect all unique documents across all techniques
    doc_map: dict[str, str] = {}
    tech_ranks: dict[str, dict[str, int]] = {t: {} for t in tech_names}

    for t in tech_names:
        docs = results[t].get("documents", [])
        for rank, doc in enumerate(docs, 1):
            doc_id = doc["id"]
            if doc_id not in doc_map:
                meta = doc.get("metadata") or {}
                title = meta.get("title") or meta.get("source") or doc_id
                doc_map[doc_id] = prettify_source_name(meta.get("source", ""), title)
            tech_ranks[t][doc_id] = rank

    if not doc_map:
        st.info("Không có tài liệu nào được tìm thấy.")
        return

    # Sort documents by minimum rank across techniques
    sorted_doc_ids = sorted(
        doc_map.keys(),
        key=lambda d_id: min(tech_ranks[t].get(d_id, 99) for t in tech_names),
    )[:8]

    # Build HTML Table safely without leading spaces
    headers_html = "".join(f"<th>{html.escape(t)}</th>" for t in tech_names)
    rows_html = []

    for d_id in sorted_doc_ids:
        doc_name = html.escape(doc_map[d_id])
        tds = [f"<td style='font-weight: 600;'>{doc_name}</td>"]
        for t in tech_names:
            rank = tech_ranks[t].get(d_id)
            if rank == 1:
                pill = '<span class="rank-pill rank-pill-1">🥇 #1</span>'
            elif rank is not None:
                pill = f'<span class="rank-pill">#{rank}</span>'
            else:
                pill = '<span class="rank-pill rank-pill-none">—</span>'
            tds.append(f"<td style='text-align: center;'>{pill}</td>")
        rows_html.append(f"<tr>{''.join(tds)}</tr>")

    table_content = "".join(rows_html)
    table_html = (
        f'<table class="ranking-table">'
        f'<thead><tr><th style="width: 35%;">Tài liệu / Trích đoạn</th>{headers_html}</tr></thead>'
        f'<tbody>{table_content}</tbody>'
        f'</table>'
    )
    st.markdown(table_html, unsafe_allow_html=True)


def render_document_overlap_matrix(results: dict[str, dict[str, Any]]) -> None:
    """Render comparison of document overlap between methods."""
    st.markdown("### 🔄 Độ trùng lặp kết quả (Document Overlap)")
    st.caption("Tỷ lệ và số lượng tài liệu/chunk chung được truy xuất đồng thời giữa các cặp chiến lược.")

    tech_names = [k for k, v in results.items() if v.get("status") == "success"]
    if len(tech_names) < 2:
        return

    # Compute pairwise overlaps
    pairs = []
    if "Dense Retrieval" in results and "BM25 (Lexical)" in results:
        pairs.append(("Dense Retrieval", "BM25 (Lexical)"))
    if "Dense Retrieval" in results and "Hybrid Search" in results:
        pairs.append(("Dense Retrieval", "Hybrid Search"))
    if "BM25 (Lexical)" in results and "Hybrid Search" in results:
        pairs.append(("BM25 (Lexical)", "Hybrid Search"))
    if "Hybrid Search" in results and "Hybrid + RRF" in results:
        pairs.append(("Hybrid Search", "Hybrid + RRF"))

    if not pairs and len(tech_names) >= 2:
        for i in range(len(tech_names) - 1):
            pairs.append((tech_names[i], tech_names[i + 1]))

    cols = st.columns(len(pairs))
    for idx, (t1, t2) in enumerate(pairs):
        ids1 = {d["id"] for d in results[t1].get("documents", [])}
        ids2 = {d["id"] for d in results[t2].get("documents", [])}
        overlap = len(ids1.intersection(ids2))
        total_k = max(len(ids1), len(ids2), 1)
        ratio = (overlap / total_k) * 100

        with cols[idx]:
            card_html = (
                f'<div class="saas-card" style="padding: 0.9rem; text-align: center;">'
                f'<div style="font-size: 0.74rem; font-weight: 700; color: #64748B; margin-bottom: 0.35rem;">{html.escape(t1)} ↔ {html.escape(t2)}</div>'
                f'<div style="font-size: 1.35rem; font-weight: 800; color: #2563EB; font-family: \'JetBrains Mono\', monospace;">{overlap} / {total_k}</div>'
                f'<div style="font-size: 0.72rem; color: #059669; font-weight: 600; margin-top: 2px;">{ratio:.0f}% trùng khớp</div>'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)


def render_technique_explanations() -> None:
    """Render 4 small educational explanation cards."""
    st.markdown("### 💡 Hiểu nhanh các kỹ thuật")
    col1, col2, col3, col4 = st.columns(4)

    expls = [
        ("🔍 Dense Retrieval", "Hiểu tương đồng về ngữ nghĩa thông qua vector embedding (Cosine Similarity)."),
        ("📝 BM25", "Tìm kiếm dựa trên mức độ khớp từ khóa chính xác và độ quan trọng của từ (TF-IDF cải tiến)."),
        ("⚡ Hybrid Search", "Kết hợp semantic search và keyword search để tăng khả năng tìm đúng tài liệu toàn diện."),
        ("🎯 RRF", "Dung hợp thứ hạng dense và BM25 bằng Reciprocal Rank Fusion (RRF)."),
    ]

    for col, (title, desc) in zip([col1, col2, col3, col4], expls):
        with col:
            c_html = (
                f'<div class="expl-card">'
                f'<div class="expl-card-title">{title}</div>'
                f'<p class="expl-card-desc">{desc}</p>'
                f'</div>'
            )
            st.markdown(c_html, unsafe_allow_html=True)
