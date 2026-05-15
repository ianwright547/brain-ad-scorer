import { useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const DIMENSION_LABELS = {
  hook_power: 'Hook Power',
  offer_strength: 'Offer Strength',
  persuasion_depth: 'Persuasion Depth',
  narrative_emotion: 'Narrative & Emotion',
  structure_flow: 'Structure & Flow',
  cta_clarity: 'CTA Clarity',
  audience_targeting: 'Audience Targeting',
  funnel_fit: 'Funnel Fit',
  platform_optimization: 'Platform Optimization',
}

function ScoreBar({ label, value }) {
  const pct = (value / 10) * 100
  const color = value >= 8 ? '#22c55e' : value >= 6 ? '#f59e0b' : '#ef4444'
  return (
    <div style={{ marginBottom: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
        <span style={{ fontSize: '14px', color: '#d1d5db' }}>{label}</span>
        <span style={{ fontSize: '14px', fontWeight: 'bold', color }}>{value}/10</span>
      </div>
      <div style={{ background: '#374151', borderRadius: '4px', height: '8px' }}>
        <div style={{ width: `${pct}%`, background: color, borderRadius: '4px', height: '8px', transition: 'width 0.6s ease' }} />
      </div>
    </div>
  )
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
      const response = await fetch(`${API_URL}/score`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ad_copy: adCopy }),
      })
      if (!response.ok) throw new Error('Scoring failed')
      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError('Could not reach the scoring API. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  const impactColor = result
    ? result.overall_impact >= 8 ? '#22c55e' : result.overall_impact >= 6 ? '#f59e0b' : '#ef4444'
    : '#fff'

  return (
    <div style={{ minHeight: '100vh', background: '#111827', color: '#f9fafb', fontFamily: 'system-ui, sans-serif', padding: '40px 20px' }}>
      <div style={{ maxWidth: '720px', margin: '0 auto' }}>

        <h1 style={{ fontSize: '28px', fontWeight: 'bold', marginBottom: '4px' }}>Brain Ad Scorer</h1>
        <p style={{ color: '#9ca3af', marginBottom: '32px' }}>Scores your ad copy using Hormozi's framework + a trained ML model.</p>

        <textarea
          value={adCopy}
          onChange={e => setAdCopy(e.target.value)}
          placeholder="Paste your ad copy here..."
          style={{
            width: '100%', minHeight: '180px', background: '#1f2937', border: '1px solid #374151',
            borderRadius: '8px', padding: '16px', color: '#f9fafb', fontSize: '15px',
            resize: 'vertical', boxSizing: 'border-box', outline: 'none',
          }}
        />

        <button
          onClick={handleScore}
          disabled={loading || !adCopy.trim()}
          style={{
            marginTop: '16px', width: '100%', padding: '14px', background: loading ? '#374151' : '#6366f1',
            color: '#fff', border: 'none', borderRadius: '8px', fontSize: '16px',
            fontWeight: 'bold', cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          {loading ? 'Scoring...' : 'Score This Ad'}
        </button>

        {error && (
          <div style={{ marginTop: '24px', background: '#450a0a', border: '1px solid #ef4444', borderRadius: '8px', padding: '16px', color: '#fca5a5' }}>
            {error}
          </div>
        )}

        {result && (
          <div style={{ marginTop: '32px' }}>
            <div style={{ background: '#1f2937', borderRadius: '12px', padding: '24px', marginBottom: '24px', textAlign: 'center' }}>
              <div style={{ fontSize: '56px', fontWeight: 'bold', color: impactColor }}>
                {result.overall_impact}
              </div>
              <div style={{ color: '#9ca3af', fontSize: '14px', marginTop: '4px' }}>Model Score / 10</div>
              <div style={{ marginTop: '12px', fontSize: '18px', fontWeight: '600', color: impactColor }}>
                {result.verdict}
              </div>
              <div style={{ color: '#6b7280', fontSize: '13px', marginTop: '4px' }}>
                Claude raw score: {result.claude_score}/10
              </div>
            </div>

            <div style={{ background: '#1f2937', borderRadius: '12px', padding: '24px' }}>
              <h2 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '20px', color: '#e5e7eb' }}>Dimension Breakdown</h2>
              {Object.entries(DIMENSION_LABELS).map(([key, label]) => (
                <ScoreBar key={key} label={label} value={result.scores[key]} />
              ))}
            </div>
          </div>
        )}

      </div>
    </div>
  )
}
