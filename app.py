"""Application entry point for the Streamlit AI20K assistant."""

import streamlit as st
from dotenv import load_dotenv

from ui.styles import inject_styles
from ui.components.sidebar import render_sidebar
from ui.chat import render_chat_page
from ui.comparison import render_comparison_page
from ui.evaluation import render_evaluation_page

load_dotenv()


def main() -> None:
    st.set_page_config(
        page_title="Trợ lý AI Thực Chiến — AI20K",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_styles()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    selected_page, options = render_sidebar()

    if "Chat" in selected_page:
        render_chat_page(top_k=options.get("top_k", 5))
    elif "So sánh" in selected_page:
        render_comparison_page(comp_top_k=options.get("comp_top_k", 5))
    else:
        render_evaluation_page()


if __name__ == "__main__":
    main()
