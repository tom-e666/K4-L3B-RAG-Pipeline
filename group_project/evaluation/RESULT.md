# RAG evaluation results

## Run information

| Field | Value |
| --- | --- |
| Evaluation date | 2026-09-25 |
| Golden dataset | 16 cases: 8 semantic, 4 keyword, 2 multi-source, 2 refusal |
| Corpus | 10 standardized Markdown files, 304 indexed chunks; SHA-256 `8ea15a93a655596230ce7bad5a68eb6819c429b5d7ba5ed63e8a63e7712c225d` |
| Embedding | `BAAI/bge-m3`, local SentenceTransformer |
| Generator, HyDE, reranker, evaluator | `gemini-3.5-flash-lite`, temperature 0 |
| Retrieval depth | 12 candidates per channel, final `top_k=5` |
| PageIndex | Not configured; `pageindex_search` is unimplemented in the application |
| Reproduce | `.venv/Scripts/python.exe -m group_project.evaluation.run_ab` from repo root |
| Evidence | [golden_dataset.json](golden_dataset.json), [run_details.json](run_details.json), [run_summary.json](run_summary.json) |

## Configurations and scoring

- **A:** original question → Chroma dense-only → top 5 in score order → grounded generation.
- **B:** HyDE hypothetical passage → dense search; original question → BM25 with per-query score normalization; weighted RRF (dense 0.55, BM25 0.45, `k=60`) → LLM rerank → MMR (`λ=0.72`, source repetition penalty) → grounded generation and citation reference validation.
- **B without HyDE:** identical to B, but dense search uses the original question. All configurations use the same 16 questions, indexed corpus, generator, evaluation rubric and final `top_k`.

Faithfulness and answer relevance are 0/0.5/1 judgments from the same Gemini model against the retrieved context and golden answer. Context recall is the fraction of golden evidence snippets found in retrieved chunks. Context precision is average precision of retrieved chunks containing a golden snippet from an expected source. For refusal cases, context metrics are 1 when the answer correctly refuses and 0 otherwise. These are **project rubric scores, not RAGAS outputs**. The evaluator failed twice and those two judge scores were conservatively recorded as 0. Because the generator also serves as judge, a human review is needed before using small deltas as proof of quality.

The latency timer currently spans retrieval, generation **and the evaluator call**. These p50 values compare the evaluation runs, not production response latency. Model loading is outside the timer.

## Overall scores

| Metric | A | B | Δ B−A | B without HyDE |
| --- | ---: | ---: | ---: | ---: |
| Faithfulness | 0.969 | 0.844 | −0.125 | 0.875 |
| Answer relevance | 0.844 | 0.750 | −0.094 | 0.813 |
| Context recall | 0.885 | 0.823 | −0.063 | 0.875 |
| Context precision | 0.719 | 0.682 | −0.037 | 0.710 |
| **Macro average** | **0.854** | **0.775** | **−0.079** | **0.818** |
| p50 evaluation latency | 2.897 s | 17.160 s | +14.263 s | 14.678 s |

## A/B comparison

A led B on all four aggregate metrics in this run. B without HyDE recovered 0.043 macro-average points relative to B, so the current HyDE prompt appears harmful on this corpus; this ablation does not isolate MMR. All keyword cases achieved context recall 1.0 in all three configurations. On the two multi-source cases, answer relevance was 0.25 for A, 1.0 for B and 0.5 for B without HyDE, but context recall stayed at 0.5 for both A and B. The small two-case slice is insufficient to establish a reliable advantage.

| Operational measure | Result |
| --- | ---: |
| HyDE failures | 0/16 (0%) |
| LLM rerank failures, including invalid response format/permutation | 22/32 (68.75%); fused order used as fallback |
| Generation failures | 0/48 (0%) |
| Evaluator failures | 2/48 (4.17%); scores recorded as 0 |
| PageIndex fallback rate | 0/48 (0% observed); unavailable and never attempted |
| Invalid B citation references | 1/16; answer replaced with safe refusal |

The high rerank fallback rate means this run tests a mixture of LLM reranking and fused-order fallback. Its score is a record of the current implementation, not a clean estimate of a working reranker. PageIndex's 0% is an availability observation, not evidence that no query needed fallback.

## Worst performers

| Case | Config | Faithfulness | Relevance | Recall | Precision | Failure stage | Root cause |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `sem-01` — Mentor Duty schedule | B | 1.0 | 0.0 | 0.0 | 0.0 | Retrieval | Retrieved the Mentor Duty file but missed the chunk containing the Wednesday/Saturday schedule; answer did not address the asked days. |
| `sem-05` — CP1 Canvas contents | B | 0.5 | 0.5 | 0.5 | 0.25 | Chunk selection | The retrieved evidence covers only six of seven Canvas lines; the willing-users line is in another chunk. |
| `sem-07` — tuition and stipend | B | 0.0 | 0.0 | 1.0 | 1.0 | Citation validation/generation | Evidence was present but generated citations failed validation, so B returned a safe refusal. |
| `multi-01` — first cohort and stipend | B without HyDE | 0.0 | 0.0 | 0.5 | 0.0 | Citation validation/retrieval | Both source files appeared, but the required evidence chunk was incomplete and citation validation returned a refusal. |

## Recommendations

| Priority | Action | Evidence | How to verify |
| ---: | --- | --- | --- |
| 1 | Fix LLM rerank response parsing and log the raw failure class; rerun the same frozen golden set. | 22/32 rerank attempts fell back, so B is not a stable treatment. | Rerank failure rate approaches zero and per-case order is recorded. |
| 2 | Improve evidence coverage for adjacent chunks and calibrate MMR/source diversity. | `sem-05` omitted the seventh Canvas line; multi-source context recall was only 0.5 for A and B. | Context recall improves on `sem-05` and both multi-source cases without lowering precision. |
| 3 | Validate citation syntax more robustly and judge claims against cited chunks. | One B answer with available evidence became a refusal after citation validation. | No valid `[1, 2]`-style reference is rejected; unsupported claims are still refused. |
| 4 | Separate production latency from evaluator latency; add an independent evaluator and implement PageIndex before interpreting fallback rate. | Current p50 includes judging; PageIndex is unavailable; two judge calls failed. | Rerun with separate per-stage timing and a configured fallback. |

This is the recorded baseline for the current strategy. Strategy changes should use the same golden set and retain per-case outputs for direct comparison.

## Remote strategy follow-up — DeepSeek

This second run used `origin/main` at `d9c18b6` in the isolated `codex/strategy-eval` worktree. It evaluates the remote code's weighted RRF and `llm_listwise_rerank` implementation with `DeepSeek_API_KEY`, `deepseek-flash` in non-thinking mode, and the same 16-case golden set. The copied 304-chunk index uses `BAAI/bge-m3`; no re-indexing or changes to the original checkout were needed. Details: [remote_details.json](remote_details.json), [remote_summary.json](remote_summary.json), and [run_remote_strategy.py](run_remote_strategy.py).

| Metric | A dense-only | Remote weighted RRF | Remote weighted RRF + listwise | Listwise − A |
| --- | ---: | ---: | ---: | ---: |
| Faithfulness | 0.969 | 0.938 | 1.000 | +0.031 |
| Answer relevance | 0.906 | 0.906 | 1.000 | +0.094 |
| Context recall | 0.885 | 0.823 | 0.938 | +0.052 |
| Context precision | 0.719 | 0.721 | 0.880 | +0.161 |
| **Macro average** | **0.870** | **0.847** | **0.954** | **+0.085** |
| p50 retrieval + generation latency | 5.608 s | 5.256 s | 8.441 s | +2.833 s |
| Valid citation reference rate | 100% | 100% | 93.75% | −6.25 pp |

Here A and both remote treatments used the same DeepSeek generator, evaluator, prompt, corpus, and `top_k=5`. The weighted treatment disabled listwise reranking; the listwise treatment enabled it. No HyDE or MMR was used in this run, because the remote strategy does not implement them. The previous Gemini run above is retained as a historical record and **should not be compared numerically** with these DeepSeek scores.

The listwise treatment improved all four rubric metrics over A. The weighted RRF treatment alone did not: its macro average was 0.023 lower than A. On the two multi-source cases, listwise answer relevance reached 1.0 and context recall 0.75; A and weighted RRF both had context recall 0.5. All three configurations correctly refused both out-of-scope questions. LLM rerank fallback was **0/16**; generation and evaluator failures were **0/48** each. PageIndex fallback was **0/32 hybrid retrievals** and remains unavailable in the application. The valid-citation check accepts `[Document 1]` and source-labelled document references; one listwise answer (`sem-03`) used an unbracketed “Document 1” reference and failed the syntax check. The answer itself was judged grounded.

### Remaining weak cases

| Case | Config | Faithfulness | Relevance | Recall | Precision | Cause |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `multi-01` — cohort size and stipend | A | 1.0 | 0.5 | 0.0 | 0.0 | Retrieved source files, but missed the exact evidence chunks for both requested facts. |
| `sem-05` — seven CP1 Canvas lines | A | 0.5 | 0.5 | 0.5 | 0.33 | Chunk boundary separates the willing-users line from other Canvas lines. |
| `multi-02` — willing users and deliverables | Weighted RRF | 1.0 | 0.5 | 0.5 | 0.2 | CP1 willing-users evidence was outside the selected chunks; the answer was partial. Listwise retrieved both facts. |
| `sem-03` — Mentor Duty XP deadline | Listwise | 1.0 | 1.0 | 1.0 | 1.0 | Content was correct, but the citation format was not machine-valid. |

**Next steps:** keep listwise reranking as the candidate strategy, add citation validation to the generation path, and test retrieval with larger or adjacent chunks for multi-part questions. The scores are based on exact golden evidence snippets and a DeepSeek rubric judge; another judge or manual audit should confirm the observed gains before rollout.

## Latest remote strategy — HyDE, MMR and citation gate

Remote `origin/main` advanced to `a7e9f69`; this third run evaluates that source in worktree `codex/strategy-eval-v2`. The same 16 golden cases and 304 BGE-M3 chunks were used. The generator, citation gate, prompt, evaluator and `top_k=5` were held constant across the three treatments. All LLM calls used `deepseek-flash` via `DeepSeek_API_KEY` in non-thinking mode. [latest_details.json](latest_details.json) records every answer and selected chunk; [latest_summary.json](latest_summary.json) has aggregate scores.

- **A dense-only:** original query → dense top 5 → Task 10 grounded generation and citation gate.
- **B full:** HyDE → dense + BM25 → weighted RRF (0.55/0.45) → DeepSeek listwise rerank → MMR context packing → the same grounded generation and citation gate.
- **B without HyDE:** identical to B, except dense search uses the original query.

| Metric | A | B full | B without HyDE | Δ B−A |
| --- | ---: | ---: | ---: | ---: |
| Faithfulness | 1.000 | 1.000 | 1.000 | 0.000 |
| Answer relevance | 0.906 | 0.906 | 0.844 | 0.000 |
| Context recall | 0.885 | 0.823 | 0.854 | −0.063 |
| Context precision | 0.719 | 0.844 | 0.844 | +0.125 |
| **Macro average** | **0.878** | **0.893** | **0.885** | **+0.016** |
| p50 retrieval + generation latency | 2.130 s | 11.027 s | 9.288 s | +8.897 s |
| Citation gate pass rate | 100% | 100% | 100% | 0 pp |

HyDE adds 0.008 macro-average points relative to B without HyDE and 1.739 seconds to p50, but reduces context recall by 0.031. The full B configuration improves context precision over A while taking roughly five times as long. This is a small golden set; the gain is not yet strong evidence to replace A everywhere. Rerank failures were **0/32**, HyDE failures **0/16**, MMR failures **0/32**, generation and judge failures **0/48**, and PageIndex fallback **0/32 hybrid retrievals**. PageIndex remains unimplemented, so the observed fallback rate is not a reliability claim.

### Latest worst performers

| Case | Config | Faithfulness | Relevance | Recall | Precision | Finding |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `multi-01` — cohort size and stipend | B full | 1.0 | 0.5 | 0.0 | 0.0 | Selected chunks cover cohort size but not the exact stipend evidence from the expected article; answer was partial. |
| `sem-05` — seven Canvas lines | B without HyDE | 1.0 | 0.0 | 0.5 | 1.0 | The missing seventh line caused the citation-gated generator to refuse. |
| `sem-07` — tuition and stipend | B full | 1.0 | 1.0 | 0.0 | 0.0 | Answer was grounded in alternate sources, but the exact expected portal snippet was not retrieved; this exposes a limitation of exact-snippet context metrics. |
| `sem-02` — Mentor Duty fields | B full | 1.0 | 0.5 | 0.67 | 1.0 | Some required fields span adjacent chunks; answer missed part of the five-field list. |

**Recommendations:** retain listwise reranking as the most promising remote component, test adjacent-chunk expansion for multi-part questions, and add fact-level/alternative-source labels to the golden set before treating exact-snippet recall as a final quality measure. Keep A available for latency-sensitive queries. The rubric judge is the same model family as the generator; manually audit the 16 answers before a production switch.

## Conversation Memory probe — contextual query rewriting

The Streamlit chat now sends up to two preceding user/assistant exchanges to DeepSeek, which rewrites a follow-up as a standalone question before retrieval. The original question remains visible; prior assistant answers are used only to resolve references, never as grounding evidence. If rewriting fails, retrieval uses the original question. [run_memory_probe.py](run_memory_probe.py) and [memory_probe_results.json](memory_probe_results.json) record a three-case probe against the same 304-chunk corpus, using `deepseek-flash` and the current retrieval pipeline (`top_k=5`).

| Follow-up | Original top-5 expected-source hit | With memory | Rewrite |
| --- | ---: | ---: | --- |
| Mentor Duty: “Nếu nộp sau 12h thì còn được XP không?” | Yes | Yes | Model kept the question unchanged. |
| Demo Day: “Mục thứ 6 dài bao lâu?” | No | Yes | Resolved “mục thứ 6” to Demo Day's deliverables. |
| CP1 Canvas: “Cần bao nhiêu người sẵn sàng thử nghiệm?” | Yes | Yes | Added CP1 Canvas/Hackathon context. |
| **Expected-source hit rate** | **2/3** | **3/3** | **2/3 questions changed** |

Median rewrite time was **1.028 s** (three DeepSeek calls, zero failures). This is a small retrieval-only demonstration, not an answer-quality score or a replacement for the 16-case A/B and ablation tables above. Retrieval timing is affected by cache warm-up and is not compared as a latency claim. A larger multi-turn golden set with evidence-level labels is needed to estimate memory's effect on faithfulness and answer relevance.

An additional live end-to-end check of the Demo Day follow-up returned “Video Demo, 3–5 phút [Document 1]” with five retrieved chunks and a valid citation. It was a functional smoke check, outside the three-case retrieval metric.
