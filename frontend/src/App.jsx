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
  ['conversion_likelihood', 'Conversion Likelihood'],
  ['message_market_match', 'Message-Market Match'],
  ['ad_type_execution', 'Ad Type Execution'],
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

function RunVerdict({ verdict, profitability }) {
  const colors = {
    'RUN': { bg: '#dcffe4', border: '#34d058', text: '#1a7f37' },
    'FIX FIRST': { bg: '#fff8c5', border: '#d4a72c', text: '#9a6700' },
    "DON'T RUN": { bg: '#ffebe9', border: '#ff8182', text: '#cf222e' },
  }
  const c = colors[verdict] || colors['FIX FIRST']

  return (
    <div style={{
      padding: '16px 20px',
      marginBottom: 24,
      background: c.bg,
      border: `2px solid ${c.border}`,
      borderRadius: 8,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: profitability ? 8 : 0 }}>
        <span style={{ fontSize: 13, fontWeight: 600, color: '#1f2328' }}>Verdict</span>
        <span style={{ fontSize: 18, fontWeight: 700, color: c.text, fontFamily: 'ui-monospace, monospace' }}>
          {verdict}
        </span>
      </div>
      {profitability && (
        <div style={{ fontSize: 13, color: '#1f2328', lineHeight: 1.5 }}>
          {profitability.reason}
        </div>
      )}
    </div>
  )
}

function ProfitabilityPanel({ data }) {
  if (!data) return null
  return (
    <div style={{
      border: '1px solid #d0d7de',
      borderRadius: 6,
      padding: '20px 24px',
      marginBottom: 24,
    }}>
      <h2 style={{ fontSize: 14, fontWeight: 600, color: '#1f2328', marginBottom: 12 }}>
        Profitability Analysis
      </h2>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, fontSize: 13 }}>
        <div>
          <span style={{ color: '#656d76' }}>Break-even {data.metric_label}</span>
          <div style={{ fontWeight: 600, fontFamily: 'ui-monospace, monospace', fontSize: 16 }}>
            ${data.break_even_cpa}
          </div>
        </div>
        {data.estimated_cpa_range && (
          <div>
            <span style={{ color: '#656d76' }}>Estimated {data.metric_label}</span>
            <div style={{ fontWeight: 600, fontFamily: 'ui-monospace, monospace', fontSize: 16 }}>
              ${data.estimated_cpa_range[0]} - ${data.estimated_cpa_range[1]}
            </div>
          </div>
        )}
        {data.margin_of_safety !== undefined && (
          <div>
            <span style={{ color: '#656d76' }}>Margin of Safety</span>
            <div style={{ fontWeight: 600, fontFamily: 'ui-monospace, monospace', fontSize: 16, color: data.margin_of_safety >= 20 ? '#1a7f37' : '#cf222e' }}>
              {data.margin_of_safety}%
            </div>
          </div>
        )}
        {data.monthly_conversions && (
          <div>
            <span style={{ color: '#656d76' }}>Monthly Conversions (est.)</span>
            <div style={{ fontWeight: 600, fontFamily: 'ui-monospace, monospace', fontSize: 16 }}>
              {data.monthly_conversions.pessimistic} - {data.monthly_conversions.optimistic}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function ContextBadges({ context }) {
  if (!context) return null
  const badges = [
    context.niche,
    context.business_type,
    context.price_point,
    context.audience_temperature && `${context.audience_temperature} traffic`,
    context.ad_style,
    context.ad_format,
  ].filter(Boolean)

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 16 }}>
      {badges.map((b, i) => (
        <span key={i} style={{
          fontSize: 11,
          padding: '3px 8px',
          background: '#f6f8fa',
          border: '1px solid #d0d7de',
          borderRadius: 12,
          color: '#656d76',
        }}>
          {b}
        </span>
      ))}
    </div>
  )
}

function FeedbackList({ items, title, color }) {
  if (!items || items.length === 0) return null
  return (
    <div style={{ marginBottom: 16 }}>
      <h3 style={{ fontSize: 12, fontWeight: 600, color, marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.5px' }}>{title}</h3>
      <ul style={{ margin: 0, paddingLeft: 16, fontSize: 13, color: '#1f2328', lineHeight: 1.7 }}>
        {items.map((item, i) => <li key={i}>{item}</li>)}
      </ul>
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
  const [accessCode, setAccessCode] = useState(localStorage.getItem('access_code') || '')
  const [businessType, setBusinessType] = useState('')
  const [productPrice, setProductPrice] = useState('')
  const [productCost, setProductCost] = useState('')
  const [closeRate, setCloseRate] = useState('')
  const [monthlyBudget, setMonthlyBudget] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleScore() {
    if (!adCopy.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)

    const body = { ad_copy: adCopy }
    if (accessCode) {
      body.access_code = accessCode
      localStorage.setItem('access_code', accessCode)
    }
    if (businessType) {
      body.business_type = businessType
      if (productPrice) body.product_price = parseFloat(productPrice)
      if (productCost) body.product_cost = parseFloat(productCost)
      if (closeRate) body.close_rate = parseFloat(closeRate)
      if (monthlyBudget) body.monthly_budget = parseFloat(monthlyBudget)
    }

    try {
      const res = await fetch(`${API_URL}/score`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (res.status === 403) {
        setError('Invalid access code.')
        return
      }
      if (!res.ok) throw new Error('Request failed')
      setResult(await res.json())
    } catch {
      setError('Could not reach the scoring API. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  const inputStyle = {
    padding: '8px 10px',
    fontSize: 13,
    border: '1px solid #d0d7de',
    borderRadius: 6,
    outline: 'none',
    color: '#1f2328',
    width: '100%',
    boxSizing: 'border-box',
  }

  const labelStyle = { fontSize: 12, color: '#656d76', marginBottom: 4, display: 'block' }

  return (
    <div>
      <header style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 22, fontWeight: 600, color: '#1f2328', marginBottom: 4 }}>
          Ad Profitability Scorer
        </h1>
        <p style={{ fontSize: 14, color: '#656d76', lineHeight: 1.6 }}>
          Scores ad copy across 12 dimensions, predicts conversion potential, calculates profitability,
          and tells you whether to run it, fix it, or kill it.
        </p>
      </header>

      <div style={{ marginBottom: 12 }}>
        <label style={{ fontSize: 12, color: '#656d76', marginBottom: 4, display: 'block' }}>Access Code</label>
        <input
          type="password"
          value={accessCode}
          onChange={e => setAccessCode(e.target.value)}
          placeholder="Enter access code"
          style={{
            padding: '8px 10px',
            fontSize: 13,
            border: '1px solid #d0d7de',
            borderRadius: 6,
            outline: 'none',
            color: '#1f2328',
            width: 200,
          }}
        />
      </div>

      <textarea
        value={adCopy}
        onChange={e => setAdCopy(e.target.value)}
        placeholder="Paste your ad copy or video transcript here..."
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
          boxSizing: 'border-box',
        }}
        onFocus={e => (e.target.style.borderColor = '#0969da')}
        onBlur={e => (e.target.style.borderColor = '#d0d7de')}
      />

      {/* Business Inputs */}
      <div style={{
        marginTop: 16,
        padding: '16px 20px',
        border: '1px solid #d0d7de',
        borderRadius: 6,
        background: '#f6f8fa',
      }}>
        <h3 style={{ fontSize: 13, fontWeight: 600, color: '#1f2328', marginBottom: 12 }}>
          Business Economics (optional — enables profitability analysis)
        </h3>

        <div style={{ marginBottom: 12 }}>
          <label style={labelStyle}>Business Type</label>
          <select
            value={businessType}
            onChange={e => setBusinessType(e.target.value)}
            style={{ ...inputStyle, background: '#fff' }}
          >
            <option value="">-- Select --</option>
            <option value="ecommerce">E-commerce / Product</option>
            <option value="lead_gen">Lead Gen / Service</option>
          </select>
        </div>

        {businessType && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={labelStyle}>
                {businessType === 'ecommerce' ? 'Product Price ($)' : 'Deal Value ($)'}
              </label>
              <input
                type="number"
                value={productPrice}
                onChange={e => setProductPrice(e.target.value)}
                placeholder={businessType === 'ecommerce' ? '49.99' : '5000'}
                style={inputStyle}
              />
            </div>

            {businessType === 'ecommerce' ? (
              <div>
                <label style={labelStyle}>Product Cost ($)</label>
                <input
                  type="number"
                  value={productCost}
                  onChange={e => setProductCost(e.target.value)}
                  placeholder="15.00"
                  style={inputStyle}
                />
              </div>
            ) : (
              <div>
                <label style={labelStyle}>Close Rate (%)</label>
                <input
                  type="number"
                  value={closeRate}
                  onChange={e => setCloseRate(e.target.value)}
                  placeholder="20"
                  style={inputStyle}
                />
              </div>
            )}

            <div style={{ gridColumn: '1 / -1' }}>
              <label style={labelStyle}>Monthly Ad Budget ($)</label>
              <input
                type="number"
                value={monthlyBudget}
                onChange={e => setMonthlyBudget(e.target.value)}
                placeholder="3000"
                style={inputStyle}
              />
            </div>
          </div>
        )}
      </div>

      <button
        onClick={handleScore}
        disabled={loading || !adCopy.trim()}
        style={{
          marginTop: 16,
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
        {loading ? 'Scoring...' : 'Score Ad'}
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

          {/* Run Verdict - most prominent */}
          <RunVerdict verdict={result.run_verdict} profitability={result.profitability} />

          {/* Context badges */}
          <ContextBadges context={result.context} />

          {/* Score cards */}
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

          {/* Profitability panel */}
          <ProfitabilityPanel data={result.profitability} />

          {/* Quick kill flags */}
          {result.quick_kill_flags && result.quick_kill_flags.length > 0 && (
            <div style={{
              padding: '12px 16px',
              marginBottom: 24,
              background: '#ffebe9',
              border: '1px solid rgba(255,129,130,0.4)',
              borderRadius: 6,
            }}>
              <h3 style={{ fontSize: 12, fontWeight: 600, color: '#cf222e', marginBottom: 6, textTransform: 'uppercase' }}>Red Flags</h3>
              <ul style={{ margin: 0, paddingLeft: 16, fontSize: 13, color: '#1f2328', lineHeight: 1.7 }}>
                {result.quick_kill_flags.map((f, i) => <li key={i}>{f}</li>)}
              </ul>
            </div>
          )}

          {/* Strengths, weaknesses, fixes */}
          <div style={{ border: '1px solid #d0d7de', borderRadius: 6, padding: '20px 24px', marginBottom: 24 }}>
            <FeedbackList items={result.top_strengths} title="Strengths" color="#1a7f37" />
            <FeedbackList items={result.top_weaknesses} title="Weaknesses" color="#cf222e" />
            <FeedbackList items={result.priority_fixes} title="Priority Fixes" color="#0969da" />
          </div>

          {/* Dimension breakdown */}
          <div style={{
            border: '1px solid #d0d7de',
            borderRadius: 6,
            padding: '20px 24px',
          }}>
            <h2 style={{ fontSize: 14, fontWeight: 600, color: '#1f2328', marginBottom: 16 }}>
              Dimension Breakdown
            </h2>
            {DIMENSIONS.map(([key, label]) => (
              result.scores[key] !== undefined && <ScoreBar key={key} label={label} value={result.scores[key]} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
