"""High-contrast visual styling shared by the Streamlit pages."""

import streamlit as st


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #17233b;
            --muted: #53647d;
            --line: #dce4f0;
            --surface: #ffffff;
            --canvas: #f6f8fc;
            --accent: #2457c5;
        }

        .stApp, [data-testid="stAppViewContainer"] { background: var(--canvas); color: var(--ink); }
        header[data-testid="stHeader"] { background: rgba(246, 248, 252, .96); }
        .block-container { max-width: 1100px; padding-top: 2.2rem; padding-bottom: 5rem; }
        [data-testid="stSidebar"] { background: var(--surface); border-right: 1px solid var(--line); }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] label { color: var(--ink); }
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: var(--muted); }
        [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"],
        [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] * { color: #fff !important; }

        .hero {
            padding: 1.65rem 1.85rem;
            border-radius: 20px;
            background: linear-gradient(125deg, #173983 0%, #2457c5 62%, #3475da 100%);
            color: #fff;
            margin-bottom: 1.5rem;
            box-shadow: 0 14px 28px rgba(23, 57, 131, .12);
        }
        .hero h1 { margin: .15rem 0 .55rem; color: #fff; font-size: clamp(1.7rem, 3.5vw, 2.4rem); line-height: 1.22; }
        .hero p { margin: 0; max-width: 720px; color: #e8f0ff; font-size: .98rem; line-height: 1.65; }
        .eyebrow { color: #dbe8ff; text-transform: uppercase; letter-spacing: .12em; font-size: .72rem; font-weight: 750; }
        .empty-state { text-align: center; padding: 2rem 1rem .85rem; color: var(--muted); }
        .empty-state h3 { color: var(--ink); font-size: 1.45rem; margin: 0 0 .55rem; }
        .empty-state div { line-height: 1.55; }

        div.stButton > button {
            width: 100%; min-height: 2.65rem; border-radius: 11px;
            border: 1px solid var(--line); background: var(--surface); color: var(--ink);
            font-weight: 550; text-align: left; white-space: normal;
        }
        div.stButton > button:hover { border-color: var(--accent); color: #173983; background: #eff5ff; }
        div.stButton > button[kind="primary"] { color: #fff; background: var(--accent); border-color: var(--accent); text-align: center; }
        div.stButton > button[kind="primary"]:hover { background: #173f9c; color: #fff; }
        [data-testid="stChatInput"] { background: var(--surface); border: 1px solid #bdcbe0; border-radius: 14px; }
        [data-testid="stChatInput"] textarea { color: var(--ink); background: transparent; }
        [data-testid="stChatInput"] textarea::placeholder { color: #687891; }
        [data-testid="stChatMessage"] { border: 1px solid var(--line); border-radius: 15px; background: var(--surface); }
        [data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }

        .source-card { border: 1px solid var(--line); border-radius: 12px; padding: .8rem .95rem; background: var(--surface); margin: .45rem 0; }
        .source-title { font-weight: 700; color: var(--ink); }
        .source-meta { color: var(--muted); font-size: .85rem; margin-top: .25rem; line-height: 1.55; }
        .source-meta a { color: #174aa9; font-weight: 650; }
        .answer-note { border-left: 4px solid #c98300; background: #fff8e8; padding: .75rem .95rem; border-radius: 0 10px 10px 0; color: #674300; margin: .5rem 0 1rem; }
        .metric-note { color: var(--muted); font-size: .88rem; }
        .pipeline-badge { display: inline-block; padding: .28rem .6rem; margin: .16rem .3rem .16rem 0; border-radius: 999px; background: #edf3ff; color: #254b91; border: 1px solid #d3e2ff; font-size: .76rem; font-weight: 650; }

        @media (max-width: 740px) {
            .block-container { padding: 1rem .75rem 5rem; }
            .hero { padding: 1.2rem; border-radius: 16px; }
            .empty-state { padding-top: 1.4rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
