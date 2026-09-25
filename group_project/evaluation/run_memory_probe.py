"""Small reproducible probe for follow-up query rewriting (source hit at top 5)."""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.task10_generation import rewrite_followup_query  # noqa: E402
from src.task9_retrieval_pipeline import retrieve  # noqa: E402

CASES = [
    {
        "id": "memory-mentor-xp",
        "history": [{"role": "user", "content": "Mentor Duty là gì?"}, {"role": "assistant", "content": "Mentor Duty là buổi làm việc định kỳ với mentor."}],
        "question": "Nếu nộp sau 12h thì còn được XP không?",
        "expected_source": "quy-dinh-mentor-duty.md",
    },
    {
        "id": "memory-demo-video",
        "history": [{"role": "user", "content": "Demo Day yêu cầu những deliverables nào?"}, {"role": "assistant", "content": "Quy định liệt kê 10 deliverables."}],
        "question": "Mục thứ 6 dài bao lâu?",
        "expected_source": "quy-dinh-deliverables-demo-day.md",
    },
    {
        "id": "memory-canvas",
        "history": [{"role": "user", "content": "CP1 Canvas trong Hackathon là gì?"}, {"role": "assistant", "content": "Đây là bản phác thảo ý tưởng tại CP1."}],
        "question": "Cần bao nhiêu người sẵn sàng thử nghiệm?",
        "expected_source": "quy-che-ai-product-hackathon.md",
    },
]


def search(query):
    start = time.perf_counter()
    chunks = retrieve(query, top_k=5)
    return {
        "sources": [chunk["metadata"]["source"] for chunk in chunks],
        "latency_s": round(time.perf_counter() - start, 3),
    }


def main():
    results = []
    for case in CASES:
        start = time.perf_counter()
        rewritten, changed = rewrite_followup_query(case["question"], case["history"])
        rewrite_latency = round(time.perf_counter() - start, 3)
        original = search(case["question"])
        memory = search(rewritten)
        results.append({
            **case,
            "rewritten_query": rewritten,
            "changed": changed,
            "rewrite_latency_s": rewrite_latency,
            "original": {**original, "source_hit": case["expected_source"] in original["sources"]},
            "memory": {**memory, "source_hit": case["expected_source"] in memory["sources"]},
        })
    output = Path(__file__).with_name("memory_probe_results.json")
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
