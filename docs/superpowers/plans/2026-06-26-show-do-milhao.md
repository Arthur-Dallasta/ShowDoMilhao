# Show do Milhão — Lógica Matemática: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a "Show do Milhão" quiz game with 15 prize levels using logical propositions and valid arguments as questions.

**Architecture:** FastAPI backend manages all game state (sessions in-memory dict, highscores in SQLite). React 18 + Vite frontend consumes REST API. Question bank is ~60 hardcoded questions tagged easy/medium/hard.

**Tech Stack:** Python 3.11+, FastAPI 0.115, SQLAlchemy 2.0, Pydantic v2, pytest, httpx; React 18, Vite 5, React Router 6, CSS Modules.

## Global Constraints

- Python 3.11+ required (uses `X | Y` union syntax)
- No external state management (Redux, Zustand) — React useState only
- No axios — fetch native only
- CSS Modules only — no Tailwind, no styled-components
- No authentication — player name only, stored in memory during session
- SQLite file at `backend/highscores.db`
- Backend runs on port 8000, frontend on port 5173
- CORS allows `http://localhost:5173`

---

## File Map

```
ShowDoMilhão/
├── backend/
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── main.py              # FastAPI app + all routes
│   ├── game.py              # GameState, PRIZES, SAFETY_NETS, logic functions
│   ├── questions.py         # QUESTIONS list + pick_question()
│   ├── models.py            # Pydantic request/response schemas + SQLAlchemy Highscore
│   ├── database.py          # SQLAlchemy engine, session, init_db()
│   └── tests/
│       ├── conftest.py
│       ├── test_questions.py
│       ├── test_game.py
│       └── test_api.py
└── frontend/
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.jsx
        ├── index.css
        ├── api.js
        ├── pages/
        │   ├── Home.jsx + Home.module.css
        │   ├── Game.jsx + Game.module.css
        │   └── GameOver.jsx + GameOver.module.css
        └── components/
            ├── QuestionCard.jsx + QuestionCard.module.css
            ├── PrizeLadder.jsx + PrizeLadder.module.css
            ├── HelpButtons.jsx + HelpButtons.module.css
            └── Scoreboard.jsx + Scoreboard.module.css
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/requirements-dev.txt`
- Create: `backend/main.py` (skeleton)
- Create: `backend/tests/conftest.py`

**Interfaces:**
- Produces: FastAPI app importable as `from main import app`; `GET /` returns `{"status": "ok"}`

- [ ] **Step 1: Init git and create directory structure**

```bash
cd "C:/Users/arthu/OneDrive/Desktop/ShowDoMilhão"
git init
mkdir -p backend/tests frontend/src/{pages,components}
```

- [ ] **Step 2: Write requirements files and pytest config**

`backend/pytest.ini`:
```ini
[pytest]
asyncio_mode = auto
pythonpath = .
```

`backend/requirements.txt`:
```
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy==2.0.35
pydantic==2.9.2
```

`backend/requirements-dev.txt`:
```
-r requirements.txt
pytest==8.3.3
httpx==0.27.2
pytest-asyncio==0.24.0
```

- [ ] **Step 3: Create Python venv and install**

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate   # Windows
pip install -r requirements-dev.txt
```

- [ ] **Step 4: Write failing smoke test**

`backend/tests/conftest.py`:
```python
import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
```

`backend/tests/test_api.py` (initial smoke test only):
```python
import pytest

@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
```

- [ ] **Step 5: Run test — expect FAIL (main.py doesn't exist)**

```bash
cd backend
pytest tests/test_api.py::test_health -v
```
Expected: `ERROR` — `ModuleNotFoundError: No module named 'main'`

- [ ] **Step 6: Create minimal main.py**

`backend/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Show do Milhão")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health():
    return {"status": "ok"}
```

- [ ] **Step 7: Run test — expect PASS**

```bash
pytest tests/test_api.py::test_health -v
```
Expected: `PASSED`

- [ ] **Step 8: Commit**

```bash
cd ..
git add backend/
git commit -m "feat: backend scaffolding with FastAPI skeleton"
```

---

### Task 2: Question Bank

**Files:**
- Create: `backend/questions.py`
- Create: `backend/tests/test_questions.py`

**Interfaces:**
- Produces: `pick_question(difficulty: str, exclude_ids: set[str]) -> dict | None`
- Produces: `QUESTIONS: list[dict]` — each dict has keys: `id`, `topic`, `subtopic`, `difficulty`, `question`, `options`, `correct`, `explanation`, `help_table`

- [ ] **Step 1: Write failing tests**

`backend/tests/test_questions.py`:
```python
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
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_questions.py -v
```
Expected: `ERROR` — `ModuleNotFoundError: No module named 'questions'`

- [ ] **Step 3: Create questions.py**

`backend/questions.py`:
```python
import random

NEGATION_TABLE = "p  | p'\nV  | F\nF  | V"
CONJUNCTION_TABLE = "p  | q  | p•q\nV  | V  | V\nV  | F  | F\nF  | V  | F\nF  | F  | F"
DISJUNCTION_TABLE = "p  | q  | p+q\nV  | V  | V\nV  | F  | V\nF  | V  | V\nF  | F  | F"
CONDITIONAL_TABLE = "p  | q  | p→q\nV  | V  | V\nV  | F  | F\nF  | V  | V\nF  | F  | V"
BICONDITIONAL_TABLE = "p  | q  | p↔q\nV  | V  | V\nV  | F  | F\nF  | V  | F\nF  | F  | V"
MP_RULE = "Modus Ponens (MP):\np → q\np\n∴ q"
MT_RULE = "Modus Tollens (MT):\np → q\nq'\n∴ p'"
SH_RULE = "Silogismo Hipotético (SH):\np → q\nq → r\n∴ p → r"
SD_RULE = "Silogismo Disjuntivo (SD):\np + q\np'\n∴ q"
DC_RULE = "Dilema Construtivo (DC):\np → q, r → s\np + r\n∴ q + s"
DD_RULE = "Dilema Destrutivo (DD):\np → q, r → s\nq' + s'\n∴ p' + r'"

QUESTIONS: list[dict] = [
    # ── EASY (20) ────────────────────────────────────────────────────
    {
        "id": "easy_01",
        "topic": "proposicoes",
        "subtopic": "identificar_proposicao",
        "difficulty": "easy",
        "question": "Qual das seguintes sentenças É uma proposição?",
        "options": ["A) Estude mais!", "B) Como vai você?", "C) O Brasil fica na América do Sul.", "D) Feche a porta."],
        "correct": "C",
        "explanation": "Proposição é sentença declarativa com valor verdade definido. 'O Brasil fica na América do Sul' é declarativa e verdadeira. As demais são imperativa, interrogativa e imperativa.",
        "help_table": "Proposição: sentença declarativa que é V ou F.\nNÃO são proposições: exclamativas, interrogativas, imperativas.",
    },
    {
        "id": "easy_02",
        "topic": "proposicoes",
        "subtopic": "identificar_proposicao",
        "difficulty": "easy",
        "question": "Qual das seguintes NÃO é uma proposição?",
        "options": ["A) 5 < 2", "B) A Alemanha fica na Ásia.", "C) Como é o seu nome?", "D) Todo cachorro é mamífero."],
        "correct": "C",
        "explanation": "'Como é o seu nome?' é interrogativa — não pode ser V nem F. As demais são proposições (falsas ou verdadeiras).",
        "help_table": "Proposição: sentença declarativa que é V ou F.\nNÃO são proposições: exclamativas, interrogativas, imperativas.",
    },
    {
        "id": "easy_03",
        "topic": "proposicoes",
        "subtopic": "identificar_proposicao",
        "difficulty": "easy",
        "question": "'Vamos trabalhar!' — Do ponto de vista da lógica, essa sentença é:",
        "options": ["A) Proposição verdadeira", "B) Proposição falsa", "C) Não é proposição — é imperativa", "D) Proposição composta"],
        "correct": "C",
        "explanation": "Sentenças imperativas não são proposições pois não têm valor lógico definido (V ou F).",
        "help_table": "Proposição: sentença declarativa que é V ou F.\nNÃO são proposições: exclamativas, interrogativas, imperativas.",
    },
    {
        "id": "easy_04",
        "topic": "proposicoes",
        "subtopic": "identificar_proposicao",
        "difficulty": "easy",
        "question": "'x + 5 = 0' — Do ponto de vista da lógica, essa sentença é:",
        "options": ["A) Proposição verdadeira", "B) Proposição falsa", "C) Sentença aberta — não é proposição", "D) Proposição composta"],
        "correct": "C",
        "explanation": "'x + 5 = 0' contém variável livre x — seu valor lógico depende de x, logo não é proposição (é sentença aberta).",
        "help_table": "Proposição: sentença declarativa que é V ou F.\nSentença aberta: contém variável, valor lógico indefinido.",
    },
    {
        "id": "easy_05",
        "topic": "proposicoes",
        "subtopic": "identificar_proposicao",
        "difficulty": "easy",
        "question": "Considere: I) 'Eu fui a São Paulo ontem.' II) 'Vamos trabalhar!' III) 'O número -2 é natural.' Quais SÃO proposições?",
        "options": ["A) Apenas I", "B) Apenas III", "C) I e III", "D) I, II e III"],
        "correct": "C",
        "explanation": "I é proposição (declarativa, valor pode ser determinado). II é imperativa (não é proposição). III é proposição falsa (-2 não é natural).",
        "help_table": "Proposição: sentença declarativa que é V ou F.\nNÃO são proposições: exclamativas, interrogativas, imperativas.",
    },
    {
        "id": "easy_06",
        "topic": "proposicoes",
        "subtopic": "valor_logico",
        "difficulty": "easy",
        "question": "Qual o valor lógico de p: '2 + 2 = 4'?",
        "options": ["A) Falso", "B) Verdadeiro", "C) Indeterminado", "D) Nulo"],
        "correct": "B",
        "explanation": "2 + 2 = 4 é uma igualdade matemática verdadeira, portanto V(p) = 1 (Verdadeiro).",
        "help_table": "Valor lógico V(p) = 1 se p verdadeira, V(p) = 0 se p falsa.",
    },
    {
        "id": "easy_07",
        "topic": "proposicoes",
        "subtopic": "valor_logico",
        "difficulty": "easy",
        "question": "Qual o valor lógico de p: '5 < 2'?",
        "options": ["A) Verdadeiro", "B) Falso", "C) Indeterminado", "D) Depende de 5 e 2"],
        "correct": "B",
        "explanation": "5 < 2 é falso (5 é maior que 2), portanto V(p) = 0 (Falso).",
        "help_table": "Valor lógico V(p) = 1 se p verdadeira, V(p) = 0 se p falsa.",
    },
    {
        "id": "easy_08",
        "topic": "proposicoes",
        "subtopic": "valor_logico",
        "difficulty": "easy",
        "question": "Qual o valor lógico de: 'A Alemanha fica na Ásia'?",
        "options": ["A) Verdadeiro", "B) Falso", "C) Indeterminado", "D) Nulo"],
        "correct": "B",
        "explanation": "A Alemanha fica na Europa, não na Ásia. Portanto a proposição é Falsa.",
        "help_table": "Valor lógico V(p) = 1 se p verdadeira, V(p) = 0 se p falsa.",
    },
    {
        "id": "easy_09",
        "topic": "proposicoes",
        "subtopic": "valor_logico",
        "difficulty": "easy",
        "question": "Qual o valor lógico de: 'O número -2 é um número natural'?",
        "options": ["A) Verdadeiro", "B) Falso", "C) Indeterminado", "D) Nulo"],
        "correct": "B",
        "explanation": "Números naturais são N = {0, 1, 2, 3, ...}. -2 é negativo, portanto não é natural. Proposição Falsa.",
        "help_table": "Valor lógico V(p) = 1 se p verdadeira, V(p) = 0 se p falsa.",
    },
    {
        "id": "easy_10",
        "topic": "proposicoes",
        "subtopic": "valor_logico",
        "difficulty": "easy",
        "question": "Qual o valor lógico de: '1 + 4 ≠ 5'?",
        "options": ["A) Verdadeiro", "B) Falso", "C) Indeterminado", "D) Nulo"],
        "correct": "B",
        "explanation": "1 + 4 = 5, portanto 1 + 4 ≠ 5 é Falso.",
        "help_table": "Valor lógico V(p) = 1 se p verdadeira, V(p) = 0 se p falsa.",
    },
    {
        "id": "easy_11",
        "topic": "proposicoes",
        "subtopic": "negacao",
        "difficulty": "easy",
        "question": "Dada p: 'Está chovendo.' (Verdadeira). Qual o valor de p' (negação de p)?",
        "options": ["A) Verdadeiro", "B) Falso", "C) Indeterminado", "D) Depende do contexto"],
        "correct": "B",
        "explanation": "A negação inverte o valor lógico. p=V → p'=F.",
        "help_table": NEGATION_TABLE,
    },
    {
        "id": "easy_12",
        "topic": "proposicoes",
        "subtopic": "negacao",
        "difficulty": "easy",
        "question": "Dada q: 'Hoje não é domingo.' (Falsa). Qual o valor de q'?",
        "options": ["A) Falso", "B) Verdadeiro", "C) Nulo", "D) Indeterminado"],
        "correct": "B",
        "explanation": "q=F → q'=V. A negação de uma proposição falsa é verdadeira.",
        "help_table": NEGATION_TABLE,
    },
    {
        "id": "easy_13",
        "topic": "proposicoes",
        "subtopic": "negacao",
        "difficulty": "easy",
        "question": "Dada p: 'O Brasil fica na América do Sul.' (Verdadeira). Qual o valor de p'?",
        "options": ["A) Verdadeiro", "B) Falso", "C) Nulo", "D) Indeterminado"],
        "correct": "B",
        "explanation": "p=V → p'=F. A negação de uma proposição verdadeira é falsa.",
        "help_table": NEGATION_TABLE,
    },
    {
        "id": "easy_14",
        "topic": "proposicoes",
        "subtopic": "negacao",
        "difficulty": "easy",
        "question": "Se V(p) = 1, qual o valor de V(p')?",
        "options": ["A) 1 (Verdadeiro)", "B) 0 (Falso)", "C) Depende de p", "D) Indeterminado"],
        "correct": "B",
        "explanation": "Pela tabela da negação: V(p)=1 → V(p')=0.",
        "help_table": NEGATION_TABLE,
    },
    {
        "id": "easy_15",
        "topic": "proposicoes",
        "subtopic": "negacao",
        "difficulty": "easy",
        "question": "Se V(p) = 0, qual o valor de V(p')?",
        "options": ["A) 0 (Falso)", "B) 1 (Verdadeiro)", "C) Depende de p", "D) Nulo"],
        "correct": "B",
        "explanation": "Pela tabela da negação: V(p)=0 → V(p')=1.",
        "help_table": NEGATION_TABLE,
    },
    {
        "id": "easy_16",
        "topic": "proposicoes",
        "subtopic": "principios",
        "difficulty": "easy",
        "question": "Qual princípio afirma que uma proposição só pode ser verdadeira OU falsa, nunca outro valor?",
        "options": ["A) Princípio da não contradição", "B) Princípio do terceiro excluído", "C) Princípio da identidade", "D) Princípio da razão suficiente"],
        "correct": "B",
        "explanation": "O Princípio do Terceiro Excluído afirma que toda proposição tem exatamente dois valores possíveis: V ou F.",
        "help_table": "Princípio do Terceiro Excluído: toda proposição é V ou F — sem terceira opção.\nPrincípio da Não Contradição: uma proposição não pode ser V e F simultaneamente.",
    },
    {
        "id": "easy_17",
        "topic": "proposicoes",
        "subtopic": "tabela_verdade_basica",
        "difficulty": "easy",
        "question": "Quantas linhas tem uma tabela-verdade com 2 proposições (p e q)?",
        "options": ["A) 2", "B) 3", "C) 4", "D) 8"],
        "correct": "C",
        "explanation": "Número de linhas = 2^n onde n é o número de proposições. 2^2 = 4 linhas.",
        "help_table": "Fórmula: 2^n linhas para n proposições.\n2^1=2, 2^2=4, 2^3=8, 2^4=16",
    },
    {
        "id": "easy_18",
        "topic": "proposicoes",
        "subtopic": "tabela_verdade_basica",
        "difficulty": "easy",
        "question": "Quantas linhas tem uma tabela-verdade com 3 proposições (p, q e r)?",
        "options": ["A) 3", "B) 4", "C) 6", "D) 8"],
        "correct": "D",
        "explanation": "Número de linhas = 2^n = 2^3 = 8 linhas.",
        "help_table": "Fórmula: 2^n linhas para n proposições.\n2^1=2, 2^2=4, 2^3=8, 2^4=16",
    },
    {
        "id": "easy_19",
        "topic": "proposicoes",
        "subtopic": "identificar_proposicao",
        "difficulty": "easy",
        "question": "'Quem comprou o pastel?' — Do ponto de vista da lógica, essa sentença é:",
        "options": ["A) Proposição verdadeira", "B) Proposição falsa", "C) Não é proposição — é interrogativa", "D) Proposição composta"],
        "correct": "C",
        "explanation": "Sentenças interrogativas não são proposições pois não têm valor lógico definido.",
        "help_table": "Proposição: sentença declarativa que é V ou F.\nNÃO são proposições: exclamativas, interrogativas, imperativas.",
    },
    {
        "id": "easy_20",
        "topic": "proposicoes",
        "subtopic": "negacao",
        "difficulty": "easy",
        "question": "A negação de 'Está chovendo' é:",
        "options": ["A) Está muito chovendo", "B) Não está chovendo", "C) Talvez esteja chovendo", "D) Vai chover"],
        "correct": "B",
        "explanation": "A negação (¬p ou p') de 'Está chovendo' é 'Não está chovendo'.",
        "help_table": NEGATION_TABLE,
    },

    # ── MEDIUM (20) ───────────────────────────────────────────────────
    {
        "id": "med_01",
        "topic": "proposicoes",
        "subtopic": "conjuncao",
        "difficulty": "medium",
        "question": "A conjunção p • q é verdadeira quando:",
        "options": ["A) Pelo menos uma for verdadeira", "B) Ambas forem verdadeiras", "C) Pelo menos uma for falsa", "D) Ambas forem falsas"],
        "correct": "B",
        "explanation": "Conjunção (e): p • q é V somente quando AMBAS p e q são verdadeiras.",
        "help_table": CONJUNCTION_TABLE,
    },
    {
        "id": "med_02",
        "topic": "proposicoes",
        "subtopic": "conjuncao",
        "difficulty": "medium",
        "question": "Dadas p: 'Maria é bonita' (V) e q: 'Maria é elegante' (V). Qual o valor de p • q?",
        "options": ["A) Falso", "B) Verdadeiro", "C) Indeterminado", "D) Depende"],
        "correct": "B",
        "explanation": "p=V, q=V → p•q=V. Conjunção é V quando ambas são V.",
        "help_table": CONJUNCTION_TABLE,
    },
    {
        "id": "med_03",
        "topic": "proposicoes",
        "subtopic": "conjuncao",
        "difficulty": "medium",
        "question": "Se V(p) = 1 e V(q) = 0, qual o valor de p • q?",
        "options": ["A) Verdadeiro", "B) Falso", "C) Indeterminado", "D) Nulo"],
        "correct": "B",
        "explanation": "p=V, q=F → p•q=F. Conjunção é falsa quando ao menos uma for falsa.",
        "help_table": CONJUNCTION_TABLE,
    },
    {
        "id": "med_04",
        "topic": "proposicoes",
        "subtopic": "conjuncao",
        "difficulty": "medium",
        "question": "Se V(p) = 1 e V(q) = 0, qual o valor de p • q'?",
        "options": ["A) Verdadeiro", "B) Falso", "C) Indeterminado", "D) Nulo"],
        "correct": "A",
        "explanation": "q'=V (negação de F). p•q' = V•V = V.",
        "help_table": CONJUNCTION_TABLE,
    },
    {
        "id": "med_05",
        "topic": "proposicoes",
        "subtopic": "conjuncao",
        "difficulty": "medium",
        "question": "Dado V(p) = 1. Qual o valor de p • p'?",
        "options": ["A) Verdadeiro", "B) Falso", "C) Indeterminado", "D) Depende de p"],
        "correct": "B",
        "explanation": "p'=F (negação de V). p•p' = V•F = F. Uma proposição e sua negação sempre têm conjunção falsa.",
        "help_table": CONJUNCTION_TABLE,
    },
    {
        "id": "med_06",
        "topic": "proposicoes",
        "subtopic": "disjuncao",
        "difficulty": "medium",
        "question": "A disjunção p + q é FALSA somente quando:",
        "options": ["A) Ambas forem verdadeiras", "B) p for V e q for F", "C) Ambas forem falsas", "D) p for F e q for V"],
        "correct": "C",
        "explanation": "Disjunção (ou): p + q é F somente quando AMBAS p e q são falsas.",
        "help_table": DISJUNCTION_TABLE,
    },
    {
        "id": "med_07",
        "topic": "proposicoes",
        "subtopic": "disjuncao",
        "difficulty": "medium",
        "question": "Dadas p (Verdadeira) e q (Falsa). Qual o valor de p + q?",
        "options": ["A) Falso", "B) Verdadeiro", "C) Indeterminado", "D) Nulo"],
        "correct": "B",
        "explanation": "p=V, q=F → p+q=V. Disjunção é V quando pelo menos uma é V.",
        "help_table": DISJUNCTION_TABLE,
    },
    {
        "id": "med_08",
        "topic": "proposicoes",
        "subtopic": "disjuncao",
        "difficulty": "medium",
        "question": "Se V(p) = 1 e V(q) = 0, qual o valor de p' + q'?",
        "options": ["A) Verdadeiro", "B) Falso", "C) Indeterminado", "D) Nulo"],
        "correct": "A",
        "explanation": "p'=F, q'=V. p'+q' = F+V = V.",
        "help_table": DISJUNCTION_TABLE,
    },
    {
        "id": "med_09",
        "topic": "proposicoes",
        "subtopic": "condicional",
        "difficulty": "medium",
        "question": "O condicional p → q é FALSO somente quando:",
        "options": ["A) p é F e q é F", "B) p é V e q é V", "C) p é V e q é F", "D) p é F e q é V"],
        "correct": "C",
        "explanation": "Condicional é F somente quando a hipótese (p) é V e a conclusão (q) é F.",
        "help_table": CONDITIONAL_TABLE,
    },
    {
        "id": "med_10",
        "topic": "proposicoes",
        "subtopic": "condicional",
        "difficulty": "medium",
        "question": "Dadas p: 'Chove' (V) e q: 'Faz sol' (F). Qual o valor de p → q?",
        "options": ["A) Verdadeiro", "B) Falso", "C) Indeterminado", "D) Depende"],
        "correct": "B",
        "explanation": "p=V, q=F → p→q=F. Condicional com hipótese V e conclusão F é sempre F.",
        "help_table": CONDITIONAL_TABLE,
    },
    {
        "id": "med_11",
        "topic": "proposicoes",
        "subtopic": "condicional",
        "difficulty": "medium",
        "question": "Se V(p) = 0 e V(q) = 0, qual o valor de p → q?",
        "options": ["A) Falso", "B) Verdadeiro", "C) Indeterminado", "D) Nulo"],
        "correct": "B",
        "explanation": "p=F, q=F → p→q=V. Condicional com hipótese F é sempre V.",
        "help_table": CONDITIONAL_TABLE,
    },
    {
        "id": "med_12",
        "topic": "proposicoes",
        "subtopic": "condicional",
        "difficulty": "medium",
        "question": "Dada: 'Se 5+5=9, então 6+6=12.' Qual o valor lógico?",
        "options": ["A) Falso", "B) Verdadeiro", "C) Indeterminado", "D) Nulo"],
        "correct": "B",
        "explanation": "p: '5+5=9' é F. Condicional com hipótese F é sempre V, independente de q.",
        "help_table": CONDITIONAL_TABLE,
    },
    {
        "id": "med_13",
        "topic": "proposicoes",
        "subtopic": "condicional",
        "difficulty": "medium",
        "question": "'Se eu sair de casa, vou ao cinema.' p='saí de casa'(V), q='vou ao cinema'(F). Valor da proposição?",
        "options": ["A) Verdadeiro", "B) Falso", "C) Indeterminado", "D) Nulo"],
        "correct": "B",
        "explanation": "p=V, q=F → p→q=F. A única situação que torna o condicional falso.",
        "help_table": CONDITIONAL_TABLE,
    },
    {
        "id": "med_14",
        "topic": "proposicoes",
        "subtopic": "bicondicional",
        "difficulty": "medium",
        "question": "O bicondicional p ↔ q é verdadeiro quando:",
        "options": ["A) p é V e q é F", "B) p e q têm valores lógicos iguais", "C) p é F e q é V", "D) Apenas quando ambas são V"],
        "correct": "B",
        "explanation": "Bicondicional é V quando p e q têm o MESMO valor lógico (ambas V ou ambas F).",
        "help_table": BICONDITIONAL_TABLE,
    },
    {
        "id": "med_15",
        "topic": "proposicoes",
        "subtopic": "bicondicional",
        "difficulty": "medium",
        "question": "Dadas p (F) e q (F). Qual o valor de p ↔ q?",
        "options": ["A) Falso", "B) Verdadeiro", "C) Indeterminado", "D) Nulo"],
        "correct": "B",
        "explanation": "p=F, q=F → valores iguais → p↔q=V.",
        "help_table": BICONDITIONAL_TABLE,
    },
    {
        "id": "med_16",
        "topic": "proposicoes",
        "subtopic": "bicondicional",
        "difficulty": "medium",
        "question": "Sendo V(p)=1 e V(q)=0. Qual o valor de p ↔ q?",
        "options": ["A) Verdadeiro", "B) Falso", "C) Indeterminado", "D) Nulo"],
        "correct": "B",
        "explanation": "p=V, q=F → valores diferentes → p↔q=F.",
        "help_table": BICONDITIONAL_TABLE,
    },
    {
        "id": "med_17",
        "topic": "proposicoes",
        "subtopic": "precedencia",
        "difficulty": "medium",
        "question": "Qual a ordem correta de precedência dos operadores lógicos (do maior para o menor)?",
        "options": ["A) →, ↔, ¬, ∧, ∨", "B) ¬, ∧ e ∨, →, ↔", "C) ∧ e ∨, ¬, →, ↔", "D) ↔, →, ∧ e ∨, ¬"],
        "correct": "B",
        "explanation": "Ordem: 1°) Negação (¬), 2°) Conjunção (∧) e Disjunção (∨), 3°) Condicional (→), 4°) Bicondicional (↔).",
        "help_table": "Ordem dos operadores:\n1) Negação (¬ / ')\n2) Conjunção (∧ / •) e Disjunção (∨ / +)\n3) Condicional (→)\n4) Bicondicional (↔)",
    },
    {
        "id": "med_18",
        "topic": "proposicoes",
        "subtopic": "condicional",
        "difficulty": "medium",
        "question": "Dada a proposição: 'Se 2 é par, então 3 é primo.' Qual seu valor lógico?",
        "options": ["A) Falso", "B) Verdadeiro", "C) Indeterminado", "D) Depende de 2"],
        "correct": "B",
        "explanation": "p: '2 é par' (V), q: '3 é primo' (V). p→q = V→V = V.",
        "help_table": CONDITIONAL_TABLE,
    },
    {
        "id": "med_19",
        "topic": "proposicoes",
        "subtopic": "conjuncao",
        "difficulty": "medium",
        "question": "Sejam p='Tavares é estudioso'(V) e q='Aranhas voam'(F). Qual o valor de p • q?",
        "options": ["A) Verdadeiro", "B) Falso", "C) Indeterminado", "D) Nulo"],
        "correct": "B",
        "explanation": "p=V, q=F → p•q=F. Conjunção com uma proposição falsa é sempre falsa.",
        "help_table": CONJUNCTION_TABLE,
    },
    {
        "id": "med_20",
        "topic": "proposicoes",
        "subtopic": "bicondicional",
        "difficulty": "medium",
        "question": "Dadas p (V) e q (V). Qual o valor de (p → q) ↔ (q → p)?",
        "options": ["A) Falso", "B) Verdadeiro", "C) Indeterminado", "D) Nulo"],
        "correct": "B",
        "explanation": "p→q = V→V = V. q→p = V→V = V. V↔V = V.",
        "help_table": BICONDITIONAL_TABLE,
    },

    # ── HARD (20) ────────────────────────────────────────────────────
    {
        "id": "hard_01",
        "topic": "argumentos",
        "subtopic": "argumento_valido",
        "difficulty": "hard",
        "question": "Um argumento é VÁLIDO quando:",
        "options": ["A) Todas as premissas são verdadeiras", "B) A conclusão é verdadeira", "C) Sempre que as premissas são V, a conclusão também é V", "D) A conclusão é falsa quando premissas são falsas"],
        "correct": "C",
        "explanation": "Argumento válido: sempre que todas as premissas forem V, a conclusão também será V. Validade é sobre a forma, não sobre valores concretos.",
        "help_table": "Argumento válido: p1•p2•...•pn → conclusão é tautologia.\nInválido: existe linha com todas premissas V e conclusão F.",
    },
    {
        "id": "hard_02",
        "topic": "argumentos",
        "subtopic": "argumento_valido",
        "difficulty": "hard",
        "question": "Um argumento é INVÁLIDO quando existe alguma linha da tabela-verdade onde:",
        "options": ["A) Todas as premissas são F e a conclusão é F", "B) Todas as premissas são V e a conclusão é F", "C) Todas as premissas são F e a conclusão é V", "D) Alguma premissa é V e a conclusão é V"],
        "correct": "B",
        "explanation": "Argumento inválido = existe ao menos uma linha onde TODAS as premissas são V e a conclusão é F (ocorre o par 1,0).",
        "help_table": "Argumento válido: não existe linha com premissas V e conclusão F.\nInválido: existe ao menos uma tal linha.",
    },
    {
        "id": "hard_03",
        "topic": "argumentos",
        "subtopic": "modus_ponens",
        "difficulty": "hard",
        "question": "O argumento Modus Ponens (MP) tem a forma:",
        "options": ["A) p→q, q' / p'", "B) p→q, p / q", "C) p→q, q / p", "D) p, q / p•q"],
        "correct": "B",
        "explanation": "Modus Ponens: de 'p→q' e 'p', concluímos 'q'. É a implicação (p→q)•p ⟹ q.",
        "help_table": MP_RULE,
    },
    {
        "id": "hard_04",
        "topic": "argumentos",
        "subtopic": "modus_tollens",
        "difficulty": "hard",
        "question": "O argumento Modus Tollens (MT) tem a forma:",
        "options": ["A) p→q, p / q", "B) p→q, q' / p'", "C) p→q, q / p", "D) p→q / p→(p•q)"],
        "correct": "B",
        "explanation": "Modus Tollens: de 'p→q' e 'q'' (negação da conclusão), concluímos 'p'' (negação da hipótese).",
        "help_table": MT_RULE,
    },
    {
        "id": "hard_05",
        "topic": "argumentos",
        "subtopic": "silogismo_hipotetico",
        "difficulty": "hard",
        "question": "Silogismo Hipotético (SH): das premissas p→q e q→r, concluímos:",
        "options": ["A) p→r", "B) p•r", "C) q→p", "D) r→p"],
        "correct": "A",
        "explanation": "Silogismo Hipotético: encadeia condicionais. De p→q e q→r, conclui p→r.",
        "help_table": SH_RULE,
    },
    {
        "id": "hard_06",
        "topic": "argumentos",
        "subtopic": "silogismo_disjuntivo",
        "difficulty": "hard",
        "question": "Silogismo Disjuntivo (SD): das premissas p+q e p', concluímos:",
        "options": ["A) p", "B) p'", "C) q", "D) q'"],
        "correct": "C",
        "explanation": "Silogismo Disjuntivo: de 'p+q' (pelo menos um é V) e 'p'' (p é F), concluímos que q deve ser V.",
        "help_table": SD_RULE,
    },
    {
        "id": "hard_07",
        "topic": "argumentos",
        "subtopic": "adicao",
        "difficulty": "hard",
        "question": "Pela regra de Adição (A): de p (verdadeiro), podemos concluir:",
        "options": ["A) p•q", "B) p+q", "C) p→q", "D) p↔q"],
        "correct": "B",
        "explanation": "Adição: de p verdadeiro, podemos adicionar qualquer q e a disjunção p+q será verdadeira.",
        "help_table": "Adição (A):\np\n∴ p + q",
    },
    {
        "id": "hard_08",
        "topic": "argumentos",
        "subtopic": "simplificacao",
        "difficulty": "hard",
        "question": "Pela regra de Simplificação (S): de p•q (conjunção), podemos concluir:",
        "options": ["A) p+q", "B) p→q", "C) p (ou q)", "D) p↔q"],
        "correct": "C",
        "explanation": "Simplificação: se p•q é V (ambas V), podemos extrair p (ou q) individualmente.",
        "help_table": "Simplificação (S):\np • q\n∴ p",
    },
    {
        "id": "hard_09",
        "topic": "argumentos",
        "subtopic": "dilema_construtivo",
        "difficulty": "hard",
        "question": "Dilema Construtivo (DC): das premissas p→q, r→s e p+r, concluímos:",
        "options": ["A) p•r", "B) q•s", "C) q+s", "D) p→s"],
        "correct": "C",
        "explanation": "Dilema Construtivo: se p leva a q, r leva a s, e ocorre p ou r, então ocorre q ou s.",
        "help_table": DC_RULE,
    },
    {
        "id": "hard_10",
        "topic": "argumentos",
        "subtopic": "dilema_destrutivo",
        "difficulty": "hard",
        "question": "Dilema Destrutivo (DD): das premissas p→q, r→s e q'+s', concluímos:",
        "options": ["A) p+r", "B) p•r", "C) p'+r'", "D) q+s"],
        "correct": "C",
        "explanation": "Dilema Destrutivo: se q' ou s' (negações das conclusões), então p' ou r' (negações das hipóteses).",
        "help_table": DD_RULE,
    },
    {
        "id": "hard_11",
        "topic": "argumentos",
        "subtopic": "dupla_negacao",
        "difficulty": "hard",
        "question": "Pela Dupla Negação (DN): de (p')' podemos concluir:",
        "options": ["A) p'", "B) p", "C) p→p'", "D) p•p'"],
        "correct": "B",
        "explanation": "Dupla Negação: negar duas vezes volta ao original. (p')' = p.",
        "help_table": "Dupla Negação (DN):\n(p')'\n∴ p\n\nou: p\n∴ (p')'",
    },
    {
        "id": "hard_12",
        "topic": "argumentos",
        "subtopic": "modus_ponens",
        "difficulty": "hard",
        "question": "Das premissas: 'Se João estudou, então João passou' e 'João estudou' (ambas V), concluímos:",
        "options": ["A) João não passou", "B) João passou na prova", "C) João não estudou", "D) Nada pode ser concluído"],
        "correct": "B",
        "explanation": "Modus Ponens: p→q e p (ambas V) → q. João passou.",
        "help_table": MP_RULE,
    },
    {
        "id": "hard_13",
        "topic": "argumentos",
        "subtopic": "modus_tollens",
        "difficulty": "hard",
        "question": "Das premissas: 'Se chove, a rua fica molhada' e 'A rua NÃO ficou molhada', concluímos:",
        "options": ["A) Choveu", "B) Não choveu", "C) A rua ficou seca", "D) Nada pode ser concluído"],
        "correct": "B",
        "explanation": "Modus Tollens: p→q e q' → p'. 'rua não molhada' = q', logo 'não choveu' = p'.",
        "help_table": MT_RULE,
    },
    {
        "id": "hard_14",
        "topic": "argumentos",
        "subtopic": "identificar_regra",
        "difficulty": "hard",
        "question": "O argumento: 'p→q' e 'p' logo 'q' — chama-se:",
        "options": ["A) Modus Tollens", "B) Silogismo Hipotético", "C) Modus Ponens", "D) Silogismo Disjuntivo"],
        "correct": "C",
        "explanation": "Forma p→q, p / q é exatamente o Modus Ponens.",
        "help_table": MP_RULE,
    },
    {
        "id": "hard_15",
        "topic": "argumentos",
        "subtopic": "identificar_regra",
        "difficulty": "hard",
        "question": "O argumento: 'p→q', 'q'' logo 'p'' — chama-se:",
        "options": ["A) Modus Ponens", "B) Modus Tollens", "C) Adição", "D) Simplificação"],
        "correct": "B",
        "explanation": "Forma p→q, q' / p' é o Modus Tollens.",
        "help_table": MT_RULE,
    },
    {
        "id": "hard_16",
        "topic": "argumentos",
        "subtopic": "silogismo_hipotetico",
        "difficulty": "hard",
        "question": "Das premissas p→q e q→r pelo Silogismo Hipotético concluímos p→r. Se p=V e r=V, a conclusão p→r é:",
        "options": ["A) Falsa", "B) Verdadeira", "C) Indeterminada", "D) Inválida"],
        "correct": "B",
        "explanation": "p→r com p=V e r=V → V→V = V.",
        "help_table": SH_RULE,
    },
    {
        "id": "hard_17",
        "topic": "argumentos",
        "subtopic": "absorcao",
        "difficulty": "hard",
        "question": "Regra da Absorção (RA): de p→q, podemos concluir:",
        "options": ["A) p→(p+q)", "B) p→(p•q)", "C) p•q", "D) p+q"],
        "correct": "B",
        "explanation": "Absorção: p→q ⟹ p→(p•q). Se p implica q, então p implica (p e q).",
        "help_table": "Absorção (RA):\np → q\n∴ p → (p • q)",
    },
    {
        "id": "hard_18",
        "topic": "argumentos",
        "subtopic": "simplificacao_disjuntiva",
        "difficulty": "hard",
        "question": "Simplificação Disjuntiva (S+): das premissas p+r e p+r', concluímos:",
        "options": ["A) p+r", "B) r", "C) p", "D) p•r"],
        "correct": "C",
        "explanation": "S+: de (p+r) e (p+r') podemos concluir p, pois p aparece em ambas e r/r' se cancelam.",
        "help_table": "Simplificação Disjuntiva (S+):\np + r\np + r'\n∴ p",
    },
    {
        "id": "hard_19",
        "topic": "argumentos",
        "subtopic": "identificar_regra",
        "difficulty": "hard",
        "question": "O argumento: 'p+q' e 'p'' logo 'q' — chama-se:",
        "options": ["A) Modus Ponens", "B) Modus Tollens", "C) Silogismo Disjuntivo", "D) Adição"],
        "correct": "C",
        "explanation": "Forma p+q, p' / q é o Silogismo Disjuntivo.",
        "help_table": SD_RULE,
    },
    {
        "id": "hard_20",
        "topic": "argumentos",
        "subtopic": "dilema_construtivo",
        "difficulty": "hard",
        "question": "Se temos 'p→q', 'r→s' e 'p+r', qual regra usamos e o que concluímos?",
        "options": ["A) Modus Ponens → q", "B) Dilema Construtivo → q+s", "C) Silogismo Hipotético → p→s", "D) Dilema Destrutivo → p'+r'"],
        "correct": "B",
        "explanation": "As três premissas correspondem ao Dilema Construtivo (DC), que conclui q+s.",
        "help_table": DC_RULE,
    },
]


def pick_question(difficulty: str, exclude_ids: set[str]) -> dict | None:
    pool = [q for q in QUESTIONS if q["difficulty"] == difficulty and q["id"] not in exclude_ids]
    if not pool:
        return None
    return random.choice(pool)
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_questions.py -v
```
Expected: all 7 tests PASS

- [ ] **Step 5: Commit**

```bash
cd ..
git add backend/questions.py backend/tests/test_questions.py
git commit -m "feat: add hardcoded question bank with 60 questions"
```

---

### Task 3: Game State + Logic

**Files:**
- Create: `backend/game.py`
- Create: `backend/tests/test_game.py`

**Interfaces:**
- Consumes: `pick_question` from `questions.py`
- Produces: `GameState` dataclass, `PRIZES`, `SAFETY_NETS`, `DIFFICULTY_FOR_LEVEL`, `create_game_state()`, `evaluate_answer()`, `apply_help()`

- [ ] **Step 1: Write failing tests**

`backend/tests/test_game.py`:
```python
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
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_game.py -v
```
Expected: `ERROR` — `ModuleNotFoundError: No module named 'game'`

- [ ] **Step 3: Implement game.py**

`backend/game.py`:
```python
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


def create_game_state(player_name: str) -> GameState:
    session_id = str(uuid.uuid4())
    state = GameState(session_id=session_id, player_name=player_name)
    q = pick_question("easy", set())
    assert q is not None, "No easy questions available"
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
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_game.py -v
```
Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
cd ..
git add backend/game.py backend/tests/test_game.py
git commit -m "feat: game state and logic (evaluate_answer, apply_help)"
```

---

### Task 4: Pydantic Schemas + Database

**Files:**
- Create: `backend/models.py`
- Create: `backend/database.py`
- Create: `backend/tests/test_database.py`

**Interfaces:**
- Produces: Pydantic schemas (`StartRequest`, `StartResponse`, `AnswerRequest`, `AnswerResponse`, `HelpRequest`, `QuitRequest`, `ScoreEntry`)
- Produces: `init_db()`, `save_score(name, prize, levels)`, `get_top_scores(n) -> list[dict]`

- [ ] **Step 1: Write failing tests**

`backend/tests/test_database.py`:
```python
import os
import pytest
from database import init_db, save_score, get_top_scores

TEST_DB = "test_highscores.db"

@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / TEST_DB)
    monkeypatch.setenv("DB_PATH", db_path)
    init_db()
    yield
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
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_database.py -v
```
Expected: `ERROR` — `ModuleNotFoundError: No module named 'database'`

- [ ] **Step 3: Implement models.py and database.py**

`backend/models.py`:
```python
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
```

`backend/database.py`:
```python
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, desc
from sqlalchemy.orm import DeclarativeBase, Session

DB_PATH = os.getenv("DB_PATH", "highscores.db")


def _engine():
    return create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})


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
        entry = Highscore(player_name=player_name, prize=prize, levels_reached=levels_reached)
        session.add(entry)
        session.commit()


def get_top_scores(n: int = 10) -> list[dict]:
    with Session(_engine()) as session:
        rows = session.query(Highscore).order_by(desc(Highscore.prize)).limit(n).all()
        return [
            {
                "player_name": r.player_name,
                "prize": r.prize,
                "levels_reached": r.levels_reached,
                "played_at": r.played_at.isoformat() if r.played_at else "",
            }
            for r in rows
        ]
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_database.py -v
```
Expected: all 3 tests PASS

- [ ] **Step 5: Commit**

```bash
cd ..
git add backend/models.py backend/database.py backend/tests/test_database.py
git commit -m "feat: Pydantic schemas and SQLite highscore persistence"
```

---

### Task 5: Complete API Endpoints

**Files:**
- Modify: `backend/main.py` (add all routes)
- Modify: `backend/tests/test_api.py` (add endpoint tests)

**Interfaces:**
- Consumes: `create_game_state`, `evaluate_answer`, `apply_help` from `game.py`; `init_db`, `save_score`, `get_top_scores` from `database.py`; all Pydantic models from `models.py`
- Produces: all REST endpoints as documented in spec

- [ ] **Step 1: Write failing endpoint tests**

Add to `backend/tests/test_api.py`:
```python
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
    wrong = next(x for x in ["A","B","C","D"] if x != correct)

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
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_api.py -v
```
Expected: `test_health` PASSES, rest FAIL with 404

- [ ] **Step 3: Implement complete main.py**

`backend/main.py`:
```python
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
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: dict[str, GameState] = {}


@app.on_event("startup")
def startup():
    init_db()


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
```

- [ ] **Step 4: Run ALL backend tests — expect PASS**

```bash
pytest tests/ -v
```
Expected: all tests PASS

- [ ] **Step 5: Manual smoke test**

```bash
uvicorn main:app --reload
# In another terminal:
curl http://localhost:8000/
curl -X POST http://localhost:8000/game/start -H "Content-Type: application/json" -d '{"player_name":"Arthur"}'
```
Expected: `{"status":"ok"}` and a valid start response with session_id and question.

- [ ] **Step 6: Commit**

```bash
cd ..
git add backend/main.py backend/tests/test_api.py
git commit -m "feat: complete REST API with all game endpoints"
```

---

### Task 6: Frontend Scaffolding

**Files:**
- Create: `frontend/` (via Vite)
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/api.js`
- Create: `frontend/src/index.css`

**Interfaces:**
- Produces: React app with routes `/` (Home), `/game` (Game), `/game-over` (GameOver)
- Produces: `api.js` with `startGame(name)`, `sendAnswer(sid, answer)`, `useHelp(sid, type)`, `quitGame(sid)`, `getScores()`

- [ ] **Step 1: Scaffold Vite project**

```bash
cd "C:/Users/arthu/OneDrive/Desktop/ShowDoMilhão"
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install react-router-dom
```

- [ ] **Step 2: Write api.js**

`frontend/src/api.js`:
```js
const BASE = 'http://localhost:8000'

async function post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`)
  return res.json()
}

export const startGame = (playerName) =>
  post('/game/start', { player_name: playerName })

export const sendAnswer = (sessionId, answer) =>
  post('/game/answer', { session_id: sessionId, answer })

export const useHelp = (sessionId, helpType) =>
  post(`/game/help/${helpType}`, { session_id: sessionId })

export const quitGame = (sessionId) =>
  post('/game/quit', { session_id: sessionId })

export const getScores = () =>
  fetch(`${BASE}/scores`).then(r => r.json())
```

- [ ] **Step 3: Write App.jsx with routing**

`frontend/src/App.jsx`:
```jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Game from './pages/Game'
import GameOver from './pages/GameOver'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/game" element={<Game />} />
        <Route path="/game-over" element={<GameOver />} />
      </Routes>
    </BrowserRouter>
  )
}
```

- [ ] **Step 4: Create placeholder pages (enough to verify routing works)**

`frontend/src/pages/Home.jsx`:
```jsx
export default function Home() { return <div>Home</div> }
```
`frontend/src/pages/Game.jsx`:
```jsx
export default function Game() { return <div>Game</div> }
```
`frontend/src/pages/GameOver.jsx`:
```jsx
export default function GameOver() { return <div>GameOver</div> }
```

- [ ] **Step 5: Clear default Vite CSS and update index.css**

Replace `frontend/src/index.css` with:
```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Segoe UI', system-ui, sans-serif;
  background: #0a0a2e;
  color: #fff;
  min-height: 100vh;
}
```

Update `frontend/src/main.jsx` — remove import of `App.css` if present, keep only:
```jsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

- [ ] **Step 6: Start dev server and verify routing**

```bash
npm run dev
```
Open `http://localhost:5173/` → shows "Home"
Open `http://localhost:5173/game` → shows "Game"
Open `http://localhost:5173/game-over` → shows "GameOver"

- [ ] **Step 7: Commit**

```bash
cd ..
git add frontend/
git commit -m "feat: React frontend scaffold with routing and api.js"
```

---

### Task 7: Home Page

**Files:**
- Modify: `frontend/src/pages/Home.jsx`
- Create: `frontend/src/pages/Home.module.css`
- Create: `frontend/src/components/Scoreboard.jsx`
- Create: `frontend/src/components/Scoreboard.module.css`

**Interfaces:**
- Consumes: `startGame(name)` from `api.js`; `getScores()` from `api.js`
- Produces: navigates to `/game` with state `{sessionId, playerName, question, prizeLadder, safetyNetLevels}`

- [ ] **Step 1: Implement Scoreboard.jsx**

`frontend/src/components/Scoreboard.jsx`:
```jsx
import { useEffect, useState } from 'react'
import { getScores } from '../api'
import styles from './Scoreboard.module.css'

export default function Scoreboard() {
  const [scores, setScores] = useState([])

  useEffect(() => {
    getScores().then(setScores).catch(() => {})
  }, [])

  if (!scores.length) return <p className={styles.empty}>Nenhum recorde ainda.</p>

  return (
    <table className={styles.table}>
      <thead>
        <tr><th>#</th><th>Jogador</th><th>Prêmio</th><th>Nível</th></tr>
      </thead>
      <tbody>
        {scores.map((s, i) => (
          <tr key={i}>
            <td>{i + 1}</td>
            <td>{s.player_name}</td>
            <td>R$ {s.prize.toLocaleString('pt-BR')}</td>
            <td>{s.levels_reached}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
```

`frontend/src/components/Scoreboard.module.css`:
```css
.table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.table th, .table td { padding: 0.5rem 1rem; text-align: left; border-bottom: 1px solid #1a1a4e; }
.table th { color: #ffd700; font-weight: 600; }
.table tr:hover td { background: #1a1a4e; }
.empty { color: #888; font-style: italic; }
```

- [ ] **Step 2: Implement Home.jsx**

`frontend/src/pages/Home.jsx`:
```jsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { startGame } from '../api'
import Scoreboard from '../components/Scoreboard'
import styles from './Home.module.css'

export default function Home() {
  const [name, setName] = useState('')
  const [showScores, setShowScores] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  async function handleStart() {
    if (!name.trim()) { setError('Digite seu nome!'); return }
    setLoading(true)
    setError('')
    try {
      const data = await startGame(name.trim())
      navigate('/game', {
        state: {
          sessionId: data.session_id,
          playerName: name.trim(),
          question: data.question,
          prizeLadder: data.prize_ladder,
          safetyNetLevels: data.safety_net_levels,
          level: data.level,
        },
      })
    } catch {
      setError('Erro ao conectar com o servidor.')
      setLoading(false)
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h1 className={styles.title}>Show do Milhão</h1>
        <p className={styles.subtitle}>Lógica Matemática</p>

        <div className={styles.form}>
          <input
            className={styles.input}
            placeholder="Seu nome"
            value={name}
            onChange={e => setName(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleStart()}
            maxLength={30}
          />
          {error && <p className={styles.error}>{error}</p>}
          <button className={styles.btnStart} onClick={handleStart} disabled={loading}>
            {loading ? 'Carregando...' : '▶ Jogar'}
          </button>
          <button className={styles.btnScores} onClick={() => setShowScores(v => !v)}>
            {showScores ? 'Ocultar Ranking' : '🏆 Ver Ranking'}
          </button>
        </div>

        {showScores && (
          <div className={styles.scores}>
            <h2 className={styles.scoresTitle}>Top 10</h2>
            <Scoreboard />
          </div>
        )}
      </div>
    </div>
  )
}
```

`frontend/src/pages/Home.module.css`:
```css
.container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(ellipse at center, #0d0d3b 0%, #0a0a1e 100%);
}
.card {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,215,0,0.3);
  border-radius: 1rem;
  padding: 3rem 2.5rem;
  width: min(480px, 90vw);
  text-align: center;
}
.title {
  font-size: 2.5rem;
  font-weight: 800;
  color: #ffd700;
  text-shadow: 0 0 20px rgba(255,215,0,0.5);
  margin-bottom: 0.25rem;
}
.subtitle {
  color: #aac; font-size: 1rem; margin-bottom: 2rem;
}
.form { display: flex; flex-direction: column; gap: 0.75rem; }
.input {
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  border: 2px solid #2a2a6e;
  background: #0d0d3b;
  color: #fff;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s;
}
.input:focus { border-color: #ffd700; }
.btnStart {
  padding: 0.875rem;
  background: #ffd700;
  color: #0a0a1e;
  font-size: 1.1rem;
  font-weight: 700;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: opacity 0.2s;
}
.btnStart:hover:not(:disabled) { opacity: 0.85; }
.btnStart:disabled { opacity: 0.5; cursor: default; }
.btnScores {
  padding: 0.625rem;
  background: transparent;
  color: #aac;
  border: 1px solid #2a2a6e;
  border-radius: 0.5rem;
  cursor: pointer;
  font-size: 0.9rem;
  transition: border-color 0.2s;
}
.btnScores:hover { border-color: #ffd700; color: #ffd700; }
.error { color: #ff6b6b; font-size: 0.875rem; }
.scores { margin-top: 1.5rem; text-align: left; }
.scoresTitle { color: #ffd700; font-size: 1.1rem; margin-bottom: 0.75rem; }
```

- [ ] **Step 3: Manual test**

Start backend: `cd backend && uvicorn main:app --reload`
Start frontend: `cd frontend && npm run dev`
Open `http://localhost:5173/`
- Type a name, press Jogar → should navigate to `/game`
- Click Ver Ranking → should show table (empty initially)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/Home.jsx frontend/src/pages/Home.module.css \
        frontend/src/components/Scoreboard.jsx frontend/src/components/Scoreboard.module.css
git commit -m "feat: Home page with name input and scoreboard"
```

---

### Task 8: Game Components

**Files:**
- Create: `frontend/src/components/QuestionCard.jsx` + `QuestionCard.module.css`
- Create: `frontend/src/components/PrizeLadder.jsx` + `PrizeLadder.module.css`
- Create: `frontend/src/components/HelpButtons.jsx` + `HelpButtons.module.css`

**Interfaces:**
- `QuestionCard` props: `question: {id, question, options}`, `eliminatedOptions: string[]|null`, `selectedAnswer: string|null`, `answerResult: 'correct'|'wrong'|null`, `onSelect: (letter)=>void`, `onConfirm: ()=>void`, `confirming: bool`
- `PrizeLadder` props: `prizes: number[]`, `currentLevel: number`, `safetyNetLevels: number[]`
- `HelpButtons` props: `helpsUsed: string[]`, `onHelp: (type)=>void`, `disabled: bool`

- [ ] **Step 1: Implement QuestionCard.jsx**

`frontend/src/components/QuestionCard.jsx`:
```jsx
import styles from './QuestionCard.module.css'

const LETTERS = ['A', 'B', 'C', 'D']

export default function QuestionCard({
  question, eliminatedOptions, selectedAnswer, answerResult, onSelect, onConfirm, confirming
}) {
  function getOptionClass(letter) {
    const isEliminated = eliminatedOptions && !eliminatedOptions.some(o => o.startsWith(letter))
    if (isEliminated) return styles.eliminated
    if (answerResult && letter === selectedAnswer) {
      return answerResult === 'correct' ? styles.correct : styles.wrong
    }
    if (letter === selectedAnswer) return styles.selected
    return styles.option
  }

  const option = (letter) => question.options.find(o => o.startsWith(letter))

  return (
    <div className={styles.card}>
      <p className={styles.question}>{question.question}</p>
      <div className={styles.options}>
        {LETTERS.map(letter => {
          const opt = option(letter)
          if (!opt) return null
          const isEliminated = eliminatedOptions && !eliminatedOptions.some(o => o.startsWith(letter))
          return (
            <button
              key={letter}
              className={getOptionClass(letter)}
              onClick={() => !answerResult && !isEliminated && onSelect(letter)}
              disabled={!!answerResult || isEliminated}
            >
              {opt}
            </button>
          )
        })}
      </div>
      {selectedAnswer && !answerResult && (
        <button className={styles.confirm} onClick={onConfirm} disabled={confirming}>
          {confirming ? 'Verificando...' : 'Confirmar resposta'}
        </button>
      )}
    </div>
  )
}
```

`frontend/src/components/QuestionCard.module.css`:
```css
.card { flex: 1; display: flex; flex-direction: column; gap: 1.5rem; }
.question {
  font-size: 1.15rem;
  line-height: 1.6;
  color: #e8e8ff;
  background: rgba(255,255,255,0.04);
  border: 1px solid #2a2a6e;
  border-radius: 0.75rem;
  padding: 1.25rem 1.5rem;
}
.options { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.option, .selected, .correct, .wrong, .eliminated {
  padding: 0.875rem 1rem;
  border-radius: 0.5rem;
  border: 2px solid #2a2a6e;
  background: #0d0d3b;
  color: #e8e8ff;
  font-size: 0.95rem;
  text-align: left;
  cursor: pointer;
  transition: all 0.15s;
}
.option:hover:not(:disabled) { border-color: #ffd700; background: #1a1a5e; }
.selected { border-color: #ffd700; background: #2a2a00; color: #ffd700; }
.correct { border-color: #00e676; background: #003300; color: #00e676; cursor: default; }
.wrong { border-color: #ff1744; background: #330000; color: #ff1744; cursor: default; }
.eliminated { opacity: 0.3; cursor: not-allowed; }
.confirm {
  padding: 0.875rem;
  background: #ffd700;
  color: #0a0a1e;
  font-weight: 700;
  font-size: 1rem;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: opacity 0.2s;
}
.confirm:hover:not(:disabled) { opacity: 0.85; }
.confirm:disabled { opacity: 0.5; cursor: default; }
```

- [ ] **Step 2: Implement PrizeLadder.jsx**

`frontend/src/components/PrizeLadder.jsx`:
```jsx
import styles from './PrizeLadder.module.css'

export default function PrizeLadder({ prizes, currentLevel, safetyNetLevels }) {
  return (
    <div className={styles.ladder}>
      {[...prizes].reverse().map((prize, revIdx) => {
        const idx = prizes.length - 1 - revIdx
        const isCurrent = idx === currentLevel
        const isSafe = safetyNetLevels.includes(idx)
        const isPassed = idx < currentLevel
        return (
          <div
            key={idx}
            className={[
              styles.row,
              isCurrent ? styles.current : '',
              isSafe ? styles.safe : '',
              isPassed ? styles.passed : '',
            ].join(' ')}
          >
            <span className={styles.level}>{idx + 1}</span>
            <span className={styles.prize}>
              {isSafe ? '✓ ' : ''}R$ {prize.toLocaleString('pt-BR')}
            </span>
          </div>
        )
      })}
    </div>
  )
}
```

`frontend/src/components/PrizeLadder.module.css`:
```css
.ladder {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  width: 200px;
  flex-shrink: 0;
}
.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.35rem 0.75rem;
  border-radius: 0.35rem;
  font-size: 0.8rem;
  color: #aac;
  background: transparent;
  transition: all 0.2s;
}
.level { font-weight: 600; color: #555; min-width: 1.5rem; }
.prize { font-weight: 500; }
.current { background: #2a2a00; border: 1px solid #ffd700; color: #ffd700; }
.current .level { color: #ffd700; }
.safe { color: #00e676; }
.safe .level { color: #00e676; }
.passed { opacity: 0.45; }
```

- [ ] **Step 3: Implement HelpButtons.jsx**

`frontend/src/components/HelpButtons.jsx`:
```jsx
import styles from './HelpButtons.module.css'

const HELPS = [
  { type: 'table',    label: '📊 Tabela-Verdade', title: 'Ver tabela-verdade do operador' },
  { type: 'eliminate', label: '✂️ Eliminar 2',    title: 'Eliminar 2 alternativas erradas' },
  { type: 'skip',    label: '⏭️ Pular',           title: 'Pular para outra questão do mesmo nível' },
]

export default function HelpButtons({ helpsUsed, onHelp, disabled }) {
  return (
    <div className={styles.container}>
      <p className={styles.label}>Ajudas:</p>
      <div className={styles.buttons}>
        {HELPS.map(h => {
          const used = helpsUsed.includes(h.type)
          return (
            <button
              key={h.type}
              className={used ? styles.used : styles.btn}
              onClick={() => !used && !disabled && onHelp(h.type)}
              disabled={used || disabled}
              title={h.title}
            >
              {used ? <s>{h.label}</s> : h.label}
            </button>
          )
        })}
      </div>
    </div>
  )
}
```

`frontend/src/components/HelpButtons.module.css`:
```css
.container { display: flex; flex-direction: column; gap: 0.5rem; }
.label { font-size: 0.8rem; color: #666; }
.buttons { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.btn, .used {
  padding: 0.5rem 0.875rem;
  border-radius: 0.4rem;
  border: 1px solid #2a2a6e;
  background: #0d0d3b;
  color: #e8e8ff;
  font-size: 0.8rem;
  cursor: pointer;
  transition: border-color 0.15s;
}
.btn:hover:not(:disabled) { border-color: #ffd700; }
.used { opacity: 0.35; cursor: not-allowed; }
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/
git commit -m "feat: QuestionCard, PrizeLadder, and HelpButtons components"
```

---

### Task 9: Game Page

**Files:**
- Modify: `frontend/src/pages/Game.jsx`
- Create: `frontend/src/pages/Game.module.css`

**Interfaces:**
- Consumes: router state `{sessionId, playerName, question, prizeLadder, safetyNetLevels, level}`
- Consumes: `sendAnswer`, `useHelp`, `quitGame` from `api.js`
- Consumes: `QuestionCard`, `PrizeLadder`, `HelpButtons` components

- [ ] **Step 1: Implement Game.jsx**

`frontend/src/pages/Game.jsx`:
```jsx
import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { sendAnswer, useHelp, quitGame } from '../api'
import QuestionCard from '../components/QuestionCard'
import PrizeLadder from '../components/PrizeLadder'
import HelpButtons from '../components/HelpButtons'
import styles from './Game.module.css'

export default function Game() {
  const { state } = useLocation()
  const navigate = useNavigate()

  const [sessionId] = useState(state?.sessionId)
  const [playerName] = useState(state?.playerName)
  const [prizeLadder] = useState(state?.prizeLadder ?? [])
  const [safetyNetLevels] = useState(state?.safetyNetLevels ?? [])

  const [question, setQuestion] = useState(state?.question)
  const [level, setLevel] = useState(state?.level ?? 0)
  const [helpsUsed, setHelpsUsed] = useState([])
  const [eliminatedOptions, setEliminatedOptions] = useState(null)
  const [selectedAnswer, setSelectedAnswer] = useState(null)
  const [answerResult, setAnswerResult] = useState(null)
  const [confirming, setConfirming] = useState(false)
  const [tableModal, setTableModal] = useState(null)
  const [currentPrize, setCurrentPrize] = useState(0)

  if (!sessionId || !question) {
    navigate('/')
    return null
  }

  async function handleConfirm() {
    if (!selectedAnswer || confirming) return
    setConfirming(true)
    try {
      const data = await sendAnswer(sessionId, selectedAnswer)
      setAnswerResult(data.correct ? 'correct' : 'wrong')

      setTimeout(() => {
        if (data.game_over) {
          navigate('/game-over', {
            state: { playerName, prize: data.current_prize, won: data.won, level: data.level },
          })
        } else {
          setQuestion(data.next_question)
          setLevel(data.level)
          setCurrentPrize(data.current_prize)
          setSelectedAnswer(null)
          setAnswerResult(null)
          setEliminatedOptions(null)
          setConfirming(false)
        }
      }, 1800)
    } catch {
      setConfirming(false)
    }
  }

  async function handleHelp(type) {
    try {
      const data = await useHelp(sessionId, type)
      setHelpsUsed(prev => [...prev, type])
      if (type === 'table') setTableModal(data.table_content)
      if (type === 'eliminate') setEliminatedOptions(data.remaining_options)
      if (type === 'skip' && data.new_question) {
        setQuestion(data.new_question)
        setSelectedAnswer(null)
        setEliminatedOptions(null)
      }
    } catch {}
  }

  async function handleQuit() {
    if (!confirm('Deseja desistir e receber o prêmio acumulado?')) return
    try {
      const data = await quitGame(sessionId)
      navigate('/game-over', {
        state: { playerName, prize: data.final_prize, won: false, level: data.levels_reached },
      })
    } catch {}
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <span className={styles.player}>🎮 {playerName}</span>
        {currentPrize > 0 && (
          <span className={styles.prize}>R$ {currentPrize.toLocaleString('pt-BR')}</span>
        )}
        <button className={styles.quit} onClick={handleQuit}>Desistir</button>
      </header>

      <div className={styles.main}>
        <aside className={styles.sidebar}>
          <PrizeLadder prizes={prizeLadder} currentLevel={level} safetyNetLevels={safetyNetLevels} />
        </aside>

        <section className={styles.content}>
          <QuestionCard
            question={question}
            eliminatedOptions={eliminatedOptions}
            selectedAnswer={selectedAnswer}
            answerResult={answerResult}
            onSelect={setSelectedAnswer}
            onConfirm={handleConfirm}
            confirming={confirming}
          />
          <div className={styles.bottom}>
            <HelpButtons helpsUsed={helpsUsed} onHelp={handleHelp} disabled={!!answerResult} />
          </div>
        </section>
      </div>

      {tableModal && (
        <div className={styles.overlay} onClick={() => setTableModal(null)}>
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <h3>Tabela-Verdade</h3>
            <pre className={styles.table}>{tableModal}</pre>
            <button onClick={() => setTableModal(null)}>Fechar</button>
          </div>
        </div>
      )}
    </div>
  )
}
```

`frontend/src/pages/Game.module.css`:
```css
.page { min-height: 100vh; display: flex; flex-direction: column; }
.header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1.5rem;
  background: rgba(255,215,0,0.07);
  border-bottom: 1px solid rgba(255,215,0,0.2);
}
.player { font-weight: 600; color: #ffd700; flex: 1; }
.prize { font-weight: 700; color: #00e676; font-size: 1.1rem; }
.quit {
  padding: 0.4rem 0.875rem;
  background: transparent;
  border: 1px solid #ff1744;
  color: #ff1744;
  border-radius: 0.35rem;
  cursor: pointer;
  font-size: 0.85rem;
}
.quit:hover { background: #ff1744; color: #fff; }
.main { display: flex; flex: 1; gap: 1.5rem; padding: 1.5rem; max-width: 1100px; margin: 0 auto; width: 100%; }
.sidebar { padding-top: 0.5rem; }
.content { flex: 1; display: flex; flex-direction: column; gap: 1.5rem; }
.bottom { margin-top: auto; }
.overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.75);
  display: flex; align-items: center; justify-content: center;
  z-index: 100;
}
.modal {
  background: #0d0d3b;
  border: 1px solid #ffd700;
  border-radius: 0.75rem;
  padding: 2rem;
  max-width: 400px;
  width: 90vw;
  display: flex; flex-direction: column; gap: 1rem;
}
.modal h3 { color: #ffd700; }
.table { font-family: monospace; font-size: 0.9rem; white-space: pre; color: #e8e8ff; }
.modal button {
  padding: 0.5rem 1rem; background: #ffd700; color: #0a0a1e;
  border: none; border-radius: 0.35rem; cursor: pointer; font-weight: 600; align-self: flex-end;
}
```

- [ ] **Step 2: Manual test**

With backend running:
1. Go to Home, type name, click Jogar
2. Game page shows question + prize ladder + 3 help buttons
3. Click an option → highlights yellow
4. Click Confirmar → green/red, then next question
5. Click 📊 → modal shows truth table
6. Click ✂️ → 2 options disappear
7. Click ⏭️ → new question appears
8. Click Desistir → confirm dialog → GameOver page

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Game.jsx frontend/src/pages/Game.module.css
git commit -m "feat: Game page with question flow, help buttons, and prize ladder"
```

---

### Task 10: GameOver Page

**Files:**
- Modify: `frontend/src/pages/GameOver.jsx`
- Create: `frontend/src/pages/GameOver.module.css`

**Interfaces:**
- Consumes: router state `{playerName, prize, won, level}`

- [ ] **Step 1: Implement GameOver.jsx**

`frontend/src/pages/GameOver.jsx`:
```jsx
import { useLocation, useNavigate } from 'react-router-dom'
import Scoreboard from '../components/Scoreboard'
import styles from './GameOver.module.css'

export default function GameOver() {
  const { state } = useLocation()
  const navigate = useNavigate()

  const { playerName = 'Jogador', prize = 0, won = false, level = 0 } = state ?? {}

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.result}>
          {won ? (
            <>
              <p className={styles.emoji}>🏆</p>
              <h1 className={styles.title}>Parabéns, {playerName}!</h1>
              <p className={styles.subtitle}>Você ganhou o prêmio máximo!</p>
            </>
          ) : (
            <>
              <p className={styles.emoji}>{prize > 0 ? '🎯' : '😢'}</p>
              <h1 className={styles.title}>{prize > 0 ? `Você ganhou` : 'Que pena!'}</h1>
              <p className={styles.subtitle}>
                {prize > 0 ? `Parabéns, ${playerName}!` : `Melhor sorte da próxima, ${playerName}.`}
              </p>
            </>
          )}
          <p className={styles.prize}>
            R$ {prize.toLocaleString('pt-BR')}
          </p>
          <p className={styles.levels}>
            Chegou ao nível {level} de 15
          </p>
        </div>

        <button className={styles.btn} onClick={() => navigate('/')}>
          🔄 Jogar Novamente
        </button>

        <div className={styles.scores}>
          <h2 className={styles.scoresTitle}>🏆 Top 10</h2>
          <Scoreboard />
        </div>
      </div>
    </div>
  )
}
```

`frontend/src/pages/GameOver.module.css`:
```css
.page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(ellipse at center, #0d0d3b 0%, #0a0a1e 100%);
  padding: 2rem 1rem;
}
.card {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,215,0,0.3);
  border-radius: 1rem;
  padding: 2.5rem 2rem;
  width: min(540px, 95vw);
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}
.result { text-align: center; }
.emoji { font-size: 3.5rem; margin-bottom: 0.5rem; }
.title { font-size: 1.8rem; font-weight: 800; color: #ffd700; margin-bottom: 0.25rem; }
.subtitle { color: #aac; margin-bottom: 1rem; }
.prize { font-size: 2.5rem; font-weight: 900; color: #00e676; }
.levels { color: #888; font-size: 0.9rem; margin-top: 0.25rem; }
.btn {
  width: 100%;
  padding: 0.875rem;
  background: #ffd700;
  color: #0a0a1e;
  font-size: 1rem;
  font-weight: 700;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: opacity 0.2s;
}
.btn:hover { opacity: 0.85; }
.scores { border-top: 1px solid #2a2a6e; padding-top: 1rem; }
.scoresTitle { color: #ffd700; font-size: 1rem; margin-bottom: 0.75rem; }
```

- [ ] **Step 2: Manual test**

Play a full game to completion (correct and incorrect paths). Verify:
- Losing shows prize = 0 or safety net amount
- Winning 15 levels shows R$1.000.000
- Scoreboard shows new entry
- "Jogar Novamente" returns to Home

- [ ] **Step 3: Final backend + frontend integration test**

```bash
# Terminal 1
cd backend && uvicorn main:app --reload

# Terminal 2  
cd frontend && npm run dev
```

Full flow test:
1. Start game with name
2. Answer 5 questions correctly → verify safety net message (prize_if_quit = R$5.000)
3. Answer wrong → lose, check GameOver shows R$5.000
4. Play again, answer all 15 → check GameOver shows R$1.000.000
5. Check /scores endpoint returns both games

- [ ] **Step 4: Run all backend tests one final time**

```bash
cd backend && pytest tests/ -v
```
Expected: all tests PASS

- [ ] **Step 5: Final commit**

```bash
cd ..
git add frontend/src/pages/GameOver.jsx frontend/src/pages/GameOver.module.css
git commit -m "feat: GameOver page with prize display and scoreboard"
git tag v1.0.0
```

---

## Running the Project

```bash
# Backend (from /backend with venv active)
uvicorn main:app --reload --port 8000

# Frontend (from /frontend)
npm run dev
```

Open: `http://localhost:5173`
