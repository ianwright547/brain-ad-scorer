import { useEffect, useState } from 'react'
import { fetchHistory } from '../api'

const VERDICT_CLASS = { 'RUN': 'run', 'FIX FIRST': 'fix', "DON'T RUN": 'kill' }

function timeAgo(sqliteUtc) {
  // SQLite datetime('now') is UTC without a zone marker — append Z so
  // the Date parses correctly, then render a rough relative time.
  const then = new Date(sqliteUtc.replace(' ', 'T') + 'Z')
  const mins = Math.floor((Date.now() - then.getTime()) / 60000)
  if (Number.isNaN(mins)) return sqliteUtc
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  if (mins < 1440) return `${Math.floor(mins / 60)}h ago`
  return `${Math.floor(mins / 1440)}d ago`
}

export default function HistoryTab({ active }) {
  const [rows, setRows] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!active) return
    fetchHistory().then(setRows).catch(() => setError('Could not load history from the API.'))
  }, [active])

  if (!active) return null
  if (error) return <div className="flash-error">{error}</div>

  return (
    <div className="panel">
      <div className="panel-header">
        <span>scoring-history</span>
        <span>{rows ? `${rows.length} evaluations` : 'loading…'}</span>
      </div>
      {rows && rows.length === 0 && (
        <div className="empty-state">nothing scored yet — every evaluation lands here</div>
      )}
      {rows && rows.map(r => (
        <div className="history-row" key={r.id}>
          <span className={`verdict-badge ${VERDICT_CLASS[r.run_verdict] || 'fix'}`}>{r.run_verdict}</span>
          <span className="history-preview">
            {r.input_type === 'image' ? '🖼 ' : ''}{r.ad_preview}
          </span>
          <span className="history-scores">
            rf {r.rf_score?.toFixed(1)} · xgb {r.xgb_score?.toFixed(1)} · claude {r.claude_score}
          </span>
          {r.cached === 1 && <span className="cache-pill">cache</span>}
          <span className="history-time">{timeAgo(r.created_at)}</span>
        </div>
      ))}
    </div>
  )
}
