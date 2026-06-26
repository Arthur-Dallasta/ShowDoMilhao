import styles from './HelpButtons.module.css'

const HELPS = [
  { type: 'table',    label: '📊 Tabela-Verdade', title: 'Ver tabela-verdade do operador' },
  { type: 'eliminate', label: '✂️ Eliminar 2',    title: 'Eliminar 2 alternativas erradas' },
  { type: 'skip',     label: '⏭️ Pular',          title: 'Pular para outra questão do mesmo nível' },
]

export default function HelpButtons({ helpsUsed, onHelp, disabled }) {
  return (
    <div className={styles.container}>
      <p className={styles.label}>Ajudas:</p>
      <div className={styles.buttons}>
        {HELPS.map(h => {
          const used = helpsUsed instanceof Set
            ? helpsUsed.has(h.type)
            : Array.isArray(helpsUsed) && helpsUsed.includes(h.type)
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
