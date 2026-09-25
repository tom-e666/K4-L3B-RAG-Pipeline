# Kế hoạch cập nhật strategy từ remote

## Bản cập nhật mới nhất

- `origin/main` đã tiến đến `a7e9f69`, bổ sung grounding/citation verification, HyDE và MMR.
- Tạo worktree v2 `C:\AI\K4-L3B-RAG-Pipeline-strategy-eval-v2` trên nhánh `codex/strategy-eval-v2` từ commit đó. Worktree trước ở cổng 8502 vẫn được giữ nguyên để đối chiếu.
- Eval v2 dùng A dense-only, B đầy đủ và B không HyDE trên cùng 16 case; output ghi riêng `latest_details.json` và `latest_summary.json`.

## Trạng thái và phạm vi

- Checkout đang dùng: `C:\AI\vinai20k\K4-L3B-RAG-Pipeline`, giữ nguyên các file đang sửa và app ở cổng 8501.
- Remote đã fetch: `origin/main` tại `d9c18b6` (weighted RRF và LLM listwise rerank).
- Worktree tích hợp: `C:\AI\K4-L3B-RAG-Pipeline-strategy-eval`, nhánh `codex/strategy-eval` từ commit trên.
- Golden set 16 case, log Gemini trước đó và UI được sao chép sang worktree; không chạy `git pull` trên checkout đang dùng.

## Tích hợp và đo

1. Dùng `DeepSeek_API_KEY` qua OpenAI-compatible endpoint với model `deepseek-flash`; giữ BGE-M3 vì index 304 chunks hiện tại được tạo bằng model này.
2. Chạy trên cùng golden set: A dense-only; weighted RRF; weighted RRF + listwise rerank. Chỉ thay retrieval, giữ cùng generator và evaluator DeepSeek.
3. Ghi output riêng vào `remote_details.json` và `remote_summary.json` để không ghi đè lượt Gemini cũ. Đo bốn metric, p50 retrieval+generation, rerank fallback và PageIndex fallback.
4. Cập nhật `RESULT.md` bằng số thật và phân tích worst performers. Chạy test và kiểm tra UI trong worktree.

## Đưa vào checkout chính sau khi review

So sánh diff của nhánh `codex/strategy-eval` với `origin/main`, kiểm tra kết quả eval, rồi chọn thời điểm tích hợp vào checkout đang dùng. Nếu giữ hai phiên bản song song, có thể chạy app worktree trên cổng khác; việc xóa worktree không đụng tới checkout chính.
