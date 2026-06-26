import random
import uuid
from dataclasses import dataclass, field
from typing import Optional

from questions import pick_question, QUESTIONS

PRIZES = [
    1_000, 2_000, 3_000, 4_000, 5_000,
    10_000, 20_000, 30_000, 40_000, 50_000,
    100_000, 200_000, 300_000, 500_000, 1_000_000,
]

SAFETY_NETS: dict[int, int] = {4: 5_000, 9: 50_000}

DIFFICULTY_FOR_LEVEL: dict[int, str] = {
    **{i: "easy" for i in range(5)},
    **{i: "medium" for i in range(5, 10)},
    **{i: "hard" for i in range(10, 15)},
}


@dataclass
class GameState:
    session_id: str
    player_name: str
    current_level: int = 0
    prize_if_quit: int = 0
    current_question: dict = field(default_factory=dict)
    used_questions: set = field(default_factory=set)
    helps_used: set = field(default_factory=set)
    active_eliminates: Optional[list] = None


sessions: dict[str, "GameState"] = {}


def create_game_state(player_name: str) -> GameState:
    session_id = str(uuid.uuid4())
    state = GameState(session_id=session_id, player_name=player_name)
    q = pick_question("easy", set())
    if q is None:
        raise RuntimeError("No questions available for difficulty: easy")
    state.current_question = q
    state.used_questions.add(q["id"])
    return state


def _next_question(state: GameState) -> dict | None:
    difficulty = DIFFICULTY_FOR_LEVEL[state.current_level]
    q = pick_question(difficulty, state.used_questions)
    if q:
        state.used_questions.add(q["id"])
    return q


def evaluate_answer(state: GameState, answer: str) -> tuple[bool, dict]:
    correct = answer == state.current_question["correct"]
    base = {
        "correct": correct,
        "correct_answer": state.current_question["correct"],
        "explanation": state.current_question["explanation"],
    }
    if correct:
        # Update safety net before advancing level
        if state.current_level in SAFETY_NETS:
            state.prize_if_quit = SAFETY_NETS[state.current_level]
        state.current_level += 1
        state.active_eliminates = None

        if state.current_level >= len(PRIZES):
            return True, {**base, "game_over": True, "won": True,
                          "current_prize": PRIZES[-1], "level": state.current_level}

        next_q = _next_question(state)
        state.current_question = next_q or state.current_question
        return True, {
            **base,
            "game_over": False,
            "won": False,
            "current_prize": PRIZES[state.current_level - 1],
            "level": state.current_level,
            "next_question": _safe_question(state.current_question),
        }
    else:
        return False, {
            **base,
            "game_over": True,
            "won": False,
            "current_prize": state.prize_if_quit,
            "level": state.current_level,
        }


def apply_help(state: GameState, help_type: str) -> dict:
    if help_type in state.helps_used:
        return {"error": "help_already_used"}

    state.helps_used.add(help_type)

    if help_type == "table":
        return {"table_content": state.current_question.get("help_table", "")}

    if help_type == "eliminate":
        correct = state.current_question["correct"]
        wrong = [o for o in state.current_question["options"] if not o.startswith(correct)]
        to_remove = random.sample(wrong, min(2, len(wrong)))
        remaining = [o for o in state.current_question["options"] if o not in to_remove]
        state.active_eliminates = remaining
        return {"remaining_options": remaining}

    if help_type == "skip":
        difficulty = DIFFICULTY_FOR_LEVEL[state.current_level]
        new_q = pick_question(difficulty, state.used_questions)
        if new_q:
            state.used_questions.add(new_q["id"])
            state.current_question = new_q
            state.active_eliminates = None
            return {"new_question": _safe_question(new_q)}
        return {"new_question": None}

    return {"error": "unknown_help"}


def _safe_question(q: dict) -> dict:
    return {"id": q["id"], "question": q["question"], "options": q["options"]}
