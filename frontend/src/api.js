const API_URL = import.meta.env.VITE_API_URL || 'https://brain-ad-scorer.fly.dev'

async function post(path, body) {
  const res = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const detail = await res.json().then(d => d.detail).catch(() => null)
    const err = new Error(detail || `Request failed (${res.status})`)
    err.status = res.status
    throw err
  }
  return res.json()
}

export function scoreAd(body) {
  return post('/score', body)
}

export function analyzeAd(adCopy) {
  return post('/analyze', { ad_copy: adCopy })
}

export async function fetchHistory(limit = 25) {
  const res = await fetch(`${API_URL}/history?limit=${limit}`)
  if (!res.ok) throw new Error('Could not load history')
  const data = await res.json()
  return data.history
}

export async function checkHealth() {
  try {
    const res = await fetch(`${API_URL}/health`)
    return res.ok
  } catch {
    return false
  }
}
