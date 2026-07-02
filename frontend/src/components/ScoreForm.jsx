import { useState, useRef } from 'react'

export default function ScoreForm({ onScore, onPreflight, loading, preflightLoading }) {
  const [adCopy, setAdCopy] = useState('')
  const [imageB64, setImageB64] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [imageName, setImageName] = useState('')
  const [dragging, setDragging] = useState(false)
  const [accessCode, setAccessCode] = useState(localStorage.getItem('access_code') || '')
  const [businessType, setBusinessType] = useState('')
  const [productPrice, setProductPrice] = useState('')
  const [productCost, setProductCost] = useState('')
  const [closeRate, setCloseRate] = useState('')
  const [monthlyBudget, setMonthlyBudget] = useState('')
  const fileRef = useRef(null)

  function loadImage(file) {
    if (!file || !file.type.startsWith('image/')) return
    const reader = new FileReader()
    reader.onload = () => {
      setImageB64(reader.result.split(',')[1])
      setImagePreview(reader.result)
      setImageName(file.name)
    }
    reader.readAsDataURL(file)
  }

  function clearImage(e) {
    e.stopPropagation()
    setImageB64(null)
    setImagePreview(null)
    setImageName('')
    if (fileRef.current) fileRef.current.value = ''
  }

  function submit() {
    const body = {}
    if (adCopy.trim()) body.ad_copy = adCopy
    if (imageB64) body.image_base64 = imageB64
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
    onScore(body)
  }

  const hasInput = adCopy.trim() || imageB64

  return (
    <div className="panel">
      <div className="panel-header">
        <span>new-evaluation.md</span>
        <span>paste copy, drop a creative, or both</span>
      </div>
      <div className="panel-body">
        <textarea
          className="ad-textarea"
          value={adCopy}
          onChange={e => setAdCopy(e.target.value)}
          placeholder={'// Paste ad copy or a video transcript…\n\nATTENTION Austin homeowners — your lawn is costing you weekends.\nWe mow, edge, and clean up in under an hour. First cut is $1.\nBook before Friday: only 12 spots this month.'}
          spellCheck={false}
        />
        <div className="form-meta">
          <span>{adCopy.trim() ? `${adCopy.trim().split(/\s+/).length} words` : 'empty'}</span>
          <span>text and images are hashed for caching — identical input never bills twice</span>
        </div>

        <div
          className={`dropzone${dragging ? ' dragging' : ''}`}
          onClick={() => fileRef.current?.click()}
          onDragOver={e => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={e => {
            e.preventDefault()
            setDragging(false)
            loadImage(e.dataTransfer.files[0])
          }}
        >
          <input
            ref={fileRef}
            type="file"
            accept="image/png,image/jpeg,image/gif,image/webp"
            onChange={e => loadImage(e.target.files[0])}
          />
          {imagePreview ? (
            <>
              <img className="thumb" src={imagePreview} alt="ad creative preview" />
              <span>{imageName}</span>
              <button className="remove" onClick={clearImage}>remove</button>
            </>
          ) : (
            <span>+ drop an ad creative here (png / jpeg / gif / webp, max 5MB)</span>
          )}
        </div>

        <details className="econ">
          <summary>business economics — optional, enables the break-even math</summary>
          <div className="econ-fields">
            <div className="field" style={{ gridColumn: '1 / -1' }}>
              <label>business type</label>
              <select value={businessType} onChange={e => setBusinessType(e.target.value)}>
                <option value="">— none —</option>
                <option value="ecommerce">e-commerce / product</option>
                <option value="lead_gen">lead gen / service</option>
              </select>
            </div>
            {businessType && (
              <>
                <div className="field">
                  <label>{businessType === 'ecommerce' ? 'product price ($)' : 'deal value ($)'}</label>
                  <input type="number" value={productPrice} onChange={e => setProductPrice(e.target.value)}
                    placeholder={businessType === 'ecommerce' ? '49.99' : '5000'} />
                </div>
                {businessType === 'ecommerce' ? (
                  <div className="field">
                    <label>product cost ($)</label>
                    <input type="number" value={productCost} onChange={e => setProductCost(e.target.value)} placeholder="15.00" />
                  </div>
                ) : (
                  <div className="field">
                    <label>close rate (%)</label>
                    <input type="number" value={closeRate} onChange={e => setCloseRate(e.target.value)} placeholder="20" />
                  </div>
                )}
                <div className="field" style={{ gridColumn: '1 / -1' }}>
                  <label>monthly ad budget ($)</label>
                  <input type="number" value={monthlyBudget} onChange={e => setMonthlyBudget(e.target.value)} placeholder="3000" />
                </div>
              </>
            )}
          </div>
        </details>

        <div className="actions">
          <button className="btn btn-primary" onClick={submit} disabled={loading || !hasInput}>
            {loading && <span className="spinner" />}
            {loading ? 'scoring…' : 'score ad'}
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => onPreflight(adCopy)}
            disabled={preflightLoading || !adCopy.trim()}
            title="Deterministic local checks — no API call, no cost"
          >
            {preflightLoading ? 'running…' : 'pre-flight (free)'}
          </button>
          <div className="access-field">
            <input
              type="password"
              value={accessCode}
              onChange={e => setAccessCode(e.target.value)}
              placeholder="access code"
              autoComplete="off"
            />
          </div>
        </div>
      </div>
    </div>
  )
}
