import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './Page.css'
import './YieldPage.css'

const CROPS = ['cotton', 'maize', 'rice', 'soybean', 'sugarcane']

export default function YieldPage() {
  const navigate = useNavigate()

  const [fields, setFields] = useState({
    crop: '', nitrogen: '', phosphorus: '', potassium: '',
    temperature: '', humidity: '', moisture: '', ph: ''
  })
  const [result, setResult]   = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  const set = (k) => (e) => setFields(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true); setError(''); setResult(null)
    try {
      const res  = await fetch('http://127.0.0.1:5000/yield', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          crop:        fields.crop,
          nitrogen:    Number(fields.nitrogen),
          phosphorus:  Number(fields.phosphorus),
          potassium:   Number(fields.potassium),
          temperature: Number(fields.temperature),
          humidity:    Number(fields.humidity),
          moisture:    Number(fields.moisture),
          ph:          Number(fields.ph),
        }),
      })
      const data = await res.json()
      if (data.error) { setError(data.error); return }
      setResult(data)
    } catch {
      setError('Could not reach the server. Is Flask running?')
    } finally {
      setLoading(false)
    }
  }

  const goToFertilizer = () => {
    navigate('/fertilizer', {
      state: {
        prefill: {
          crop:        fields.crop,
          nitrogen:    fields.nitrogen,
          phosphorus:  fields.phosphorus,
          potassium:   fields.potassium,
          temperature: fields.temperature,
          humidity:    fields.humidity,
          moisture:    fields.moisture,
          ph:          fields.ph,
        }
      }
    })
  }

  const needsFertilizer = result && (result.yield_category === 'Low' || result.yield_category === 'Medium')

  return (
    <div className="page-wrapper">
      <div className="card">
        <div className="card-header">
          <span className="card-icon">📊</span>
          <h1 className="card-title">Yield Prediction</h1>
          <p className="card-subtitle">Enter crop and field conditions to estimate harvest yield.</p>
        </div>

        <form onSubmit={handleSubmit} className="form">
          <div className="form-grid">
            <label className="field field--full">
              <span className="field-label">Crop</span>
              <select className="field-input" value={fields.crop} onChange={set('crop')} required>
                <option value="" disabled>Select a crop…</option>
                {CROPS.map(c => (
                  <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
                ))}
              </select>
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
              <input className="field-input" type="number" placeholder="e.g. 40" value={fields.potassium} onChange={set('potassium')} required />
            </label>
            <label className="field">
              <span className="field-label">Temperature (°C)</span>
              <input className="field-input" type="number" step="0.1" placeholder="e.g. 28" value={fields.temperature} onChange={set('temperature')} required />
            </label>
            <label className="field">
              <span className="field-label">Humidity (%)</span>
              <input className="field-input" type="number" step="0.1" placeholder="e.g. 75" value={fields.humidity} onChange={set('humidity')} required />
            </label>
            <label className="field">
              <span className="field-label">Moisture (%)</span>
              <input className="field-input" type="number" step="0.1" placeholder="e.g. 65" value={fields.moisture} onChange={set('moisture')} required />
            </label>
            <label className="field">
              <span className="field-label">Soil pH</span>
              <input className="field-input" type="number" step="0.01" placeholder="e.g. 6.5" value={fields.ph} onChange={set('ph')} required />
            </label>
          </div>

          <button className="submit-btn" type="submit" disabled={loading}>
            {loading ? <span className="spinner" /> : 'Predict Yield'}
          </button>
        </form>

        {error && <div className="result-box result-box--error">{error}</div>}

        {result && (
          <div className={`result-box result-box--success yield-result ${needsFertilizer ? 'yield-result--has-cta' : ''}`}>
            <div className="yield-main">
              <div className="yield-numeric">
                <span className="result-label">Estimated Yield</span>
                <span className="yield-value">
                  {result.yield_kg_ha.toLocaleString()}
                  <span className="yield-unit"> kg / ha</span>
                </span>
              </div>
              <div className="yield-divider" />
              <div className="yield-category">
                <span className="result-label">Category</span>
                <span className={`yield-badge yield-badge--${result.yield_category.toLowerCase()}`}>
                  {result.yield_category}
                </span>
              </div>
            </div>

            {result.validation?.length > 0 && (
              <div className="fert-explanation">
                {result.validation.map((line, i) => (
                  <p key={i} className={`fert-line fert-line--${i === 0 ? 'title' : i === 1 ? 'status' : 'reason'}`}>
                    {i === 0 ? '📊 ' : i === 1 ? '🎯 ' : '💡 '}
                    {line}
                  </p>
                ))}
              </div>
            )}

            {needsFertilizer && (
              <div className="yield-cta">
                <p className="yield-cta-text">
                  {result.yield_category === 'Low'
                    ? '⚠️ Low yield detected. Fertilizer may help significantly.'
                    : '💡 Yield could be improved with the right fertilizer.'}
                </p>
                <button className="cta-btn" type="button" onClick={goToFertilizer}>
                  Get Fertilizer Recommendation →
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}