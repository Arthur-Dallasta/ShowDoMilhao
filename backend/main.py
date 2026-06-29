from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import init_db, save_score, get_top_scores
from game import (
    GameState, PRIZES, SAFETY_NETS,
    create_game_state, evaluate_answer, apply_help, _safe_question,
)
from models import (
    StartRequest, StartResponse, QuestionOut,
    AnswerRequest, AnswerResponse,
    HelpRequest,
    QuitRequest, QuitResponse,
    ScoreEntry,
)

app = FastAPI(title="Show do Milhão")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: dict[str, GameState] = {}

# Initialize DB at import time so tests work without ASGI lifespan events
init_db()


@app.on_event("startup")
def startup():
    init_db()  # idempotent – safe to call again when server starts normally


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/game/start", response_model=StartResponse)
def start_game(body: StartRequest):
    state = create_game_state(body.player_name.strip() or "Jogador")
    sessions[state.session_id] = state
    return StartResponse(
        session_id=state.session_id,
        question=QuestionOut(**_safe_question(state.current_question)),
        level=state.current_level,
        prize_ladder=PRIZES,
        safety_net_levels=list(SAFETY_NETS.keys()),
    )


@app.post("/game/answer", response_model=AnswerResponse)
def answer(body: AnswerRequest):
    state = sessions.get(body.session_id)
    if not state:
        raise HTTPException(404, "Session not found")
    if body.answer not in ("A", "B", "C", "D"):
        raise HTTPException(400, "Answer must be A, B, C or D")

    is_correct, data = evaluate_answer(state, body.answer)

    if data["game_over"]:
        save_score(state.player_name, data["current_prize"], state.current_level)
        del sessions[body.session_id]

    next_q = data.get("next_question")
    return AnswerResponse(
        correct=data["correct"],
        correct_answer=data["correct_answer"],
        explanation=data["explanation"],
        game_over=data["game_over"],
        won=data.get("won", False),
        current_prize=data["current_prize"],
        level=data["level"],
        next_question=QuestionOut(**next_q) if next_q else None,
    )


@app.post("/game/help/{help_type}")
def help_endpoint(help_type: str, body: HelpRequest):
    state = sessions.get(body.session_id)
    if not state:
        raise HTTPException(404, "Session not found")
    if help_type not in ("table", "eliminate", "skip"):
        raise HTTPException(400, "Unknown help type")

    result = apply_help(state, help_type)
    if result.get("error") == "help_already_used":
        raise HTTPException(400, "Help already used")

    if help_type == "skip" and result.get("new_question"):
        result["new_question"] = QuestionOut(**result["new_question"]).model_dump()

    return result


@app.post("/game/quit", response_model=QuitResponse)
def quit_game(body: QuitRequest):
    state = sessions.get(body.session_id)
    if not state:
        raise HTTPException(404, "Session not found")
    prize = state.prize_if_quit
    levels = state.current_level
    save_score(state.player_name, prize, levels)
    del sessions[body.session_id]
    return QuitResponse(final_prize=prize, game_over=True, levels_reached=levels)


@app.get("/scores", response_model=list[ScoreEntry])
def scores():
    return get_top_scores(10)
