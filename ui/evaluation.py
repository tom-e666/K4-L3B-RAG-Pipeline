"""A/B evaluation page."""

import streamlit as st

from .config import load_evaluation_report, report_has_results


def render_evaluation_page() -> None:
    st.markdown(
        '<section class="hero"><div class="eyebrow">Đánh giá retrieval</div>'
        '<h1>So sánh A/B</h1><p>Theo dõi chất lượng tìm kiếm trên cùng bộ câu hỏi đánh giá.</p></section>',
        unsafe_allow_html=True,
    )
    report = load_evaluation_report()
    if not report_has_results(report):
        st.info(
            "Chưa có dữ liệu đánh giá A/B. Khi nhóm hoàn tất chạy evaluation, "
            "hãy cập nhật RESULT.md; các chỉ số sẽ được hiển thị tại đây."
        )
        st.markdown("#### Bố cục kết quả sẽ gồm")
        st.caption("Config A: dense-only · Config B: hybrid + RRF")
        st.dataframe(
            {
                "Chỉ số": ["Faithfulness", "Answer relevance", "Context recall", "Context precision", "Trung bình"],
                "Config A — dense-only": ["Chưa có dữ liệu"] * 5,
                "Config B — hybrid + RRF": ["Chưa có dữ liệu"] * 5,
            },
            hide_index=True,
            use_container_width=True,
        )
        st.markdown(
            '<div class="metric-note">Faithfulness: câu trả lời có bám nguồn không. '
            'Relevance: câu trả lời có đúng câu hỏi không. Recall/precision: hệ thống có lấy đủ và đúng đoạn tài liệu cần thiết không.</div>',
            unsafe_allow_html=True,
        )
        return
    st.success("Đã tải báo cáo đánh giá từ dự án.")
    st.markdown(report)
