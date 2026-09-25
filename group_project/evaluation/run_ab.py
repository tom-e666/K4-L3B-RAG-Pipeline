"""Reproducible A/B and no-HyDE evaluation on the local Chroma corpus.

Run from the repository root: .venv/Scripts/python.exe -m group_project.evaluation.run_ab
Writes per-case evidence to run_details.json and a summary to run_summary.json.
"""

from __future__ import annotations

import json
import os
import re
import statistics
import time
import unicodedata
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from google import genai
from google.genai import types
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from src.task4_chunking_indexing import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL


ROOT = Path(__file__).resolve().parent
TOP_K = 5
CANDIDATES = 12
load_dotenv(ROOT.parent.parent / ".env")
MODEL = os.getenv("EVAL_LLM_MODEL", "gemini-3.5-flash-lite")
REFUSAL = "Tôi không thể xác minh thông tin này từ các tài liệu được cung cấp."


def norm(value: str) -> str:
    value = unicodedata.normalize("NFC", value).lower()
    return " ".join(re.sub(r"\s+", " ", value).split())


def json_object(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError(f"LLM did not return JSON: {text[:160]}")
    return json.loads(match.group())


class Runner:
    def __init__(self) -> None:
        self.client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        self.embedder = SentenceTransformer(EMBEDDING_MODEL)
        self.collection = chromadb.PersistentClient(path=str(CHROMA_DIR)).get_collection(COLLECTION_NAME)
        data = self.collection.get(include=["documents", "metadatas"])
        self.corpus = [
            {"id": i, "content": d, "metadata": m}
            for i, d, m in zip(data["ids"], data["documents"], data["metadatas"])
        ]
        self.bm25 = BM25Okapi([self.tokens(item["content"]) for item in self.corpus])
        self.failures = {"hyde": 0, "rerank": 0, "generation": 0, "judge": 0}
        self.attempts = {"hyde": 0, "rerank": 0, "generation": 0, "judge": 0}

    @staticmethod
    def tokens(text: str) -> list[str]:
        return re.findall(r"[\w/-]+", norm(text))

    def llm(self, prompt: str, stage: str, max_tokens: int = 1024) -> str:
        self.attempts[stage] += 1
        try:
            result = self.client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0, max_output_tokens=max_tokens),
            )
            if not result.text:
                raise ValueError("empty LLM response")
            return result.text.strip()
        except Exception:
            self.failures[stage] += 1
            raise

    def dense(self, query: str) -> list[dict]:
        vector = self.embedder.encode([query])[0].tolist()
        data = self.collection.query(
            query_embeddings=[vector], n_results=CANDIDATES,
            include=["documents", "metadatas", "distances"],
        )
        return [
            {"id": i, "content": d, "metadata": m, "score": max(0, 1 - dist)}
            for i, d, m, dist in zip(
                data["ids"][0], data["documents"][0], data["metadatas"][0], data["distances"][0]
            )
        ]

    def lexical(self, query: str) -> list[dict]:
        scores = self.bm25.get_scores(self.tokens(query))
        order = sorted(range(len(scores)), key=lambda i: (-scores[i], i))[:CANDIDATES]
        high = max((scores[i] for i in order), default=0)
        return [
            {**self.corpus[i], "score": float(scores[i] / high) if high > 0 else 0.0}
            for i in order if scores[i] > 0
        ]

    @staticmethod
    def wrrf(dense: list[dict], lexical: list[dict]) -> list[dict]:
        fused: dict[str, dict] = {}
        for weight, results in ((0.55, dense), (0.45, lexical)):
            for rank, item in enumerate(results, 1):
                entry = fused.setdefault(item["id"], {**item, "score": 0.0})
                # Scores are normalized per retrieval channel; rank remains primary.
                normalized = item["score"] if results is lexical else min(1.0, max(0.0, item["score"]))
                entry["score"] += weight * (0.5 + 0.5 * normalized) / (60 + rank)
        return sorted(fused.values(), key=lambda x: x["score"], reverse=True)

    def hyde(self, question: str) -> str:
        try:
            return self.llm(
                "Viết một đoạn tài liệu giả định 2-3 câu có thể trả lời câu hỏi sau. "
                "Không nêu rằng đây là câu trả lời chắc chắn. Chỉ trả đoạn văn.\n" + question,
                "hyde", 180,
            )
        except Exception:
            return question

    def rerank(self, question: str, candidates: list[dict]) -> list[dict]:
        items = "\n".join(
            f"{i}. [{x['metadata']['source']}] {x['content'][:370]}"
            for i, x in enumerate(candidates)
        )
        failures_before = self.failures["rerank"]
        try:
            answer = self.llm(
                "Xếp các đoạn theo mức hỗ trợ câu hỏi, ưu tiên bằng chứng trực tiếp và các nguồn khác nhau. "
                "Chỉ xuất JSON dạng {\"order\":[0,1,...]} với mọi chỉ số xuất hiện đúng một lần.\n"
                f"Câu hỏi: {question}\nĐoạn:\n{items}", "rerank", 230,
            )
            order = json_object(answer)["order"]
            if sorted(order) != list(range(len(candidates))):
                raise ValueError("invalid rerank permutation")
            return [candidates[i] for i in order]
        except Exception:
            if self.failures["rerank"] == failures_before:
                self.failures["rerank"] += 1
            return candidates

    def mmr(self, ranked: list[dict]) -> list[dict]:
        if len(ranked) <= TOP_K:
            return ranked
        vectors = self.embedder.encode([x["content"] for x in ranked], normalize_embeddings=True)
        selected: list[int] = []
        remaining = set(range(len(ranked)))
        while remaining and len(selected) < TOP_K:
            def score(i: int) -> float:
                relevance = 1 - i / max(1, len(ranked) - 1)
                similarity = max((float(vectors[i] @ vectors[j]) for j in selected), default=0)
                same_source = any(
                    ranked[i]["metadata"]["source"] == ranked[j]["metadata"]["source"]
                    for j in selected
                )
                return 0.72 * relevance - 0.28 * similarity - (0.08 if same_source else 0)
            chosen = max(remaining, key=lambda i: (score(i), -i))
            selected.append(chosen)
            remaining.remove(chosen)
        return [ranked[i] for i in selected]

    def generate(self, question: str, chunks: list[dict], validate: bool) -> tuple[str, bool]:
        context = "\n\n".join(
            f"[{i}] Nguồn: {x['metadata']['source']}\n{x['content']}"
            for i, x in enumerate(chunks, 1)
        )
        try:
            answer = self.llm(
                "Chỉ trả lời từ các đoạn dưới đây, ngắn gọn tối đa 120 từ. Mỗi ý thực tế phải có citation [số]. "
                "Nếu thiếu bằng chứng cho câu hỏi thì trả lời đúng câu: " + REFUSAL +
                f"\n\nĐoạn:\n{context}\n\nCâu hỏi: {question}", "generation", 700,
            )
        except Exception:
            return REFUSAL, False
        if not validate:
            return answer, True
        refs = [int(v) for v in re.findall(r"\[(\d+)\]", answer)]
        refusal = "không thể xác minh" in norm(answer)
        valid = (refusal and not refs) or (bool(refs) and all(1 <= n <= len(chunks) for n in refs))
        return (answer if valid else REFUSAL), valid

    def judge(self, case: dict, answer: str, chunks: list[dict]) -> tuple[float, float]:
        context = "\n".join(x["content"][:600] for x in chunks)
        try:
            result = json_object(self.llm(
                "Chấm độc lập câu trả lời RAG bằng JSON chỉ gồm faithfulness và answer_relevance, mỗi giá trị 0, 0.5 hoặc 1. "
                "faithfulness=1 khi mọi khẳng định thực tế được context hỗ trợ; 0 nếu có khẳng định sai/không có nguồn; "
                "0.5 nếu một phần. Với câu hỏi thiếu bằng chứng, từ chối đúng được 1. "
                "answer_relevance=1 nếu trả lời đúng trọng tâm và đủ ý so với đáp án chuẩn; 0 nếu lạc đề/sai; 0.5 nếu thiếu một phần. "
                "Không thưởng câu từ chối khi context/đáp án chuẩn có câu trả lời.\n"
                f"Câu hỏi: {case['question']}\nĐáp án chuẩn: {case['expected_answer']}\n"
                f"Context truy xuất: {context}\nCâu trả lời: {answer}", "judge", 100,
            ))
            return tuple(float(result[k]) for k in ("faithfulness", "answer_relevance"))
        except Exception:
            return 0.0, 0.0


def retrieval_metrics(case: dict, chunks: list[dict], answer: str) -> tuple[float, float]:
    evidence = case["expected_context"]
    if not evidence:
        refused = "không thể xác minh" in norm(answer)
        return (1.0 if refused else 0.0), (1.0 if refused else 0.0)
    found = [any(norm(phrase) in norm(x["content"]) for x in chunks) for phrase in evidence]
    recall = sum(found) / len(found)
    source_set = set(case["expected_sources"])
    relevance = [
        x["metadata"]["source"] in source_set
        and any(norm(phrase) in norm(x["content"]) for phrase in evidence)
        for x in chunks
    ]
    hits = 0
    ap = 0.0
    for rank, relevant in enumerate(relevance, 1):
        if relevant:
            hits += 1
            ap += hits / rank
    precision = ap / hits if hits else 0.0
    return recall, precision


def main() -> None:
    cases = json.loads((ROOT / "golden_dataset.json").read_text(encoding="utf-8"))
    runner = Runner()
    details: list[dict] = []
    output = ROOT / "run_details.json"
    for case in cases:
        for config in ("A", "B", "B_no_HyDE"):
            start = time.perf_counter()
            if config == "A":
                chunks = runner.dense(case["question"])[:TOP_K]
            else:
                query = runner.hyde(case["question"]) if config == "B" else case["question"]
                fused = runner.wrrf(runner.dense(query), runner.lexical(case["question"]))
                reranked = runner.rerank(case["question"], fused[:CANDIDATES])
                chunks = runner.mmr(reranked)
            answer, citations_valid = runner.generate(case["question"], chunks, config != "A")
            faithfulness, relevance = runner.judge(case, answer, chunks)
            recall, precision = retrieval_metrics(case, chunks, answer)
            details.append({
                "id": case["id"], "case_type": case["case_type"], "question": case["question"],
                "config": config, "answer": answer, "sources": [x["id"] for x in chunks],
                "faithfulness": faithfulness, "answer_relevance": relevance,
                "context_recall": recall, "context_precision": precision,
                "citations_valid": citations_valid,
                "latency_seconds": round(time.perf_counter() - start, 3),
            })
            output.write_text(json.dumps(details, ensure_ascii=False, indent=2), encoding="utf-8")
            print(case["id"], config, "done", flush=True)
    summary = {"corpus_chunks": len(runner.corpus), "top_k": TOP_K, "model": MODEL,
               "embedding_model": EMBEDDING_MODEL, "attempts": runner.attempts,
               "failures": runner.failures, "pageindex_fallbacks": 0,
               "pageindex_fallback_available": False, "configs": {}}
    for config in ("A", "B", "B_no_HyDE"):
        rows = [x for x in details if x["config"] == config]
        summary["configs"][config] = {
            metric: round(statistics.mean(x[metric] for x in rows), 4)
            for metric in ("faithfulness", "answer_relevance", "context_recall", "context_precision")
        }
        summary["configs"][config]["p50_latency_seconds"] = round(
            statistics.median(x["latency_seconds"] for x in rows), 3
        )
    (ROOT / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
