export default function ImageMetricsPanel({ metrics }) {
  if (!metrics) return null
  const m = metrics

  const rows = [
    ['format', m.format],
    ['dimensions', `${m.width} × ${m.height} px (${m.file_size_kb} KB)`],
    ['nearest placement', `${m.nearest_platform} — ${m.aspect_deviation_pct}% off spec`],
    ['brightness', `${m.brightness} / 255`],
    ['contrast (RMS)', m.contrast],
    ['sharpness (Laplacian var)', m.sharpness],
    ['edge density', m.edge_density],
    ['colorfulness (Hasler-Süsstrunk)', m.colorfulness],
  ]

  return (
    <div className="panel result-section">
      <div className="panel-header">
        <span>creative-inspector — pixel-level metrics, computed locally</span>
        <span>$0.00</span>
      </div>
      <table className="inspector">
        <tbody>
          {rows.map(([k, v]) => (
            <tr key={k}>
              <td className="key">{k}</td>
              <td className="val">{v}</td>
            </tr>
          ))}
          {m.flags.map((f, i) => (
            <tr key={`flag-${i}`}>
              <td className="key" style={{ color: 'var(--red)' }}>⚠ flag</td>
              <td className="val" style={{ color: 'var(--red)' }}>{f}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
