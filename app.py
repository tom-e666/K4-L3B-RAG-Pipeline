"""Application entry point for the Streamlit AI20K assistant."""

import streamlit as st
from dotenv import load_dotenv

from ui.chat import render_chat_page
from ui.evaluation import render_evaluation_page
from ui.styles import inject_styles

load_dotenv()


def main() -> None:
    st.set_page_config(page_title="Trợ lý AI Thực Chiến", page_icon="🤖", layout="wide")
    inject_styles()
    if "messages" not in st.session_state:
        st.session_state.messages = []

    with st.sidebar:
        page = st.radio(
            "Điều hướng",
            ["Chat", "Đánh giá A/B"],
            key="page",
            label_visibility="collapsed",
        )

    if page == "Chat":
        render_chat_page()
    else:
        render_evaluation_page()


if __name__ == "__main__":
    main()
