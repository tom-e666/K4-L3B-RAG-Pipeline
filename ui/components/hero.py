"""Hero banner component with status badges."""

import streamlit as st


def render_hero(
    eyebrow: str = "AI20K • RAG KNOWLEDGE ASSISTANT",
    title: str = "Trợ lý AI Thực Chiến",
    subtitle: str = "Tra cứu chương trình, lộ trình học và quy định từ tài liệu chính thức.",
    badges: list[str] | None = None,
) -> None:
    if badges is None:
        badges = [
            "Hybrid Retrieval",
            "Citation Enabled",
            "Knowledge Base Ready",
        ]

    badges_html = "".join(
        f'<span class="hero-badge"><span class="badge-dot"></span>{b}</span>'
        for b in badges
    )

    st.markdown(
        f"""
        <div class="hero-banner">
            <div class="hero-eyebrow">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                </svg>
                {eyebrow}
            </div>
            <h1 class="hero-title">{title}</h1>
            <p class="hero-subtitle">{subtitle}</p>
            <div class="hero-badges">
                {badges_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

