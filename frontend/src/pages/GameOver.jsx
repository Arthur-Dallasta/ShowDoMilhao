import { useLocation, useNavigate } from 'react-router-dom'
import Scoreboard from '../components/Scoreboard'
import styles from './GameOver.module.css'

export default function GameOver() {
  const { state } = useLocation()
  const navigate = useNavigate()

  if (!state) {
    navigate('/')
    return null
  }

  const { playerName = 'Jogador', finalPrize: prize = 0, won = false, levelsReached: level = 0 } = state

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
