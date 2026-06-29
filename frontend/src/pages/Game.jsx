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
  const [helpsUsed, setHelpsUsed] = useState(new Set())
  const [activeEliminates, setActiveEliminates] = useState(null)
  const [selected, setSelected] = useState(null)
  const [feedback, setFeedback] = useState(null)
  const [confirming, setConfirming] = useState(false)
  const [disabled, setDisabled] = useState(false)
  const [tableModal, setTableModal] = useState(null)
  const [currentPrize, setCurrentPrize] = useState(0)
  const [correctReveal, setCorrectReveal] = useState(null)
  const [quitModal, setQuitModal] = useState(false)

  if (!sessionId || !question) {
    navigate('/')
    return null
  }

  async function handleConfirm() {
    if (!selected || confirming) return
    setConfirming(true)
    setDisabled(true)
    try {
      const data = await sendAnswer(sessionId, selected)
      setFeedback(data.correct ? 'correct' : 'wrong')
      if (!data.correct) {
        const correctOption = question.options.find(o => o.startsWith(data.correct_answer))
        setCorrectReveal({ letter: data.correct_answer, option: correctOption, explanation: data.explanation })
      }

      setTimeout(() => {
        setCorrectReveal(null)
        if (data.game_over) {
          navigate('/gameover', {
            state: {
              playerName,
              finalPrize: data.current_prize,
              levelsReached: data.level,
              won: data.won,
            },
          })
        } else {
          setQuestion(data.next_question)
          setLevel(data.level)
          setCurrentPrize(data.current_prize)
          setSelected(null)
          setFeedback(null)
          setActiveEliminates(null)
          setConfirming(false)
          setDisabled(false)
        }
      }, 1500)
    } catch {
      setConfirming(false)
      setDisabled(false)
    }
  }

  async function handleHelp(type) {
    try {
      const data = await useHelp(sessionId, type)
      setHelpsUsed(prev => new Set([...prev, type]))
      if (type === 'table') {
        setTableModal(data.table_content)
      }
      if (type === 'eliminate') {
        setActiveEliminates(data.remaining_options)
        if (selected && !data.remaining_options.some(o => o.startsWith(selected))) {
          setSelected(null)
        }
      }
      if (type === 'skip' && data.new_question) {
        setQuestion(data.new_question)
        setSelected(null)
        setActiveEliminates(null)
      }
    } catch {}
  }

  async function handleQuitConfirm() {
    setQuitModal(false)
    try {
      const data = await quitGame(sessionId)
      navigate('/gameover', {
        state: {
          playerName,
          finalPrize: data.final_prize,
          levelsReached: data.levels_reached,
          won: false,
        },
      })
    } catch {}
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <span className={styles.player}>{playerName}</span>
        {currentPrize > 0 && (
          <span className={styles.prize}>R$ {currentPrize.toLocaleString('pt-BR')}</span>
        )}
        <button className={styles.quit} onClick={() => setQuitModal(true)}>Desistir</button>
      </header>

      <div className={styles.main}>
        <aside className={styles.sidebar}>
          <PrizeLadder
            prizeLadder={prizeLadder}
            currentLevel={level}
            safetyNetLevels={safetyNetLevels}
          />
        </aside>

        <section className={styles.content}>
          <QuestionCard
            question={question}
            selected={selected}
            onSelect={setSelected}
            feedback={feedback}
            activeEliminates={activeEliminates}
            disabled={disabled}
          />
          <div className={styles.bottom}>
            <HelpButtons
              helpsUsed={helpsUsed}
              onHelp={handleHelp}
              disabled={!!feedback}
            />
            <button
              className={styles.confirm}
              onClick={handleConfirm}
              disabled={!selected || confirming || !!feedback}
            >
              {confirming ? 'Confirmando...' : 'Confirmar'}
            </button>
          </div>
        </section>
      </div>

      {correctReveal && (
        <div className={styles.overlay}>
          <div className={styles.modal}>
            <h3>❌ Resposta errada</h3>
            <p><strong>Resposta correta:</strong> {correctReveal.option}</p>
            <p className={styles.explanation}>{correctReveal.explanation}</p>
          </div>
        </div>
      )}

      {tableModal && (
        <div className={styles.overlay} onClick={() => setTableModal(null)}>
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <h3>Tabela-Verdade</h3>
            <pre className={styles.table}>{tableModal}</pre>
            <button onClick={() => setTableModal(null)}>Fechar</button>
          </div>
        </div>
      )}

      {quitModal && (
        <div className={styles.overlay} onClick={() => setQuitModal(false)}>
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <h3>Desistir da partida?</h3>
            <p>Você receberá o prêmio acumulado até agora.</p>
            {currentPrize > 0 && (
              <p className={styles.quitPrize}>R$ {currentPrize.toLocaleString('pt-BR')}</p>
            )}
            <div className={styles.modalActions}>
              <button className={styles.cancelBtn} onClick={() => setQuitModal(false)}>
                Continuar jogando
              </button>
              <button className={styles.quitConfirm} onClick={handleQuitConfirm}>
                Desistir
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
