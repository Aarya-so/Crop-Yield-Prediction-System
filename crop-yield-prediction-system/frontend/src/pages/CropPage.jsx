import { useState } from 'react'
import './Page.css'

export default function CropPage() {
  const [fields, setFields] = useState({
    temperature: '', humidity: '', nitrogen: '', phosphorus: '', potassium: ''
  })
  const [result, setResult]   = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  const set = (k) => (e) => setFields(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true); setError(''); setResult('')
    try {
      const res  = await fetch('http://127.0.0.1:5000/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          temperature: Number(fields.temperature),
          humidity:    Number(fields.humidity),
          nitrogen:    Number(fields.nitrogen),
          phosphorus:  Number(fields.phosphorus),
          potassium:   Number(fields.potassium),
        }),
      })
      const data = await res.json()
      setResult(data)
    } catch {
      setError('Could not reach the server. Is Flask running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-wrapper">
      <div className="card">
        <div className="card-header">
          <span className="card-icon">🌾</span>
          <h1 className="card-title">Crop Recommendation</h1>
          <p className="card-subtitle">Enter soil & climate parameters to find the best crop for your field.</p>
        </div>

        <form onSubmit={handleSubmit} className="form">
          <div className="form-grid">
            <label className="field">
              <span className="field-label">Temperature (°C)</span>
              <input className="field-input" type="number" placeholder="e.g. 28" value={fields.temperature} onChange={set('temperature')} required />
            </label>
            <label className="field">
              <span className="field-label">Humidity (%)</span>
              <input className="field-input" type="number" placeholder="e.g. 70" value={fields.humidity} onChange={set('humidity')} required />
            </label>
            <label className="field">
              <span className="field-label">Nitrogen (N)</span>
              <input className="field-input" type="number" placeholder="e.g. 90" value={fields.nitrogen} onChange={set('nitrogen')} required />
            </label>
            <label className="field">
              <span className="field-label">Phosphorus (P)</span>
              <input className="field-input" type="number" placeholder="e.g. 50" value={fields.phosphorus} onChange={set('phosphorus')} required />
            </label>
            <label className="field">
              <span className="field-label">Potassium (K)</span>
              <input className="field-input" type="number" placeholder="e.g. 100" value={fields.potassium} onChange={set('potassium')} required />
            </label>
          </div>

          <button className="submit-btn" type="submit" disabled={loading}>
            {loading ? <span className="spinner" /> : 'Predict Crop'}
          </button>
        </form>

        {error  && <div className="result-box result-box--error">{error}</div>}
        {result && (
          <div className="result-box result-box--success fert-result">
            <span className="result-label">Recommended Crop</span>
            <span className="result-value">{result.recommended_crop}</span>
            {result.validation?.length > 0 && (
              <div className="fert-explanation">
                {result.validation.map((line, i) => (
                  <p key={i} className={`fert-line fert-line--${i === 0 ? 'title' : i === 1 ? 'status' : 'reason'}`}>
                    {i === 0 ? '🌱 ' : i === 1 ? '📊 ' : '💡 '}
                    {line}
                  </p>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}