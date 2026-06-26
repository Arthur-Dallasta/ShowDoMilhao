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
