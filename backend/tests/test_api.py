import pytest


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_start_game(client):
    resp = await client.post("/game/start", json={"player_name": "Arthur"})
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert "question" in data
    assert len(data["prize_ladder"]) == 15
    assert "correct" not in data["question"]  # never expose answer


@pytest.mark.asyncio
async def test_answer_correct(client):
    start = await client.post("/game/start", json={"player_name": "Tester"})
    sid = start.json()["session_id"]
    q_id = start.json()["question"]["id"]

    from questions import QUESTIONS
    correct = next(q["correct"] for q in QUESTIONS if q["id"] == q_id)

    resp = await client.post("/game/answer", json={"session_id": sid, "answer": correct})
    assert resp.status_code == 200
    data = resp.json()
    assert data["correct"] is True
    assert data["game_over"] is False
    assert data["level"] == 1


@pytest.mark.asyncio
async def test_answer_wrong_ends_game(client):
    start = await client.post("/game/start", json={"player_name": "Tester"})
    sid = start.json()["session_id"]
    q_id = start.json()["question"]["id"]

    from questions import QUESTIONS
    correct = next(q["correct"] for q in QUESTIONS if q["id"] == q_id)
    wrong = next(x for x in ["A", "B", "C", "D"] if x != correct)

    resp = await client.post("/game/answer", json={"session_id": sid, "answer": wrong})
    assert resp.status_code == 200
    data = resp.json()
    assert data["correct"] is False
    assert data["game_over"] is True
    assert data["current_prize"] == 0


@pytest.mark.asyncio
async def test_help_table(client):
    start = await client.post("/game/start", json={"player_name": "Tester"})
    sid = start.json()["session_id"]
    resp = await client.post("/game/help/table", json={"session_id": sid})
    assert resp.status_code == 200
    assert "table_content" in resp.json()


@pytest.mark.asyncio
async def test_help_eliminate(client):
    start = await client.post("/game/start", json={"player_name": "Tester"})
    sid = start.json()["session_id"]
    resp = await client.post("/game/help/eliminate", json={"session_id": sid})
    assert resp.status_code == 200
    assert len(resp.json()["remaining_options"]) == 2


@pytest.mark.asyncio
async def test_help_reuse_returns_400(client):
    start = await client.post("/game/start", json={"player_name": "Tester"})
    sid = start.json()["session_id"]
    await client.post("/game/help/table", json={"session_id": sid})
    resp = await client.post("/game/help/table", json={"session_id": sid})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_quit(client):
    start = await client.post("/game/start", json={"player_name": "Tester"})
    sid = start.json()["session_id"]
    resp = await client.post("/game/quit", json={"session_id": sid})
    assert resp.status_code == 200
    data = resp.json()
    assert data["game_over"] is True
    assert "final_prize" in data


@pytest.mark.asyncio
async def test_scores_endpoint(client):
    resp = await client.get("/scores")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
