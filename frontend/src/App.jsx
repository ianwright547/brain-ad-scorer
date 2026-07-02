import { useEffect, useState } from 'react'
import { scoreAd, analyzeAd, checkHealth } from './api'
import ScoreForm from './components/ScoreForm'
import Results from './components/Results'
import TextMetricsPanel from './components/TextMetricsPanel'
import HistoryTab from './components/HistoryTab'

export default function App() {
  const [tab, setTab] = useState('score')
  const [result, setResult] = useState(null)
  const [preflight, setPreflight] = useState(null)
  const [loading, setLoading] = useState(false)
  const [preflightLoading, setPreflightLoading] = useState(false)
  const [error, setError] = useState(null)
  const [apiUp, setApiUp] = useState(null)

  useEffect(() => {
    checkHealth().then(setApiUp)
  }, [])

  async function handleScore(body) {
    setLoading(true)
    setError(null)
    setResult(null)
    setPreflight(null)
    try {
      setResult(await scoreAd(body))
    } catch (e) {
      setError(e.status === 403 ? 'Invalid access code.' : e.message)
    } finally {
      setLoading(false)
    }
  }

  async function handlePreflight(adCopy) {
    setPreflightLoading(true)
    setError(null)
    try {
      const data = await analyzeAd(adCopy)
      setPreflight(data.text_metrics)
    } catch (e) {
      setError(e.message)
    } finally {
      setPreflightLoading(false)
    }
  }

  return (
    <div>
      <header className="site-header">
        <div className="breadcrumb">
          <span className="owner">ianwright547</span>
          <span className="sep">/</span>
          <span className="repo">brain-ad-scorer</span>
          <span className="badge-pill">public beta</span>
        </div>
        <div className="api-status">
          <span className={`status-dot${apiUp ? ' ok' : ''}`} />
          {apiUp === null ? 'checking api…' : apiUp ? 'api: operational' : 'api: unreachable'}
        </div>
      </header>

      <p className="tagline">
        Scores ads before you spend money on them. An expert persona grades 12 dimensions,
        two ML models predict overall impact, a hand-written <code>preflight</code> engine runs
        deterministic checks, and the break-even math decides: run it, fix it, or kill it.
      </p>

      <nav className="tabs">
        <button className={`tab${tab === 'score' ? ' active' : ''}`} onClick={() => setTab('score')}>
          score
        </button>
        <button className={`tab${tab === 'history' ? ' active' : ''}`} onClick={() => setTab('history')}>
          history
        </button>
      </nav>

      {tab === 'score' && (
        <>
          <ScoreForm
            onScore={handleScore}
            onPreflight={handlePreflight}
            loading={loading}
            preflightLoading={preflightLoading}
          />
          {error && <div className="flash-error">{error}</div>}
          {preflight && !result && <TextMetricsPanel metrics={preflight} />}
          <Results result={result} />
        </>
      )}

      <HistoryTab active={tab === 'history'} />

      <footer className="site-footer">
        <span>python · fastapi · scikit-learn · xgboost · claude api · react</span>
        <a href="https://github.com/ianwright547/brain-ad-scorer" target="_blank" rel="noreferrer">
          source on github
        </a>
      </footer>
    </div>
  )
}
