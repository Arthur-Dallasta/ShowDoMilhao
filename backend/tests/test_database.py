import os
import pytest
from database import init_db, save_score, get_top_scores, _dispose_engine

TEST_DB = "test_highscores.db"


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / TEST_DB)
    _dispose_engine()
    monkeypatch.setenv("DB_PATH", db_path)
    init_db()
    yield
    _dispose_engine()
    if os.path.exists(db_path):
        os.remove(db_path)


def test_save_and_retrieve_score():
    save_score("Alice", 50_000, 10)
    scores = get_top_scores(10)
    assert len(scores) == 1
    assert scores[0]["player_name"] == "Alice"
    assert scores[0]["prize"] == 50_000


def test_top_scores_sorted_by_prize():
    save_score("Alice", 1_000, 1)
    save_score("Bob", 1_000_000, 15)
    save_score("Carol", 50_000, 10)
    scores = get_top_scores(10)
    assert scores[0]["player_name"] == "Bob"
    assert scores[1]["player_name"] == "Carol"


def test_top_scores_limit():
    for i in range(15):
        save_score(f"Player{i}", i * 1000, i)
    scores = get_top_scores(10)
    assert len(scores) == 10
