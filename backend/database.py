import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, desc
from sqlalchemy.orm import DeclarativeBase, Session

DB_PATH = os.getenv("DB_PATH", "highscores.db")

_db_engine = None


def _engine():
    global _db_engine
    if _db_engine is None:
        _db_engine = create_engine(
            f"sqlite:///{os.getenv('DB_PATH', DB_PATH)}",
            connect_args={"check_same_thread": False},
        )
    return _db_engine


def _dispose_engine():
    global _db_engine
    if _db_engine is not None:
        _db_engine.dispose()
        _db_engine = None


class Base(DeclarativeBase):
    pass


class Highscore(Base):
    __tablename__ = "highscores"
    id = Column(Integer, primary_key=True, autoincrement=True)
    player_name = Column(String, nullable=False)
    prize = Column(Integer, nullable=False)
    levels_reached = Column(Integer, nullable=False)
    played_at = Column(DateTime, default=datetime.utcnow)


def init_db() -> None:
    Base.metadata.create_all(_engine())


def save_score(player_name: str, prize: int, levels_reached: int) -> None:
    with Session(_engine()) as session:
        entry = Highscore(
            player_name=player_name,
            prize=prize,
            levels_reached=levels_reached,
        )
        session.add(entry)
        session.commit()


def get_top_scores(n: int = 10) -> list[dict]:
    with Session(_engine()) as session:
        rows = (
            session.query(Highscore)
            .order_by(desc(Highscore.prize))
            .limit(n)
            .all()
        )
        return [
            {
                "player_name": r.player_name,
                "prize": r.prize,
                "levels_reached": r.levels_reached,
                "played_at": r.played_at.isoformat() if r.played_at else "",
            }
            for r in rows
        ]
