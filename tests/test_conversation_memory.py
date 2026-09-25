from src import task10_generation as generation


def test_first_question_skips_rewrite(monkeypatch):
    monkeypatch.setattr(generation, "call_llm", lambda *_: (_ for _ in ()).throw(AssertionError()))
    monkeypatch.setattr(generation, "generate_with_citation", lambda query, top_k: {"answer": query})
    result = generation.generate_with_memory("Điều kiện tham gia là gì?", [], top_k=5)
    assert result["answer"] == "Điều kiện tham gia là gì?"
    assert result["memory_rewritten"] is False


def test_followup_uses_standalone_query_for_retrieval(monkeypatch):
    prompts = []
    monkeypatch.setattr(generation, "call_llm", lambda system, prompt: prompts.append(prompt) or "Hạn nộp báo cáo Mentor Duty để được cộng XP là khi nào?")
    monkeypatch.setattr(generation, "generate_with_citation", lambda query, top_k: {"answer": query})
    history = [
        {"role": "user", "content": "Mentor Duty là gì?"},
        {"role": "assistant", "content": "Buổi trao đổi với mentor."},
    ]
    result = generation.generate_with_memory("Hạn nộp để được XP là khi nào?", history, top_k=5)
    assert result["answer"] == "Hạn nộp báo cáo Mentor Duty để được cộng XP là khi nào?"
    assert result["memory_rewritten"] is True
    assert "Mentor Duty là gì?" in prompts[0]


def test_rewrite_failure_falls_back_to_original(monkeypatch):
    def fail(*_):
        raise RuntimeError("provider unavailable")
    monkeypatch.setattr(generation, "call_llm", fail)
    monkeypatch.setattr(generation, "generate_with_citation", lambda query, top_k: {"answer": query})
    result = generation.generate_with_memory("Còn hạn nộp?", [{"role": "user", "content": "Mentor Duty?"}], top_k=5)
    assert result["retrieval_query"] == "Còn hạn nộp?"
    assert result["memory_rewritten"] is False


def test_rewrite_uses_at_most_two_previous_user_turns(monkeypatch):
    prompts = []
    monkeypatch.setattr(generation, "call_llm", lambda system, prompt: prompts.append(prompt) or "Câu hỏi độc lập?")
    history = [
        {"role": "user", "content": "OLD QUESTION"},
        {"role": "assistant", "content": "OLD ANSWER"},
        {"role": "user", "content": "Mentor Duty là gì?"},
        {"role": "assistant", "content": "Báo cáo định kỳ."},
        {"role": "user", "content": "Báo cáo gồm gì?"},
        {"role": "assistant", "content": "Năm trường."},
    ]
    generation.rewrite_followup_query("Còn deadline?", history)
    assert "OLD QUESTION" not in prompts[0]
    assert "Mentor Duty là gì?" in prompts[0]
    assert "Báo cáo gồm gì?" in prompts[0]
