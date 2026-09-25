# Kết quả đánh giá RAG

## Phạm vi và cách chạy

Lượt đo mới nhất ngày 2026-09-25 dùng 16 câu hỏi trong `group_project/evaluation/golden_dataset.json` (8 semantic/paraphrase, 4 keyword/tên riêng, 2 nhiều nguồn, 2 ngoài phạm vi). Corpus gồm 10 tài liệu Markdown đã chuẩn hóa, 304 chunks; embedding `BAAI/bge-m3`; `top_k=5`. DeepSeek `deepseek-flash` được dùng cho generation, HyDE, listwise rerank và rubric judge. Cả ba cấu hình trong lượt đo này dùng cùng golden set, corpus, prompt, generator, evaluator và citation gate.

| Cấu hình | Truy xuất và tạo câu trả lời |
| --- | --- |
| A · Dense-only | Query gốc → dense top 5 → grounded generation → citation validation |
| B · Full | HyDE → dense + BM25 → weighted RRF (0.55/0.45) → LLM listwise rerank → MMR context packing → grounded generation → citation validation |
| B · Không HyDE | Như B, nhưng dense search dùng query gốc; đây là ablation của HyDE |

## Kết quả mới nhất

| Metric | A | B full | B không HyDE | Δ B−A |
| --- | ---: | ---: | ---: | ---: |
| Faithfulness | 1.000 | 1.000 | 1.000 | 0.000 |
| Answer relevance | 0.906 | 0.906 | 0.844 | 0.000 |
| Context recall | 0.885 | 0.823 | 0.854 | −0.063 |
| Context precision | 0.719 | 0.844 | 0.844 | +0.125 |
| **Trung bình 4 metric** | **0.878** | **0.893** | **0.885** | **+0.016** |
| p50 retrieval + generation | 2.130 s | 11.027 s | 9.288 s | +8.897 s |

HyDE thêm 0.008 điểm trung bình so với B không HyDE và 1.739 giây vào p50. B full tăng context precision nhưng giảm context recall và chậm khoảng 5 lần A. Với 16 câu hỏi, chênh lệch này chưa đủ để thay A ở mọi truy vấn. Cả ba cấu hình đạt citation gate 100%. HyDE lỗi 0/16, listwise rerank fallback 0/32, MMR lỗi 0/32, generation và judge lỗi 0/48. PageIndex chưa được triển khai; tỷ lệ fallback quan sát 0/32 không phản ánh độ tin cậy của cơ chế đó.

Điểm là rubric của dự án, **không phải RAGAS**. Faithfulness và answer relevance do DeepSeek chấm; context recall/precision dựa trên các đoạn evidence kỳ vọng. Judge cùng họ model với generator và exact-snippet matching có thể bỏ sót nguồn thay thế, nên cần kiểm tra thủ công trước khi quyết định production. p50 của lượt này chỉ đo retrieval + generation; không so trực tiếp với lượt Gemini cũ vì model và phạm vi đo khác nhau.

## Vấn đề và hướng cải thiện

| Ưu tiên | Evidence | Hành động |
| ---: | --- | --- |
| 1 | `multi-01`: B full thiếu đúng đoạn evidence về trợ cấp, context recall 0 | Mở rộng chunks lân cận cho câu nhiều ý và kiểm tra lại cả hai multi-source case. |
| 2 | `sem-05`: dòng thứ bảy của CP1 Canvas nằm ở chunk khác | Kiểm tra ranh giới chunk, mở rộng evidence có kiểm soát và đo lại recall/precision. |
| 3 | `sem-07`: câu trả lời có nguồn khác hợp lệ nhưng exact-snippet recall 0 | Gắn nhãn fact-level và nguồn thay thế trong golden set. |
| 4 | B full tăng điểm trung bình 0.016 nhưng p50 tăng 8.897 s | Giữ A cho truy vấn nhạy độ trễ; chỉ bật pipeline đầy đủ khi lợi ích retrieval rõ ràng. |

Chi tiết từng case, hai lượt đo trước và phương pháp được lưu trong [báo cáo evaluation](../group_project/evaluation/RESULT.md). Dữ liệu gốc: [latest_summary.json](../group_project/evaluation/latest_summary.json) và [latest_details.json](../group_project/evaluation/latest_details.json). Dashboard Streamlit ở mục **Đánh giá A/B** cho phép chọn lượt đo và so sánh nhiều strategy trong cùng lượt.
