"""Shared UI configuration and evaluation report loading."""

from __future__ import annotations

import re
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
REPORT_PATHS = [
    ROOT / "group_project" / "evaluation" / "RESULT.md",
    ROOT / "reports" / "RESULT.md",
]


@st.cache_data
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
