from pydantic import BaseModel
from typing import Optional


class StartRequest(BaseModel):
    player_name: str


class QuestionOut(BaseModel):
    id: str
    question: str
    options: list[str]


class StartResponse(BaseModel):
    session_id: str
    question: QuestionOut
    level: int
    prize_ladder: list[int]
    safety_net_levels: list[int]


class AnswerRequest(BaseModel):
    session_id: str
    answer: str  # "A" | "B" | "C" | "D"


class AnswerResponse(BaseModel):
    correct: bool
    correct_answer: str
    explanation: str
    game_over: bool
    won: bool = False
    current_prize: int
    level: int
    next_question: Optional[QuestionOut] = None


class HelpRequest(BaseModel):
    session_id: str


class HelpTableResponse(BaseModel):
    table_content: str


class HelpEliminateResponse(BaseModel):
    remaining_options: list[str]


class HelpSkipResponse(BaseModel):
    new_question: Optional[QuestionOut]


class QuitRequest(BaseModel):
    session_id: str


class QuitResponse(BaseModel):
    final_prize: int
    game_over: bool = True
    levels_reached: int


class ScoreEntry(BaseModel):
    player_name: str
    prize: int
    levels_reached: int
    played_at: str
