"""Shared UI configuration and evaluation report loading."""

from __future__ import annotations

import re
import json
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
REPORT_PATHS = [
    ROOT / "group_project" / "evaluation" / "RESULT.md",
    ROOT / "reports" / "RESULT.md",
]
EVALUATION_DIR = ROOT / "group_project" / "evaluation"


@st.cache_data(ttl=30)
def load_evaluation_report() -> str | None:
    """Read the first available report without inventing evaluation metrics."""
    for path in REPORT_PATHS:
        if path.exists():
            return path.read_text(encoding="utf-8")
    return None


def report_has_results(report: str | None) -> bool:
    if not report:
        return False
    return "TODO" not in report and not re.search(
        r"\b(chưa có dữ liệu|pending)\b", report, re.IGNORECASE
    )


@st.cache_data(ttl=30)
def load_evaluation_runs() -> list[dict]:
    """Load every recorded run while preserving each run's model and metric scope."""
    definitions = (
        ("latest", "Strategy mới · DeepSeek", "latest_summary.json", "latest_details.json"),
        ("listwise", "Listwise · DeepSeek", "remote_summary.json", "remote_details.json"),
        ("historical", "Bản đầu · Gemini", "run_summary.json", "run_details.json"),
    )
    runs = []
    for run_id, label, summary_name, details_name in definitions:
        summary_path = EVALUATION_DIR / summary_name
        details_path = EVALUATION_DIR / details_name
        if summary_path.exists() and details_path.exists():
            runs.append({
                "id": run_id,
                "label": label,
                "summary": json.loads(summary_path.read_text(encoding="utf-8")),
                "details": json.loads(details_path.read_text(encoding="utf-8")),
            })
    return runs


def load_evaluation_data() -> tuple[dict | None, list[dict]]:
    """Compatibility helper for code that expects the newest run only."""
    runs = load_evaluation_runs()
    return (runs[0]["summary"], runs[0]["details"]) if runs else (None, [])
