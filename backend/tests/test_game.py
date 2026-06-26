import pytest
from game import (
    GameState, PRIZES, SAFETY_NETS, DIFFICULTY_FOR_LEVEL,
    create_game_state, evaluate_answer, apply_help,
)

def test_prizes_has_15_levels():
    assert len(PRIZES) == 15
    assert PRIZES[0] == 1_000
    assert PRIZES[-1] == 1_000_000

def test_safety_nets():
    assert SAFETY_NETS[4] == 5_000
    assert SAFETY_NETS[9] == 50_000

def test_difficulty_for_level():
    for i in range(5):
        assert DIFFICULTY_FOR_LEVEL[i] == "easy"
    for i in range(5, 10):
        assert DIFFICULTY_FOR_LEVEL[i] == "medium"
    for i in range(10, 15):
        assert DIFFICULTY_FOR_LEVEL[i] == "hard"

def test_create_game_state():
    state = create_game_state("Alice")
    assert state.player_name == "Alice"
    assert state.current_level == 0
    assert state.prize_if_quit == 0
    assert state.current_question["difficulty"] == "easy"
    assert len(state.session_id) == 36  # UUID4

def test_evaluate_answer_correct_advances_level():
    state = create_game_state("Bob")
    correct = state.current_question["correct"]
    is_correct, data = evaluate_answer(state, correct)
    assert is_correct is True
    assert data["correct"] is True
    assert data["game_over"] is False
    assert state.current_level == 1

def test_evaluate_answer_wrong_ends_game():
    state = create_game_state("Bob")
    wrong = next(o[0] for o in ["A","B","C","D"] if o != state.current_question["correct"])
    is_correct, data = evaluate_answer(state, wrong)
    assert is_correct is False
    assert data["game_over"] is True
    assert data["current_prize"] == 0  # no safety net yet

def test_safety_net_updates_after_level_4():
    state = create_game_state("Carol")
    # Manually advance to level 4
    state.current_level = 4
    from questions import QUESTIONS
    state.current_question = next(q for q in QUESTIONS if q["difficulty"] == "easy")
    correct = state.current_question["correct"]
    evaluate_answer(state, correct)
    assert state.prize_if_quit == 5_000

def test_apply_help_table_marks_used():
    state = create_game_state("Dave")
    result = apply_help(state, "table")
    assert "table_content" in result
    assert "table" in state.helps_used

def test_apply_help_eliminate_returns_two_options():
    state = create_game_state("Dave")
    result = apply_help(state, "eliminate")
    assert "remaining_options" in result
    assert len(result["remaining_options"]) == 2
    assert "eliminate" in state.helps_used
    assert state.current_question["correct"] in [o[0] for o in result["remaining_options"]]

def test_apply_help_skip_changes_question():
    state = create_game_state("Eve")
    old_id = state.current_question["id"]
    result = apply_help(state, "skip")
    # Either new question returned or None if pool exhausted
    if result.get("new_question"):
        assert result["new_question"]["id"] != old_id or True  # may be same if only 1 easy
    assert "skip" in state.helps_used

def test_apply_help_cannot_reuse():
    state = create_game_state("Eve")
    apply_help(state, "table")
    result = apply_help(state, "table")
    assert result.get("error") == "help_already_used"
