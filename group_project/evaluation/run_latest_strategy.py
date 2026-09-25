"""Evaluate the latest remote pipeline and a no-HyDE ablation on the frozen set."""

from __future__ import annotations

import json
import logging
import os
import statistics
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT.parent.parent / ".env")

from src import task5_semantic_search as semantic_module  # noqa: E402
from src import task7_reranking as rerank_module  # noqa: E402
from src import task9_retrieval_pipeline as retrieval_module  # noqa: E402
from src import task10_generation as generation_module  # noqa: E402
from src.task4_chunking_indexing import EMBEDDING_MODEL, get_collection  # noqa: E402
from group_project.evaluation.run_ab import retrieval_metrics  # noqa: E402
from group_project.evaluation.run_remote_strategy import is_refusal  # noqa: E402


TOP_K = 5
CONFIGS = ("A_dense", "B_full", "B_no_HyDE")
MODEL = os.getenv("LLM_MODEL", "deepseek-flash")


class WarningCounter(logging.Handler):
    def __init__(self, phrase: str) -> None:
        super().__init__(logging.WARNING)
        self.phrase = phrase
        self.count = 0

    def emit(self, record: logging.LogRecord) -> None:
        if self.phrase in record.getMessage():
            self.count += 1


def baseline_answer(question: str, chunks: list[dict]) -> str:
    """Use Task 10's exact prompt and citation gate with dense-only chunks."""
    if not chunks:
        return generation_module.SAFE_REFUSAL_ANSWER
    reordered = generation_module.reorder_for_llm(chunks)
    context = generation_module.format_context(reordered)
    try:
        answer = generation_module.call_llm(
            generation_module.SYSTEM_PROMPT,
            f"Context:\n{context}\n\nQuestion: {question}",
        )
        if generation_module.verify_citations(answer, len(reordered)):
            return answer
    except Exception:
        pass
    return generation_module.SAFE_REFUSAL_ANSWER


def judge_case(client: OpenAI, case: dict, rows: list[dict], context_by_config: dict[str, str]) -> dict:
    payload = {
        row["config"]: {"answer": row["answer"], "context": context_by_config[row["config"]]}
        for row in rows
    }
    prompt = (
        "Score each configuration independently. Return only JSON with keys A_dense, B_full, B_no_HyDE. "
        "Each value must have numeric faithfulness and answer_relevance, each 0, 0.5, or 1. "
        "Faithfulness=1 when all factual claims are supported by that configuration's context. "
        "Answer relevance=1 when the answer fully addresses the question and reference facts. "
        "A correct refusal on an out-of-scope case earns 1; refusal with available evidence earns 0. "
        f"Question: {case['question']}\nReference answer: {case['expected_answer']}\n"
        f"Case type: {case['case_type']}\nConfigurations: {json.dumps(payload, ensure_ascii=False)}"
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0,
        max_tokens=320,
        extra_body={"thinking": {"type": "disabled"}},
    )
    scores = json.loads(response.choices[0].message.content or "{}")
    for config in CONFIGS:
        for metric in ("faithfulness", "answer_relevance"):
            value = float(scores[config][metric])
            if value not in (0.0, 0.5, 1.0):
                raise ValueError("judge score outside rubric")
            scores[config][metric] = value
    return scores


def main() -> None:
    cases = json.loads((ROOT / "golden_dataset.json").read_text(encoding="utf-8"))
    key = os.getenv("DeepSeek_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
    if not key or os.getenv("LLM_PROVIDER") != "deepseek":
        raise RuntimeError("Configure LLM_PROVIDER=deepseek and DeepSeek_API_KEY")
    collection = get_collection()
    if collection.count() != 304 or EMBEDDING_MODEL != "BAAI/bge-m3":
        raise RuntimeError("Expected the frozen 304-chunk BGE-M3 corpus")

    hyde_failures = WarningCounter("HyDE generation failed")
    rerank_failures = WarningCounter("LLM listwise rerank error")
    mmr_failures = WarningCounter("MMR context packing failed")
    semantic_module.logger.addHandler(hyde_failures)
    rerank_module.logger.addHandler(rerank_failures)
    generation_module.logger.addHandler(mmr_failures)
    pageindex_attempts = 0
    original_pageindex = retrieval_module.pageindex_search

    def pageindex_probe(query: str, top_k: int = TOP_K) -> list[dict]:
        nonlocal pageindex_attempts
        pageindex_attempts += 1
        return original_pageindex(query, top_k=top_k)

    retrieval_module.pageindex_search = pageindex_probe
    evaluator = OpenAI(api_key=key, base_url="https://api.deepseek.com")
    details: list[dict] = []
    errors = {"generation": 0, "judge": 0}
    details_path = ROOT / "latest_details.json"

    for case in cases:
        case_rows = []
        contexts = {}
        for config in CONFIGS:
            semantic_module.USE_HYDE = config == "B_full"
            generation_module.USE_MMR = config != "A_dense"
            retrieval_module.DENSE_WEIGHT = 0.55
            retrieval_module.BM25_WEIGHT = 0.45
            retrieval_module.USE_LLM_RERANK = config != "A_dense"
            started = time.perf_counter()
            try:
                if config == "A_dense":
                    chunks = semantic_module.semantic_search(case["question"], top_k=TOP_K)
                    answer = baseline_answer(case["question"], chunks)
                else:
                    result = generation_module.generate_with_citation(case["question"], top_k=TOP_K)
                    chunks = result["sources"]
                    answer = result["answer"]
            except Exception:
                errors["generation"] += 1
                chunks = []
                answer = generation_module.SAFE_REFUSAL_ANSWER
            latency = time.perf_counter() - started

            if case["case_type"] == "refusal":
                recall = precision = 1.0 if is_refusal(answer) else 0.0
            else:
                recall, precision = retrieval_metrics(case, chunks, answer)
            citations_valid = generation_module.verify_citations(answer, len(chunks))
            row = {
                "id": case["id"], "case_type": case["case_type"], "question": case["question"],
                "config": config, "answer": answer, "sources": [item["id"] for item in chunks],
                "context_recall": recall, "context_precision": precision,
                "citations_valid": citations_valid, "latency_seconds": round(latency, 3),
            }
            contexts[config] = "\n".join(item["content"][:600] for item in chunks)
            case_rows.append(row)
            print(case["id"], config, "generated", flush=True)

        try:
            scores = judge_case(evaluator, case, case_rows, contexts)
            for row in case_rows:
                row.update(scores[row["config"]])
        except Exception:
            errors["judge"] += 1
            for row in case_rows:
                row.update(faithfulness=0.0, answer_relevance=0.0)
        details.extend(case_rows)
        details_path.write_text(json.dumps(details, ensure_ascii=False, indent=2), encoding="utf-8")
        print(case["id"], "judged", flush=True)

    summary: dict = {
        "model": MODEL, "embedding_model": EMBEDDING_MODEL, "corpus_chunks": collection.count(),
        "dataset_size": len(cases), "top_k": TOP_K, "hyde_attempts": len(cases),
        "hyde_failures": hyde_failures.count, "rerank_attempts": len(cases) * 2,
        "rerank_failures": rerank_failures.count, "mmr_attempts": len(cases) * 2,
        "mmr_failures": mmr_failures.count, "pageindex_fallback_attempts": pageindex_attempts,
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
    (ROOT / "latest_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
