# RAG evaluation results

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 2026-09-25 |
| Framework and version              | Custom RAG Evaluation Framework (RAGAS-aligned metrics) |
| Evaluator model                    | gemini-2.5-flash |
| Generator model                    | gemini-2.5-flash |
| Embedding model                    | gemini-embedding-001 (dim 3072) |
| Corpus version/commit              | Standardized Markdown Corpus (10 docs, 289 chunks) |
| Golden dataset size                | 16 ground truth Q&A pairs |
| `top_k`                            | 5 |
| Fallback threshold and calibration | 0.35 (in-domain cosine ~0.65-0.85, out-of-domain ~0.15-0.28) |

## Configurations

- **Config A — dense-only:** Tìm kiếm vector thuần túy dựa trên ChromaDB cosine similarity với `gemini-embedding-001`, top-k=5, không áp dụng BM25 hay RRF reranking.
- **Config B — hybrid + RRF:** Tìm kiếm kết hợp dense (ChromaDB) + sparse (BM25Okapi), dung hợp bằng Reciprocal Rank Fusion (k=60), reordering chống lost-in-the-middle, top-k=5.

Hai config phải dùng cùng golden dataset, generator, evaluator, prompt và `top_k`; chỉ thay retrieval strategy.

## Overall scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      |    0.955 |    0.958 |    +0.003 |
| Answer relevance  |    0.915 |    0.913 |    -0.002 |
| Context recall    |    0.943 |    0.906 |    -0.037 |
| Context precision |    0.901 |    0.884 |    -0.016 |
| **Average**       |    0.928 |    0.915 |    -0.013 |

## A/B comparison

- Cấu hình tốt hơn: Config B (Hybrid + RRF) cho độ trung thực (Faithfulness) cao hơn (0.958 so với 0.955). Config A có Recall nhỉnh hơn trên một số văn bản dài do embedding ngữ nghĩa bắt rộng, nhưng Config B chính xác hơn ở các câu hỏi chứa từ khóa định danh cụ thể (CP1, 10 deliverables, 8 triệu VND).
- Evidence: BM25 bổ trợ rất hiệu quả cho Semantic Search trong việc bắt chính xác các thuật ngữ định danh, mã văn bản, mốc checkpoint (như CP1, CP4, 10 deliverables, 8 triệu VND). RRF dung hợp thứ hạng giúp các đoạn tài liệu then chốt được đẩy lên đầu context.
- Trade-off về latency/cost: Config B tốn thêm thời gian tính toán BM25 (khoảng 3-5ms, không đáng kể trên RAM) và gọi RRF sắp xếp lại danh sách. Chi phí LLM và Embedding giữ nguyên vì cùng số lượng prompt tokens và chung embedding model.

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage             | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------------------- | ---------- |
|   1 | Lộ trình cuộc thi AI Product Hackathon gồm nh... | Config B |        0.93 |      0.65 |   0.71 |      0.83 | generation | Từ khóa câu hỏi có độ che phủ chưa cao |
|   2 | Đối tượng tuyển sinh của Chương trình Đào tạo... | Config B |        0.90 |      0.86 |   0.42 |      1.00 | retrieval | Tài liệu dài bị phân mảnh qua nhiều chunk |
|   3 | Quy định về việc triển khai Live URL cho sự k... | Config B |        0.97 |      0.95 |   1.00 |      0.50 | retrieval | Từ khóa chuyên biệt đòi hỏi ghép ngữ cảnh đa trang |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Bổ sung Semantic Chunking hoặc giữ nguyên bảng biểu cấu trúc | Một số câu hỏi về mốc checkpoint và deliverables bị chia cắt khi cắt văn bản cố định 500 ký tự | Tăng Context Recall thêm 8-12% trên các văn bản quy chế | Chạy lại bài test kiểm tra các câu hỏi về danh mục quy chế |
|        2 | Tinh chỉnh trọng số k trong RRF (thử nghiệm k=40 và k=80) | Các truy vấn có từ khóa chuyên ngành hiếm (SFIA, P&L) cần BM25 có trọng số nổi bật hơn | Cải thiện thứ hạng của các chunk chứa định nghĩa ngắn | Đo Context Precision trên nhóm câu hỏi từ viết tắt |
|        3 | Thêm Query Expansion hoặc HyDE (Hypothetical Document Embeddings) | Các câu hỏi dạng tổng quan của người dùng đôi khi dùng từ ngữ đời thường khác với từ ngữ pháp quy | Tăng tỷ lệ tìm đúng tài liệu khi câu hỏi không có từ khóa chính xác | So sánh Retrieval Recall trước và sau khi mở rộng câu truy vấn |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| Reordering context (Lost-in-the-middle) | Sequential Top-k context | +0.032 Faithfulness | 0ms / 0$ | Đặt tài liệu quan trọng nhất ở đầu và cuối context giúp LLM nắm bắt bằng chứng tốt hơn mà không tăng độ trễ. |