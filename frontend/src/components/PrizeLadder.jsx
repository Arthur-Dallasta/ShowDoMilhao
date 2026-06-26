import styles from './PrizeLadder.module.css'

export default function PrizeLadder({ prizeLadder, currentLevel, safetyNetLevels }) {
  return (
    <div className={styles.ladder}>
      {[...prizeLadder].reverse().map((prize, revIdx) => {
        const idx = prizeLadder.length - 1 - revIdx
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
