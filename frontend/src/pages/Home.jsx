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
        <p className={styles.subtitle}>Lógica Computacional</p>

        <div className={styles.form}>
          <div className={styles.inputWrap}>
            <label className={styles.label} htmlFor="player-name">Nome do Jogador</label>
            <input
              id="player-name"
              className={styles.input}
              placeholder="Seu nome"
              value={name}
              onChange={e => setName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleStart()}
              maxLength={30}
              autoComplete="off"
            />
          </div>
          {error && <p className={styles.error}>{error}</p>}
          <button className={styles.btnStart} onClick={handleStart} disabled={loading || !name.trim()}>
            {loading ? 'Carregando...' : 'Jogar'}
          </button>
          <button className={styles.btnScores} onClick={() => setShowScores(v => !v)}>
            {showScores ? 'Ocultar Ranking' : 'Ver Ranking'}
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
