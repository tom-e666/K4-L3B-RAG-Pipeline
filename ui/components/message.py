"""Chat message formatting, citation parsing, and source card rendering."""

from __future__ import annotations
import re
from typing import Any
import streamlit as st


def prettify_source_name(source: str, title: str | None = None) -> str:
    """Rút gọn và làm đẹp tên nguồn trích dẫn."""
    if title and len(title.strip()) > 3 and not title.endswith(".json") and not title.endswith(".docx") and not title.endswith(".pdf"):
        # Truncate if title is very long
        clean_title = title.strip()
        if len(clean_title) > 40:
            return clean_title[:38] + "…"
        return clean_title

    mapping = {
        "20K-AI-Handbook-ver2.1.pdf": "Sổ tay học viên AI20K",
        "quy-che-ai-product-hackathon.docx": "Quy chế Hackathon AI",
        "quy-dinh-deliverables-demo-day.docx": "Quy định 10 Deliverables Demo Day",
        "quy-dinh-mentor-duty.docx": "Quy định Mentor Duty",
        "01_portal_gioi_thieu_chuong_trinh_ai20k.json": "Cổng thông tin AI20K & Q&A",
        "02_thong_tin_tuyen_sinh_khoa_co_ban.json": "Tuyển sinh Khóa Cơ bản",
        "03_vingroup_khai_giang_khoa_1.json": "Khai giảng Khóa 1 AI20K",
        "04_ky_thi_danh_gia_nang_luc_3_ngay.json": "Kỳ thi đánh giá năng lực 3 ngày",
        "05_tuyen_sinh_khoa_2_3.json": "Tuyển sinh Khóa 2–3",
        "06_huong_dan_khoi_tao_du_an_template_ai20k.json": "Hướng dẫn Template Repo",
    }
    for key, val in mapping.items():
        if key in source:
            return val

    # Clean raw filenames
    clean = re.sub(r"^\d+_", "", source)
    clean = re.sub(r"\.(json|pdf|docx|md)$", "", clean)
    clean = clean.replace("_", " ").replace("-", " ").title()
    return clean[:35]


def format_citations_to_badges(answer_text: str) -> str:
    """Chuyển đổi chuỗi [Source: ... Title: ...] thành các badge pill thanh lịch."""
    # Pattern 1: [Source: xxx, Title: yyy] or [Document X | Title: yyy | Source: xxx]
    pattern1 = r"\[Source:\s*([^,\]]+)(?:,\s*Title:\s*([^\]]+))?\]"
    pattern2 = r"\[Document\s*\d+\s*\|\s*Title:\s*([^|\]]+)\s*\|\s*Source:\s*([^\]]+)\]"

    def repl1(match):
        source = match.group(1).strip()
        title = match.group(2).strip() if match.group(2) else None
        friendly = prettify_source_name(source, title)
        return f'<span class="citation-badge">📌 Nguồn: {friendly}</span>'

    def repl2(match):
        title = match.group(1).strip()
        source = match.group(2).strip()
        friendly = prettify_source_name(source, title)
        return f'<span class="citation-badge">📌 Nguồn: {friendly}</span>'

    text = re.sub(pattern1, repl1, answer_text)
    text = re.sub(pattern2, repl2, text)
    return text


def render_source_cards(sources: list[dict[str, Any]]) -> None:
    """Hiển thị các card nguồn tham khảo chi tiết theo yêu cầu."""
    if not sources:
        return

    with st.expander(f"▸ Nguồn tham khảo ({len(sources)})", expanded=False):
        for index, source in enumerate(sources, 1):
            metadata = source.get("metadata") or {}
            raw_source = metadata.get("source") or "Tài liệu"
            title = metadata.get("title") or raw_source
            friendly_name = prettify_source_name(raw_source, title)
            url = metadata.get("url")
            method = source.get("retrieval_method") or "hybrid"
            score = source.get("score")
            content = source.get("content") or ""

            # Excerpt snippet: first 250 characters
            snippet = content.strip().replace("\n", " ")
            if len(snippet) > 280:
                snippet = snippet[:275] + "…"

            score_str = f"{float(score):.3f}" if isinstance(score, (int, float)) else "N/A"
            method_badge = method.upper()

            link_html = (
                f'<a href="{url}" target="_blank" style="color: #2563EB; font-weight:600; text-decoration: none;">Mở liên kết ↗</a>'
                if url
                else '<span style="color: #94A3B8;">Tài liệu nội bộ</span>'
            )

            st.markdown(
                f"""
                <div class="source-card">
                    <div class="source-card-header">
                        <div class="source-title">{index}. {friendly_name}</div>
                        <div class="source-tags">
                            <span class="tag-pill tag-pill-highlight">Method: {method_badge}</span>
                            <span class="tag-pill">Score: {score_str}</span>
                        </div>
                    </div>
                    <div class="source-snippet">"{snippet}"</div>
                    <div class="source-meta-row">
                        <span>Tệp: <code>{raw_source}</code></span>
                        <span>{link_html}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_message(role: str, content: str, sources: list[dict] | None = None, safe_refusal: bool = False) -> None:
    """Render a single user or assistant chat message."""
    if role == "user":
        with st.chat_message("user", avatar="🧑"):
            st.markdown(content)
    else:
        with st.chat_message("assistant", avatar="🤖"):
            if safe_refusal:
                st.markdown(
                    """
                    <div class="answer-note">
                        <b>Thông báo:</b> Thông tin này chưa đủ bằng chứng xác thực trong bộ tài liệu AI20K hiện có.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Format formatted content with badges
            clean_content = format_citations_to_badges(content)
            st.markdown(clean_content, unsafe_allow_html=True)

            if sources:
                render_source_cards(sources)

