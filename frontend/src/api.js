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
