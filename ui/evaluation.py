"""Interactive comparison of recorded RAG strategies on the golden set."""

from __future__ import annotations

import csv
import io
from statistics import mean

import pandas as pd
import streamlit as st

from .config import load_evaluation_report, load_evaluation_runs, report_has_results
from .components.hero import render_hero


LABELS = {
    "A": "A · Dense-only",
    "B": "B · HyDE + Hybrid + MMR",
    "B_no_HyDE": "B · Không HyDE",
    "A_dense": "A · Dense-only",
    "remote_weighted": "Weighted RRF",
    "remote_listwise": "Weighted RRF + Listwise",
    "B_full": "B · HyDE + WRRF + Listwise + MMR",
}
METRICS = (
    ("faithfulness", "Faithfulness"),
    ("answer_relevance", "Answer relevance"),
    ("context_recall", "Context recall"),
    ("context_precision", "Context precision"),
)
CASE_TYPES = {
    "semantic": "Semantic / paraphrase",
    "keyword": "Keyword / tên riêng",
    "multi_source": "Nhiều nguồn",
    "refusal": "Ngoài phạm vi",
}
CARD_LABELS = {
    "A": "A · Dense",
    "A_dense": "A · Dense",
    "B": "B · Hybrid",
    "B_full": "B · Full",
    "B_no_HyDE": "B · No HyDE",
    "remote_weighted": "Weighted RRF",
    "remote_listwise": "Listwise",
}


def macro(scores: dict) -> float:
    return mean(float(scores[key]) for key, _ in METRICS)


def _failure_summary(summary: dict, detail_count: int) -> str:
    if "hyde_attempts" in summary:
        return (
            f"HyDE lỗi {summary['hyde_failures']}/{summary['hyde_attempts']} · "
            f"Rerank fallback {summary['rerank_failures']}/{summary['rerank_attempts']} · "
            f"MMR lỗi {summary['mmr_failures']}/{summary['mmr_attempts']} · "
            f"Evaluator lỗi {summary['errors']['judge']}/{detail_count}"
        )
    if "rerank_attempts" in summary:
        return (
            f"Rerank fallback {summary['rerank_failures']}/{summary['rerank_attempts']} · "
            f"Evaluator lỗi {summary['errors']['judge']}/{detail_count}"
        )
    attempts, failures = summary["attempts"], summary["failures"]
    return (
        f"HyDE lỗi {failures['hyde']}/{attempts['hyde']} · "
        f"Rerank fallback {failures['rerank']}/{attempts['rerank']} · "
        f"Evaluator lỗi {failures['judge']}/{attempts['judge']}"
    )


def _csv_export(rows: list[dict]) -> str:
    fields = ["id", "case_type", "question", "config", "faithfulness", "answer_relevance",
              "context_recall", "context_precision", "latency_seconds", "citations_valid", "answer"]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def render_evaluation_page() -> None:
    render_hero(
        eyebrow="AI20K • GOLDEN SET",
        title="So sánh chiến lược RAG",
        subtitle="Chọn lượt đánh giá, đối chiếu nhiều chiến lược và xem bằng chứng theo từng câu hỏi.",
        badges=["16 Golden Cases", "DeepSeek", "A/B + Ablation"],
    )
    runs = load_evaluation_runs()
    if not runs:
        st.info("Chưa có dữ liệu eval. Chạy script trong `group_project/evaluation` trước khi mở trang này.")
        return

    run_map = {run["id"]: run for run in runs}
    run_id = st.selectbox("Lượt đánh giá", list(run_map), format_func=lambda key: run_map[key]["label"])
    run = run_map[run_id]
    summary, details = run["summary"], run["details"]
    all_configs = list(summary["configs"])
    selected = st.multiselect(
        "Chiến lược cần so sánh", all_configs, default=all_configs,
        format_func=lambda key: LABELS.get(key, key), key=f"strategies-{run_id}",
    )
    if not selected:
        st.info("Chọn ít nhất một chiến lược để xem kết quả.")
        return

    st.caption(
        f"{summary['dataset_size'] if 'dataset_size' in summary else len(set(row['id'] for row in details))} case · "
        f"{summary['corpus_chunks']} chunks · top_k={summary['top_k']} · "
        f"Generator/evaluator: {summary['model']} · Embedding: {summary['embedding_model']}"
    )
    st.info(_failure_summary(summary, len(details)))

    st.subheader("Tổng quan")
    baseline_key = "A_dense" if "A_dense" in summary["configs"] else "A"
    baseline_score = macro(summary["configs"][baseline_key])
    cards = st.columns(len(selected))
    for col, config in zip(cards, selected):
        score = macro(summary["configs"][config])
        with col:
            st.metric(CARD_LABELS.get(config, config), f"{score:.3f}",
                      delta=f"{score - baseline_score:+.3f} so với A" if config != baseline_key else None)
            st.caption(f"p50 {summary['configs'][config]['p50_latency_seconds']:.2f} s")

    chart_data = pd.DataFrame(
        [{"Strategy": LABELS.get(config, config), "Điểm trung bình": macro(summary["configs"][config])}
         for config in selected]
    ).set_index("Strategy")
    st.bar_chart(chart_data, height=220, color="#2457C5")

    comparison = []
    for metric, label in METRICS:
        comparison.append({"Chỉ số": label, **{
            LABELS.get(config, config): round(summary["configs"][config][metric], 3)
            for config in selected
        }})
    comparison.append({"Chỉ số": "Trung bình 4 metric", **{
        LABELS.get(config, config): round(macro(summary["configs"][config]), 3)
        for config in selected
    }})
    comparison.append({"Chỉ số": "p50 latency (giây)", **{
        LABELS.get(config, config): summary["configs"][config]["p50_latency_seconds"]
        for config in selected
    }})
    st.dataframe(comparison, hide_index=True, width="stretch")
    if run_id == "historical":
        st.caption("p50 của lượt Gemini cũ bao gồm thời gian chấm; hai lượt DeepSeek chỉ đo retrieval + generation.")
    else:
        st.caption("p50 chỉ đo retrieval + generation. Context metrics dùng các đoạn bằng chứng kỳ vọng trong golden set.")

    st.subheader("Theo loại câu hỏi")
    category_rows = []
    for case_type in CASE_TYPES:
        for config in selected:
            rows = [row for row in details if row["case_type"] == case_type and row["config"] == config]
            if rows:
                category_rows.append({
                    "Loại": CASE_TYPES[case_type], "Chiến lược": LABELS.get(config, config),
                    "Số case": len(rows),
                    "Relevance": round(mean(row["answer_relevance"] for row in rows), 3),
                    "Context recall": round(mean(row["context_recall"] for row in rows), 3),
                })
    st.dataframe(category_rows, hide_index=True, width="stretch")

    st.subheader("Đối chiếu từng câu hỏi")
    case_types = list(CASE_TYPES)
    chosen_types = st.multiselect(
        "Lọc loại case", case_types, default=case_types,
        format_func=lambda key: CASE_TYPES[key], key=f"case-types-{run_id}",
    )
    filtered = [row for row in details if row["config"] in selected and row["case_type"] in chosen_types]
    case_ids = list(dict.fromkeys(row["id"] for row in filtered))
    if not case_ids:
        st.info("Không có case nào khớp bộ lọc.")
        return
    questions = {row["id"]: row["question"] for row in filtered}
    case_id = st.selectbox("Câu hỏi", case_ids, format_func=lambda key: f"{key} · {questions[key]}",
                           key=f"case-{run_id}")
    case_rows = [row for row in filtered if row["id"] == case_id]
    st.dataframe([{
        "Chiến lược": LABELS.get(row["config"], row["config"]),
        "Faithfulness": row["faithfulness"], "Relevance": row["answer_relevance"],
        "Recall": round(row["context_recall"], 3), "Precision": round(row["context_precision"], 3),
        "Latency (s)": row["latency_seconds"],
    } for row in case_rows], hide_index=True, width="stretch")

    answer_tabs = st.tabs([LABELS.get(row["config"], row["config"]) for row in case_rows])
    for tab, row in zip(answer_tabs, case_rows):
        with tab:
            st.markdown(row["answer"])
            st.caption(f"{len(row['sources'])} chunks · Citation hợp lệ: "
                       f"{'Có' if row.get('citations_valid', True) else 'Không'}")
            with st.expander("Các chunks được truy xuất"):
                for source in row["sources"]:
                    st.code(source, language=None)

    st.download_button("Tải CSV các case đang lọc", _csv_export(filtered),
                       file_name=f"rag_eval_{run_id}.csv", mime="text/csv", key=f"download-{run_id}")

    with st.expander("Xem mọi lượt chạy đã lưu"):
        st.warning("Chỉ so sánh trực tiếp các chiến lược trong cùng một lượt: prompt, model và cách đo latency khác nhau giữa các lượt.")
        history = []
        for item in runs:
            for config, scores in item["summary"]["configs"].items():
                history.append({
                    "Lượt": item["label"], "Chiến lược": LABELS.get(config, config),
                    "Model": item["summary"]["model"], "Trung bình": round(macro(scores), 3),
                    "p50 (s)": scores["p50_latency_seconds"],
                })
        st.dataframe(history, hide_index=True, width="stretch")

    report = load_evaluation_report()
    if report_has_results(report):
        with st.expander("Báo cáo phân tích và khuyến nghị"):
            st.markdown(report)
