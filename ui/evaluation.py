"""A/B evaluation page rendering."""

import streamlit as st
from ui.components.hero import render_hero
from .config import load_evaluation_report, report_has_results


def render_evaluation_page() -> None:
    """Render the evaluation report dashboard."""
    render_hero(
        eyebrow="ĐÁNH GIÁ THỰC NGHIỆM RETRIEVAL",
        title="Đánh giá & So sánh A/B",
        subtitle="Theo dõi định lượng chất lượng tìm kiếm giữa Dense-only và Hybrid + RRF trên bộ 16 câu hỏi Golden Dataset.",
        badges=["RAGAS Framework", "16 Golden Test Cases", "Dual Configuration A/B"],
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
        return

    st.success("✅ Đã tải thành công báo cáo đánh giá A/B từ dự án.")
    st.markdown(
        f"""
        <div class="saas-card" style="margin-top: 1rem; line-height: 1.65;">
            {report}
        </div>
        """,
        unsafe_allow_html=True,
    )
