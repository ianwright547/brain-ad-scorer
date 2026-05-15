import { useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const DIMENSIONS = [
  ['hook_power', 'Hook Power'],
  ['offer_strength', 'Offer Strength'],
  ['persuasion_depth', 'Persuasion Depth'],
  ['narrative_emotion', 'Narrative & Emotion'],
  ['structure_flow', 'Structure & Flow'],
  ['cta_clarity', 'CTA Clarity'],
  ['audience_targeting', 'Audience Targeting'],
  ['funnel_fit', 'Funnel Fit'],
  ['platform_optimization', 'Platform Optimization'],
]

function ScoreBar({ label, value }) {
  const pct = (value / 10) * 100
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
        <span style={{ fontSize: 13, color: '#656d76' }}>{label}</span>
        <span style={{ fontSize: 13, fontFamily: 'ui-monospace, monospace', fontWeight: 600, color: '#1f2328' }}>{value}</span>
      </div>
      <div style={{ background: '#eaeef2', borderRadius: 3, height: 6, overflow: 'hidden' }}>
        <div
          style={{
            width: `${pct}%`,
            height: 6,
            borderRadius: 3,
            transition: 'width 0.5s ease',
            background: value >= 8 ? '#1a7f37' : value >= 6 ? '#9a6700' : '#cf222e',
          }}
        />
      </div>
    </div>
  )
}

function ScoreCard({ value, label, sublabel, color }) {
  return (
    <div style={{
      flex: 1,
      border: '1px solid #d0d7de',
      borderRadius: 6,
      padding: '16px 12px',
      textAlign: 'center',
    }}>
      <div style={{
        fontSize: 32,
        fontWeight: 700,
        fontFamily: 'ui-monospace, monospace',
        color,
      }}>
        {value}
      </div>
      <div style={{ fontSize: 12, fontWeight: 600, color: '#1f2328', marginTop: 2 }}>{label}</div>
      {sublabel && <div style={{ fontSize: 11, color: '#656d76', marginTop: 1 }}>{sublabel}</div>}
    </div>
  )
}

function getScoreColor(v) {
  if (v >= 8) return '#1a7f37'
  if (v >= 6) return '#9a6700'
  return '#cf222e'
}

export default function App() {
  const [adCopy, setAdCopy] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleScore() {
    if (!adCopy.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const res = await fetch(`${API_URL}/score`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ad_copy: adCopy }),
      })
      if (!res.ok) throw new Error('Request failed')
      setResult(await res.json())
    } catch {
      setError('Could not reach the scoring API. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <header style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 22, fontWeight: 600, color: '#1f2328', marginBottom: 4 }}>
          ML Ad Scorer
        </h1>
        <p style={{ fontSize: 14, color: '#656d76', lineHeight: 1.6 }}>
          Evaluates ad copy across 9 persuasion dimensions using an LLM, then compares
          predictions from a Random Forest, XGBoost, and the LLM's own score.
        </p>
      </header>

      <textarea
        value={adCopy}
        onChange={e => setAdCopy(e.target.value)}
        placeholder="Paste your ad copy here..."
        rows={8}
        style={{
          width: '100%',
          padding: '10px 12px',
          fontSize: 14,
          fontFamily: 'inherit',
          border: '1px solid #d0d7de',
          borderRadius: 6,
          resize: 'vertical',
          outline: 'none',
          color: '#1f2328',
          background: '#ffffff',
        }}
        onFocus={e => (e.target.style.borderColor = '#0969da')}
        onBlur={e => (e.target.style.borderColor = '#d0d7de')}
      />

      <button
        onClick={handleScore}
        disabled={loading || !adCopy.trim()}
        style={{
          marginTop: 12,
          padding: '9px 20px',
          fontSize: 14,
          fontWeight: 600,
          fontFamily: 'inherit',
          color: '#ffffff',
          background: loading ? '#8c959f' : '#0969da',
          border: '1px solid rgba(27,31,36,0.15)',
          borderRadius: 6,
          cursor: loading ? 'default' : 'pointer',
          opacity: !adCopy.trim() ? 0.5 : 1,
        }}
      >
        {loading ? 'Scoring...' : 'Score ad'}
      </button>

      {error && (
        <div style={{
          marginTop: 16,
          padding: '12px 16px',
          fontSize: 13,
          color: '#cf222e',
          background: '#ffebe9',
          border: '1px solid rgba(255,129,130,0.4)',
          borderRadius: 6,
        }}>
          {error}
        </div>
      )}

      {result && (
        <div style={{ marginTop: 32 }}>

          <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
            <ScoreCard
              value={result.rf_score}
              label="Random Forest"
              sublabel="ML prediction"
              color={getScoreColor(result.rf_score)}
            />
            <ScoreCard
              value={result.xgb_score}
              label="XGBoost"
              sublabel="ML prediction"
              color={getScoreColor(result.xgb_score)}
            />
            <ScoreCard
              value={result.claude_score}
              label="Claude"
              sublabel="LLM raw score"
              color={getScoreColor(result.claude_score)}
            />
          </div>

          <div style={{
            padding: '12px 16px',
            marginBottom: 24,
            border: '1px solid #d0d7de',
            borderRadius: 6,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <span style={{ fontSize: 13, color: '#656d76' }}>Verdict</span>
            <span style={{ fontSize: 14, fontWeight: 600, color: '#1f2328' }}>{result.verdict}</span>
          </div>

          <div style={{
            border: '1px solid #d0d7de',
            borderRadius: 6,
            padding: '20px 24px',
          }}>
            <h2 style={{ fontSize: 14, fontWeight: 600, color: '#1f2328', marginBottom: 16 }}>
              Dimension breakdown
            </h2>
            {DIMENSIONS.map(([key, label]) => (
              <ScoreBar key={key} label={label} value={result.scores[key]} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
