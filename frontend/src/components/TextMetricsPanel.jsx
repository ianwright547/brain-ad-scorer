function Line({ children }) {
  return <div>{children}</div>
}

export default function TextMetricsPanel({ metrics }) {
  if (!metrics) return null
  const m = metrics

  const list = (arr) => arr.length ? arr.join(', ') : 'none'
  const listClass = (arr) => arr.length ? 't-ok' : 't-bad'

  return (
    <div className="panel result-section">
      <div className="panel-header">
        <span>pre-flight — deterministic checks, computed locally in &lt;1ms</span>
        <span>$0.00</span>
      </div>
      <div className="terminal">
        <Line>
          <span className="prompt">$ </span>
          <span className="cmd">preflight --check ad.txt</span>
        </Line>
        <Line>
          <span className="t-dim">  words </span><span className="t-val">{m.word_count}</span>
          <span className="t-dim"> · sentences </span><span className="t-val">{m.sentence_count}</span>
          <span className="t-dim"> · avg words/sentence </span><span className="t-val">{m.avg_words_per_sentence}</span>
        </Line>
        {m.flesch_reading_ease !== null && (
          <Line>
            <span className="t-dim">  readability </span>
            <span className="t-val">{m.flesch_reading_ease}</span>
            <span className="t-dim"> ({m.readability}) · grade level </span>
            <span className={m.flesch_kincaid_grade > 7 ? 't-warn' : 't-ok'}>{m.flesch_kincaid_grade}</span>
          </Line>
        )}
        <Line>
          <span className={listClass(m.cta_verbs)}>  {m.cta_verbs.length ? '✓' : '✗'} </span>
          <span className="t-dim">cta verbs: </span>
          <span className={listClass(m.cta_verbs)}>{list(m.cta_verbs)}</span>
        </Line>
        <Line>
          <span className={listClass(m.power_words)}>  {m.power_words.length ? '✓' : '·'} </span>
          <span className="t-dim">power words: </span>
          <span className="t-val">{list(m.power_words)}</span>
        </Line>
        <Line>
          <span className={listClass(m.urgency_words)}>  {m.urgency_words.length ? '✓' : '·'} </span>
          <span className="t-dim">urgency: </span>
          <span className="t-val">{list(m.urgency_words)}</span>
        </Line>
        <Line>
          <span className={listClass(m.risk_reversal_phrases)}>  {m.risk_reversal_phrases.length ? '✓' : '✗'} </span>
          <span className="t-dim">risk reversal: </span>
          <span className="t-val">{list(m.risk_reversal_phrases)}</span>
        </Line>
        <Line>
          <span className={m.specificity_count ? 't-ok' : 't-bad'}>  {m.specificity_count ? '✓' : '✗'} </span>
          <span className="t-dim">specificity: </span>
          <span className="t-val">
            {m.specificity_count
              ? [...m.specificity.money_amounts, ...m.specificity.percentages, ...m.specificity.timeframes].join(', ')
              : 'no concrete numbers'}
          </span>
        </Line>
        <Line>
          <span className="t-dim">  second person </span><span className="t-val">{m.second_person_count}×</span>
          <span className="t-dim"> · first person </span><span className="t-val">{m.first_person_count}×</span>
          <span className="t-dim"> · questions </span><span className="t-val">{m.question_count}</span>
        </Line>
        {m.flags.map((f, i) => (
          <Line key={i}>
            <span className="t-bad">  ⚠ {f}</span>
          </Line>
        ))}
        {m.flags.length === 0 && (
          <Line><span className="t-ok">  ✓ all deterministic checks passed</span></Line>
        )}
      </div>
    </div>
  )
}
