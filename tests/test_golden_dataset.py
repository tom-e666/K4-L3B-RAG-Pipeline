"""The evaluation set must remain grounded in the checked-in corpus."""

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_golden_distribution_and_evidence():
    cases = json.loads((ROOT / "group_project/evaluation/golden_dataset.json").read_text(encoding="utf-8"))
    sources = {
        path.name: path.read_text(encoding="utf-8")
        for path in (ROOT / "data/standardized").rglob("*.md")
    }
    counts = Counter(case["case_type"] for case in cases)
    assert len(cases) >= 15
    assert counts["semantic"] >= 8
    assert counts["keyword"] >= 4
    assert counts["multi_source"] >= 2
    assert counts["refusal"] >= 2
    assert len({case["id"] for case in cases}) == len(cases)

    for case in cases:
        assert case["question"].strip() and case["expected_answer"].strip()
        if case["case_type"] == "refusal":
            assert case["expected_context"] == []
            assert case["expected_sources"] == []
            continue
        assert len(case["expected_sources"]) >= (2 if case["case_type"] == "multi_source" else 1)
        assert case["expected_context"]
        assert all(source in sources for source in case["expected_sources"])
        for snippet in case["expected_context"]:
            assert any(snippet in sources[source] for source in case["expected_sources"]), case["id"]
