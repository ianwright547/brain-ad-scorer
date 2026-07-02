import TextMetricsPanel from './TextMetricsPanel'
import ImageMetricsPanel from './ImageMetricsPanel'

const DIMENSIONS = [
  ['hook_power', 'hook_power'],
  ['offer_strength', 'offer_strength'],
  ['persuasion_depth', 'persuasion_depth'],
  ['narrative_emotion', 'narrative_emotion'],
  ['structure_flow', 'structure_flow'],
  ['cta_clarity', 'cta_clarity'],
  ['audience_targeting', 'audience_targeting'],
  ['funnel_fit', 'funnel_fit'],
  ['platform_optimization', 'platform_optimization'],
  ['conversion_likelihood', 'conversion_likelihood'],
  ['message_market_match', 'message_market_match'],
  ['ad_type_execution', 'ad_type_execution'],
]

const VERDICT_CLASS = { 'RUN': 'run', 'FIX FIRST': 'fix', "DON'T RUN": 'kill' }
const VERDICT_ICON = { 'RUN': '✓', 'FIX FIRST': '●', "DON'T RUN": '✕' }

function scoreClass(v) {
  if (v >= 8) return 'score-good'
  if (v >= 6) return 'score-mid'
  return 'score-bad'
}

function barColor(v) {
  if (v >= 8) return 'var(--green)'
  if (v >= 6) return 'var(--yellow)'
  return 'var(--red)'
}

function VerdictBanner({ verdict, profitability, cached }) {
  const cls = VERDICT_CLASS[verdict] || 'fix'
  return (
    <div className="panel result-section">
      <div className={`verdict ${cls}`}>
        <div className="verdict-icon">{VERDICT_ICON[verdict] || '●'}</div>
        <div>
          <div className="verdict-title">{verdict}</div>
          {profitability && <div className="verdict-reason">{profitability.reason}</div>}
        </div>
        {cached && <span className="cache-pill" title="Served from the SQLite cache — no API call was made">cache hit</span>}
      </div>
    </div>
  )
}

function ScoreCards({ result }) {
  const delta = (v) => {
    const d = (v - result.claude_score).toFixed(2)
    return d > 0 ? `+${d}` : d
  }
  return (
    <div className="score-cards result-section">
      <div className="score-card">
        <div className={`value ${scoreClass(result.rf_score)}`}>{result.rf_score}</div>
        <div className="label">random forest</div>
        <div className="sublabel">ML · Δ {delta(result.rf_score)} vs claude</div>
      </div>
      <div className="score-card">
        <div className={`value ${scoreClass(result.xgb_score)}`}>{result.xgb_score}</div>
        <div className="label">xgboost</div>
        <div className="sublabel">ML · Δ {delta(result.xgb_score)} vs claude</div>
      </div>
      <div className="score-card">
        <div className={`value ${scoreClass(result.claude_score)}`}>{result.claude_score}</div>
        <div className="label">claude</div>
        <div className="sublabel">LLM expert score</div>
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
  if (!badges.length) return null
  return (
    <div className="context-badges result-section">
      {badges.map((b, i) => <span key={i}>{b}</span>)}
    </div>
  )
}

function ProfitabilityPanel({ data }) {
  if (!data) return null
  return (
    <div className="panel result-section">
      <div className="panel-header"><span>unit-economics</span></div>
      <div className="profit-grid">
        <div className="metric">
          <div className="k">break-even {data.metric_label}</div>
          <div className="v">${data.break_even_cpa}</div>
        </div>
        {data.estimated_cpa_range && (
          <div className="metric">
            <div className="k">estimated {data.metric_label} (heuristic)</div>
            <div className="v">${data.estimated_cpa_range[0]} – ${data.estimated_cpa_range[1]}</div>
          </div>
        )}
        {data.margin_of_safety !== undefined && (
          <div className="metric">
            <div className="k">margin of safety</div>
            <div className="v" style={{ color: data.margin_of_safety >= 20 ? 'var(--green)' : 'var(--red)' }}>
              {data.margin_of_safety}%
            </div>
          </div>
        )}
        {data.monthly_conversions && (
          <div className="metric">
            <div className="k">est. monthly conversions</div>
            <div className="v">{data.monthly_conversions.pessimistic} – {data.monthly_conversions.optimistic}</div>
          </div>
        )}
      </div>
    </div>
  )
}

function DiffFeedback({ result }) {
  const { top_strengths = [], top_weaknesses = [], priority_fixes = [], quick_kill_flags = [] } = result
  if (!top_strengths.length && !top_weaknesses.length && !priority_fixes.length && !quick_kill_flags.length) return null
  return (
    <div className="panel result-section">
      <div className="panel-header">
        <span>review.diff</span>
        <span>+{top_strengths.length} −{top_weaknesses.length} →{priority_fixes.length}</span>
      </div>
      <div className="diff" style={{ padding: '10px 0' }}>
        {quick_kill_flags.map((f, i) => (
          <div className="diff-line diff-flag" key={`k${i}`}>
            <span className="sign">✕</span><span>KILL FLAG: {f}</span>
          </div>
        ))}
        {top_strengths.map((s, i) => (
          <div className="diff-line diff-add" key={`s${i}`}>
            <span className="sign">+</span><span>{s}</span>
          </div>
        ))}
        {top_weaknesses.map((w, i) => (
          <div className="diff-line diff-del" key={`w${i}`}>
            <span className="sign">−</span><span>{w}</span>
          </div>
        ))}
        {priority_fixes.map((f, i) => (
          <div className="diff-line diff-fix" key={`f${i}`}>
            <span className="sign">→</span><span>{f}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function DimensionBars({ scores }) {
  return (
    <div className="panel result-section">
      <div className="panel-header">
        <span>dimension-scores</span>
        <span>12 expert dimensions · 1-10</span>
      </div>
      <div style={{ padding: '10px 0' }}>
        {DIMENSIONS.map(([key, label]) => (
          scores[key] !== undefined && (
            <div className="dim-row" key={key}>
              <span className="name">{label}</span>
              <div className="bar">
                <div className="fill" style={{ width: `${(scores[key] / 10) * 100}%`, background: barColor(scores[key]) }} />
              </div>
              <span className="num" style={{ color: barColor(scores[key]) }}>{scores[key]}</span>
            </div>
          )
        ))}
      </div>
    </div>
  )
}

export default function Results({ result }) {
  if (!result) return null
  return (
    <div>
      <VerdictBanner verdict={result.run_verdict} profitability={result.profitability} cached={result.cached} />
      <ContextBadges context={result.context} />
      <ScoreCards result={result} />
      <ProfitabilityPanel data={result.profitability} />
      <DiffFeedback result={result} />
      <ImageMetricsPanel metrics={result.image_metrics} />
      <TextMetricsPanel metrics={result.text_metrics} />
      <DimensionBars scores={result.scores} />
    </div>
  )
}
