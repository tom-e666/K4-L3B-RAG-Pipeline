"""Evaluate remote weighted RRF and listwise rerank against dense-only on one frozen set.

Run from this worktree root with the original project's virtualenv Python. Results
are written separately from the earlier Gemini experiment.
"""

from __future__ import annotations

import json
import logging
import os
import re
import statistics
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT.parent.parent / ".env")

from src import task5_semantic_search as semantic_module  # noqa: E402
from src import task7_reranking as reranking_module  # noqa: E402
from src import task9_retrieval_pipeline as retrieval_module  # noqa: E402
from src.task10_generation import SYSTEM_PROMPT, call_llm, format_context, reorder_for_llm  # noqa: E402
from src.task4_chunking_indexing import EMBEDDING_MODEL, get_collection  # noqa: E402
from group_project.evaluation.run_ab import norm, retrieval_metrics  # noqa: E402


TOP_K = 5
CONFIGS = ("A_dense", "remote_weighted", "remote_listwise")
MODEL = os.getenv("LLM_MODEL", "deepseek-flash")
REFUSAL = "Tôi không thể xác minh thông tin này từ nguồn hiện có."


def is_refusal(answer: str) -> bool:
    text = norm(answer)
    return any(phrase in text for phrase in (
        "không thể xác minh", "không đủ thông tin", "không có thông tin",
    ))


class RerankFailureCounter(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.count = 0

    def emit(self, record: logging.LogRecord) -> None:
        if "LLM listwise rerank error" in record.getMessage():
            self.count += 1


def main() -> None:
    cases = json.loads((ROOT / "golden_dataset.json").read_text(encoding="utf-8"))
    key = os.getenv("DeepSeek_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("DeepSeek_API_KEY is required")
    if os.getenv("LLM_PROVIDER") != "deepseek":
        raise RuntimeError("Set LLM_PROVIDER=deepseek in this worktree's .env")
    if os.getenv("EMBEDDING_MODEL") != EMBEDDING_MODEL:
        raise RuntimeError("Embedding model does not match the indexed corpus")

    collection = get_collection()
    if collection.count() == 0:
        raise RuntimeError("The strategy worktree has no indexed chunks")
    embedder = SentenceTransformer(EMBEDDING_MODEL)
    semantic_module.embed_texts = lambda texts: embedder.encode(texts).tolist()

    rerank_failures = RerankFailureCounter()
    reranking_module.logger.addHandler(rerank_failures)
    pageindex_attempts = 0
    original_pageindex = retrieval_module.pageindex_search

    def pageindex_probe(query: str, top_k: int = TOP_K) -> list[dict]:
        nonlocal pageindex_attempts
        pageindex_attempts += 1
        return original_pageindex(query, top_k=top_k)

    retrieval_module.pageindex_search = pageindex_probe
    evaluator = OpenAI(api_key=key, base_url="https://api.deepseek.com")
    errors = {"generation": 0, "judge": 0}
    details: list[dict] = []
    details_path = ROOT / "remote_details.json"

    for case in cases:
        for config in CONFIGS:
            started = time.perf_counter()
            if config == "A_dense":
                chunks = semantic_module.semantic_search(case["question"], top_k=TOP_K)
            else:
                retrieval_module.DENSE_WEIGHT = 0.55
                retrieval_module.BM25_WEIGHT = 0.45
                retrieval_module.USE_LLM_RERANK = config == "remote_listwise"
                chunks = retrieval_module.retrieve(case["question"], top_k=TOP_K)
            try:
                context = format_context(reorder_for_llm(chunks))
                answer = call_llm(SYSTEM_PROMPT, f"Context:\n{context}\n\nQuestion: {case['question']}")
                if not answer:
                    raise ValueError("empty answer")
            except Exception:
                errors["generation"] += 1
                answer = REFUSAL
            latency = time.perf_counter() - started  # production path, excludes judge

            references = [int(value) for value in re.findall(r"\[(?:Document\s+)?(\d+)(?:\s*\|[^\]]*)?\]", answer, re.I)]
            refused = is_refusal(answer)
            citations_valid = (refused and not references) or (
                bool(references) and all(1 <= value <= len(chunks) for value in references)
            )
            if case["case_type"] == "refusal":
                context_recall = context_precision = 1.0 if refused else 0.0
            else:
                context_recall, context_precision = retrieval_metrics(case, chunks, answer)
            try:
                judge_context = "\n".join(item["content"][:600] for item in chunks)
                judgment = evaluator.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": (
                            "Return only a JSON object with numeric faithfulness and answer_relevance, "
                            "each 0, 0.5, or 1. Faithfulness means every factual claim is supported "
                            "by the retrieved context. Answer relevance means the answer addresses "
                            "the question and includes the reference answer's key facts. "
                            "A correct refusal for a question without evidence earns 1 on both."
                        )},
                        {"role": "user", "content": (
                            f"Question: {case['question']}\nReference answer: {case['expected_answer']}\n"
                            f"Retrieved context: {judge_context}\nAnswer: {answer}\nOutput JSON."
                        )},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0,
                    max_tokens=120,
                    extra_body={"thinking": {"type": "disabled"}},
                )
                scores = json.loads(judgment.choices[0].message.content or "{}")
                faithfulness = float(scores["faithfulness"])
                answer_relevance = float(scores["answer_relevance"])
                if faithfulness not in (0.0, 0.5, 1.0) or answer_relevance not in (0.0, 0.5, 1.0):
                    raise ValueError("judge output outside rubric")
            except Exception:
                errors["judge"] += 1
                faithfulness = 0.0
                answer_relevance = 0.0

            details.append({
                "id": case["id"], "case_type": case["case_type"], "question": case["question"],
                "config": config, "answer": answer, "sources": [item["id"] for item in chunks],
                "faithfulness": faithfulness, "answer_relevance": answer_relevance,
                "context_recall": context_recall, "context_precision": context_precision,
                "citations_valid": citations_valid, "latency_seconds": round(latency, 3),
            })
            details_path.write_text(json.dumps(details, ensure_ascii=False, indent=2), encoding="utf-8")
            print(case["id"], config, "done", flush=True)

    summary: dict = {
        "model": MODEL, "embedding_model": EMBEDDING_MODEL, "corpus_chunks": collection.count(),
        "top_k": TOP_K, "dataset_size": len(cases), "rerank_attempts": len(cases),
        "rerank_failures": rerank_failures.count, "pageindex_fallback_attempts": pageindex_attempts,
        "pageindex_fallback_rate": round(pageindex_attempts / (len(cases) * 2), 4),
        "errors": errors, "configs": {},
    }
    for config in CONFIGS:
        rows = [item for item in details if item["config"] == config]
        summary["configs"][config] = {
            metric: round(statistics.mean(item[metric] for item in rows), 4)
            for metric in ("faithfulness", "answer_relevance", "context_recall", "context_precision")
        }
        summary["configs"][config]["p50_latency_seconds"] = round(
            statistics.median(item["latency_seconds"] for item in rows), 3
        )
        summary["configs"][config]["citation_valid_rate"] = round(
            statistics.mean(item["citations_valid"] for item in rows), 4
        )
    (ROOT / "remote_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
