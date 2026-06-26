# Show do Milhão — Lógica Matemática: Design Spec

**Data:** 2026-06-26  
**Stack:** FastAPI (Python 3.11+) + React 18 + Vite  
**Conteúdo:** Proposições e Argumentos Válidos (UFN — Prof. Leandro Fontoura)

---

## 1. Visão Geral

Jogo estilo "Show do Milhão" com 15 níveis de prêmio (R$1.000 a R$1.000.000). Questões de múltipla escolha (4 alternativas) sobre lógica matemática — proposições, operadores lógicos, tabelas-verdade e argumentos válidos. Banco de ~60 questões hardcoded. Estado do jogo gerenciado no backend (FastAPI). Frontend React consome API REST.

---

## 2. Arquitetura

```
ShowDoMilhão/
├── backend/
│   ├── main.py          # FastAPI app + routers
│   ├── game.py          # lógica de sessão, validação, ajudas
│   ├── questions.py     # banco de questões hardcoded
│   ├── models.py        # Pydantic schemas + SQLAlchemy models
│   └── database.py      # SQLite via SQLAlchemy (highscores)
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── Home.jsx
    │   │   ├── Game.jsx
    │   │   └── GameOver.jsx
    │   ├── components/
    │   │   ├── QuestionCard.jsx
    │   │   ├── PrizeLadder.jsx
    │   │   ├── HelpButtons.jsx
    │   │   └── Scoreboard.jsx
    │   └── api.js        # fetch wrapper
    └── vite.config.js
```

**Comunicação:** React → REST API (JSON) → FastAPI  
**Sessões:** dicionário em memória `dict[uuid → GameState]` (sem persistência de sessão)  
**Highscores:** SQLite via SQLAlchemy

---

## 3. Banco de Questões

### Estrutura
```python
{
  "id": str,              # ex: "prop_01"
  "topic": str,           # "proposicoes" | "argumentos"
  "subtopic": str,        # ex: "condicional", "modus_ponens"
  "difficulty": str,      # "easy" | "medium" | "hard"
  "question": str,        # enunciado
  "options": list[str],   # ["A) ...", "B) ...", "C) ...", "D) ..."]
  "correct": str,         # "A" | "B" | "C" | "D"
  "explanation": str,     # explicação da resposta correta
  "help_table": str       # tabela-verdade do operador (para ajuda)
}
```

### Distribuição (~60 questões)
| Dificuldade | Níveis | Qtd | Tópicos |
|-------------|--------|-----|---------|
| easy        | 1–5    | ~20 | Identificar proposição, valor lógico, negação simples |
| medium      | 6–10   | ~20 | Conjunção, disjunção, condicional, bicondicional, tabela-verdade composta |
| hard        | 11–15  | ~20 | Argumentos válidos, MP, MT, SH, DC, DD, regras de inferência |

Questões sorteadas aleatoriamente do pool de dificuldade correspondente ao nível. `used_questions` evita repetição na mesma sessão.

---

## 4. Escada de Prêmios

```python
PRIZES = [
    1_000, 2_000, 3_000, 4_000, 5_000,
    10_000, 20_000, 30_000, 40_000, 50_000,
    100_000, 200_000, 300_000, 500_000, 1_000_000
]
SAFETY_NETS = {4: 5_000, 9: 50_000}  # índices 0-based (níveis 5 e 10)
```

**Regras de encerramento:**
- Acertar nível 15 → ganhou R$1.000.000
- Errar antes do safety net 1 (nível 5) → R$0
- Errar entre safety nets → recebe o safety net anterior
- Desistir → recebe `prize_if_quit` (último safety net alcançado)

---

## 5. Estado de Sessão (Backend)

```python
@dataclass
class GameState:
    session_id: str
    player_name: str
    current_level: int           # 0–14
    prize_if_quit: int           # último safety net ou 0
    current_question: dict
    used_questions: set[str]
    helps_used: set[str]         # "table" | "eliminate" | "skip"
    active_eliminates: list[str] | None  # alternativas após eliminar 2
```

---

## 6. API Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/game/start` | Inicia sessão, retorna primeira questão |
| POST | `/game/answer` | Valida resposta, retorna próxima questão ou game_over |
| POST | `/game/help/{type}` | Usa ajuda: `table`, `eliminate`, `skip` |
| POST | `/game/quit` | Desiste, retorna prêmio acumulado |
| GET  | `/scores` | Top 10 highscores |

### Payloads principais

**POST /game/start**
```json
Request:  { "player_name": "Arthur" }
Response: {
  "session_id": "uuid",
  "question": { "id", "question", "options" },
  "level": 0,
  "prize_ladder": [1000, 2000, ...]
}
```

**POST /game/answer**
```json
Request:  { "session_id": "uuid", "answer": "A" }
Response: {
  "correct": true,
  "correct_answer": "A",
  "explanation": "...",
  "game_over": false,
  "current_prize": 2000,
  "next_question": { "id", "question", "options" },
  "level": 1
}
```

**POST /game/help/{type}**
```json
// type=table
Response: { "table": "p | q | p→q\nV|V|V\n..." }

// type=eliminate
Response: { "remaining_options": ["A) ...", "C) ..."] }

// type=skip
Response: { "new_question": { "id", "question", "options" } }
```

**POST /game/quit**
```json
Request:  { "session_id": "uuid" }
Response: { "final_prize": 5000, "game_over": true }
```

---

## 7. Ajudas Temáticas (1x cada por sessão)

| Ajuda | Ícone | Comportamento |
|-------|-------|---------------|
| Ver tabela-verdade | 📊 | Exibe `help_table` do operador da questão atual em modal |
| Eliminar 2 alternativas | ✂️ | Backend remove 2 erradas, retorna as 2 restantes |
| Pular questão | ⏭️ | Backend sorteia nova questão do mesmo nível/dificuldade |

---

## 8. Frontend — Componentes

### Layout da tela Game
```
┌─────────────────────────────────────────┐
│  PrizeLadder       QuestionCard          │
│  R$1.000.000       Enunciado da questão  │
│  R$500.000         [A]  [B]              │
│  ...               [C]  [D]             │
│  ► R$10.000                             │
│  ✓ R$5.000         HelpButtons          │
│  ...               [📊]  [✂️]  [⏭️]    │
│                                         │
│              [DESISTIR]                 │
└─────────────────────────────────────────┘
```

### Fluxo de resposta
1. Clica alternativa → botão fica amarelo
2. Clica confirmar → POST /game/answer
3. Animação 1s: verde (certo) ou vermelho (errado)
4. Após 1.5s → próxima questão ou navega para GameOver

### Tech
- React 18 + Vite
- CSS Modules (tema azul escuro estilo TV)
- Fetch nativo (sem axios)
- React Router para navegação entre páginas

---

## 9. Highscores

Tabela SQLite `highscores`:
```sql
CREATE TABLE highscores (
  id INTEGER PRIMARY KEY,
  player_name TEXT NOT NULL,
  prize INTEGER NOT NULL,
  levels_reached INTEGER NOT NULL,
  played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Salvo ao final de cada partida (game_over ou quit). GET /scores retorna top 10 por prize DESC.

---

## 10. Fora do Escopo

- Autenticação/login
- Multiplayer
- Geração de questões por IA
- Deploy em produção (roda local: `uvicorn` + `vite dev`)
