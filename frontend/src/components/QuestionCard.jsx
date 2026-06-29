import styles from './QuestionCard.module.css'

const LETTERS = ['A', 'B', 'C', 'D']

export default function QuestionCard({
  question, selected, onSelect, feedback, activeEliminates, disabled
}) {
  function getOptionClass(letter) {
    const isEliminated = activeEliminates && !activeEliminates.some(o => o.startsWith(letter))
    if (isEliminated) return styles.eliminated
    if (feedback && letter === selected) {
      return feedback === 'correct' ? styles.correct : styles.wrong
    }
    if (letter === selected) return styles.selected
    return styles.option
  }

  const getOption = (letter) => question.options.find(o => o.startsWith(letter))

  return (
    <div className={styles.card}>
      <p className={styles.question}>{question.question}</p>
      <div className={styles.options}>
        {LETTERS.map(letter => {
          const opt = getOption(letter)
          if (!opt) return null
          const isEliminated = activeEliminates && !activeEliminates.some(o => o.startsWith(letter))
          return (
            <button
              key={letter}
              className={getOptionClass(letter)}
              onClick={() => !feedback && !isEliminated && !disabled && onSelect(letter)}
              disabled={!!feedback || isEliminated || disabled}
            >
              <span className={styles.badge}>{letter}</span>
              <span className={styles.optText}>{opt.replace(/^[A-D][).]\s*/, '')}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
