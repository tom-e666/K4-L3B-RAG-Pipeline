# Báo cáo nhóm T021 — RAG Pipeline

## Sản phẩm

Nhóm xây dựng trợ lý hỏi đáp về chương trình AI20K từ 10 tài liệu Markdown đã chuẩn hóa (4 văn bản quy định và 6 bài viết/trang thông tin), tạo 304 chunks với `BAAI/bge-m3`. Ứng dụng Streamlit có trang Chat hiển thị câu trả lời kèm nguồn và trang Đánh giá A/B cho so sánh nhiều chiến lược trên cùng golden set. Cấu hình LLM mới nhất dùng DeepSeek qua `DeepSeek_API_KEY`.

Pipeline nâng cao: HyDE trước truy xuất → dense + BM25 → weighted RRF → LLM listwise rerank → MMR context packing → grounded generation → citation validation. A dense-only và B không HyDE được giữ làm đối chứng. PageIndex chưa được triển khai; không tính nó là thành phần hoạt động.

## Đánh giá

Golden set có 16 case: 8 semantic/paraphrase, 4 keyword/tên riêng, 2 cần nhiều nguồn và 2 ngoài phạm vi. Cùng DeepSeek generator/judge, prompt, 304 chunks và `top_k=5` trong lượt đo mới nhất:

| Cấu hình | Faithfulness | Relevance | Context recall | Context precision | Trung bình | p50 retrieval + generation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A dense-only | 1.000 | 0.906 | 0.885 | 0.719 | 0.878 | 2.130 s |
| B full | 1.000 | 0.906 | 0.823 | 0.844 | 0.893 | 11.027 s |
| B không HyDE | 1.000 | 0.844 | 0.854 | 0.844 | 0.885 | 9.288 s |

B full tăng trung bình 0.016 so với A, chủ yếu do context precision, nhưng context recall giảm 0.063 và p50 tăng 8.897 giây. HyDE tăng 0.008 so với B không HyDE. HyDE lỗi 0/16, rerank fallback 0/32, MMR lỗi 0/32; citation gate đạt 100% trong lượt mới nhất. Các con số là rubric nội bộ, không phải RAGAS; bộ 16 case và judge cùng họ model với generator chưa đủ cho quyết định production. Chi tiết phương pháp, các lượt đo trước và worst performers: [evaluation/RESULT.md](../group_project/evaluation/RESULT.md); dữ liệu gốc: [latest_summary.json](../group_project/evaluation/latest_summary.json), [latest_details.json](../group_project/evaluation/latest_details.json).

## Phân công và minh chứng Git

Git phân biệt **người được phân công** với **tác giả commit**. Bảng dưới chỉ gán phần đã thấy trực tiếp trong lịch sử; branch chứa một commit không tự chứng minh người đặt tên branch viết commit đó.

| Thành viên | Phân công theo `TEAMMATES.md` | Minh chứng kiểm tra được | Trạng thái ghi nhận |
| --- | --- | --- | --- |
| Thái Phúc Tiến (`2A202602873`) | Trưởng nhóm, dữ liệu và pipeline cơ bản | [`6e01a55`](https://github.com/tom-e666/K4-L3B-RAG-Pipeline/commit/6e01a55) thêm nguồn, tài liệu chuẩn hóa và pipeline; [`6f0e7a5`](https://github.com/tom-e666/K4-L3B-RAG-Pipeline/commit/6f0e7a5) thêm golden set, eval DeepSeek, dashboard multi-strategy và report | Có commit tác giả Tiến |
| Nguyễn Đức Long (`2A202602917`) | Retrieval, fusion và các kỹ thuật nâng cao | [`f5876c8`](https://github.com/tom-e666/K4-L3B-RAG-Pipeline/commit/f5876c8) weighted RRF; [`2989b37`](https://github.com/tom-e666/K4-L3B-RAG-Pipeline/commit/2989b37) listwise; [`db1d6a4`](https://github.com/tom-e666/K4-L3B-RAG-Pipeline/commit/db1d6a4) citation gate; [`9f3bcef`](https://github.com/tom-e666/K4-L3B-RAG-Pipeline/commit/9f3bcef) HyDE; [`00caf70`](https://github.com/tom-e666/K4-L3B-RAG-Pipeline/commit/00caf70) MMR | Có commit tác giả Long, được merge qua PR #1–#5 |
| Nguyễn Thành Luân (`2A202602769`) | Nghiên cứu, kiểm thử và đánh giá | [`8d5877a`](https://github.com/tom-e666/K4-L3B-RAG-Pipeline/commit/8d5877a) thêm `app.py` và `ui/` Streamlit; Git ghi tác giả `ThanhLuan` | Có commit UI tác giả Luân; công việc khác cần chứng cứ riêng |
| Trần Đình Duy (`2A202602631`) | Streamlit UI, dữ liệu, golden set, báo cáo | [`TEAMMATES.md`](../TEAMMATES.md) ghi vai trò; người yêu cầu báo cáo xác nhận Duy cùng làm UI với Luân; mã UI nằm trong [`8d5877a`](https://github.com/tom-e666/K4-L3B-RAG-Pipeline/commit/8d5877a) | Ghi nhận **đồng thực hiện UI theo xác nhận của người yêu cầu**, cần Duy và Luân xác nhận phạm vi cụ thể; Git chưa có commit tác giả Duy |

Commit `d9c18b6` trên nhánh `duytd` là merge PR #2 **từ `dlong`** về listwise rerank. Nó không chứng minh một PR UI của Duy. UI gốc ở `8d5877a` đã là tổ tiên của `main`; lần cập nhật `6f0e7a5` được đẩy fast-forward lên `main`, giữ nguyên lịch sử đó. Xác nhận Duy đồng thực hiện UI hiện đến từ người yêu cầu báo cáo, không phải metadata Git. Duy và Luân nên xác nhận phần cụ thể mỗi người làm; PR review, issue, ảnh demo hoặc biên bản sẽ làm chứng cứ cá nhân mạnh hơn.

## Hạn chế và hướng tiếp theo

`multi-01` và `sem-05` thiếu evidence nằm ở chunks khác; cần thử mở rộng chunks lân cận và đo lại. Exact-snippet recall bỏ sót trường hợp trả lời đúng từ nguồn thay thế như `sem-07`; cần nhãn fact-level. Giữ A cho truy vấn nhạy độ trễ, dùng B full có chọn lọc sau khi kiểm tra thêm và audit thủ công. PageIndex fallback và đánh giá độc lập với generator vẫn chưa hoàn thành.
