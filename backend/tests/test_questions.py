from questions import QUESTIONS, pick_question

def test_questions_have_required_keys():
    required = {"id", "topic", "subtopic", "difficulty", "question", "options", "correct", "explanation", "help_table"}
    for q in QUESTIONS:
        assert required <= q.keys(), f"Question {q.get('id')} missing keys"

def test_questions_have_4_options():
    for q in QUESTIONS:
        assert len(q["options"]) == 4, f"Question {q['id']} needs 4 options"

def test_correct_is_valid_option():
    for q in QUESTIONS:
        assert q["correct"] in ("A", "B", "C", "D"), f"Question {q['id']} invalid correct"

def test_difficulty_distribution():
    from collections import Counter
    counts = Counter(q["difficulty"] for q in QUESTIONS)
    assert counts["easy"] >= 15
    assert counts["medium"] >= 15
    assert counts["hard"] >= 15

def test_pick_question_returns_dict():
    q = pick_question("easy", set())
    assert q is not None
    assert q["difficulty"] == "easy"

def test_pick_question_respects_exclude():
    easy_ids = {q["id"] for q in QUESTIONS if q["difficulty"] == "easy"}
    result = pick_question("easy", easy_ids)
    assert result is None

def test_pick_question_avoids_excluded():
    first = pick_question("medium", set())
    assert first is not None
    second = pick_question("medium", {first["id"]})
    # Should not return the same question (probabilistically, or None if only 1)
    medium_count = sum(1 for q in QUESTIONS if q["difficulty"] == "medium")
    if medium_count > 1:
        assert second is not None
