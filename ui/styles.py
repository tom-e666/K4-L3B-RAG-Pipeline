"""Visual styling shared by all Streamlit pages."""

import streamlit as st


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root { --ink:#172033; --muted:#667085; }
        .stApp { background:#f7f9fc; color:var(--ink); }
        [data-testid="stSidebar"] { background:#fff; border-right:1px solid #e7ebf3; }
        .hero { padding:1.5rem 1.6rem; border-radius:20px; background:linear-gradient(135deg,#173b96,#3974e8); color:#fff; margin-bottom:1rem; }
        .hero h1 { margin:0 0 .35rem; font-size:clamp(1.65rem,4vw,2.35rem); letter-spacing:-.02em; }
        .hero p { margin:0; color:#e7edff; font-size:1rem; }
        .eyebrow { text-transform:uppercase; letter-spacing:.1em; font-size:.72rem; font-weight:700; color:#cbd8ff; }
        .empty-state { text-align:center; padding:2.2rem 1rem 1rem; color:var(--muted); }
        .empty-state h3 { color:var(--ink); margin-bottom:.4rem; }
        .source-card { border:1px solid #e1e7f0; border-radius:12px; padding:.7rem .85rem; background:#fff; margin:.4rem 0; }
        .source-title { font-weight:650; color:var(--ink); }
        .source-meta { color:var(--muted); font-size:.83rem; margin-top:.2rem; }
        .answer-note { border-left:4px solid #f59e0b; background:#fff8e8; padding:.7rem .9rem; border-radius:0 10px 10px 0; color:#7a4b00; margin:.5rem 0 1rem; }
        .metric-note { color:var(--muted); font-size:.88rem; }
        @media (max-width:640px) { .block-container { padding:1rem .75rem 5rem; } .hero { padding:1.2rem; } }
        </style>
        """,
        unsafe_allow_html=True,
    )
