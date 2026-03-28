import { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import './Page.css'

const CROPS = ['cotton', 'maize', 'rice', 'soybean', 'sugarcane']

const EMPTY = {
  crop: '', nitrogen: '', phosphorus: '', potassium: '',
  temperature: '', humidity: '', moisture: '', ph: ''
}

export default function FertilizerPage() {
  const location = useLocation()
  const [fields, setFields] = useState(EMPTY)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [prefilled, setPrefilled] = useState(false)

  // Pre-fill from Yield page redirect
  useEffect(() => {
    if (location.state?.prefill) {
      setFields(f => ({ ...f, ...location.state.prefill }))
      setPrefilled(true)
      // Clear router state so refresh doesn't re-prefill
      window.history.replaceState({}, '')
    }
  }, [location.state])

  const set = (k) => (e) => setFields(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true); setError(''); setResult('')
    try {
      const res = await fetch('http://127.0.0.1:5000/fertilizer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          crop: fields.crop,
          nitrogen: Number(fields.nitrogen),
          phosphorus: Number(fields.phosphorus),
          potassium: Number(fields.potassium),
          temperature: Number(fields.temperature),
          humidity: Number(fields.humidity),
          moisture: Number(fields.moisture),
          ph: Number(fields.ph),
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

  return (
    <div className="page-wrapper">
      <div className="card">
        <div className="card-header">
          <span className="card-icon">🧪</span>
          <h1 className="card-title">Fertilizer Recommendation</h1>
          <p className="card-subtitle">
            {prefilled
              ? '✅ Field data carried over from Yield Prediction. Review and submit.'
              : 'Enter crop and field conditions to get a fertilizer suggestion.'}
          </p>
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
            {loading ? <span className="spinner" /> : 'Recommend Fertilizer'}
          </button>
        </form>

        {error && <div className="result-box result-box--error">{error}</div>}
        {result && (
          <div className="result-box result-box--success fert-result">
            <span className="result-label">Recommended Fertilizer</span>
            <span className="result-value">{result.recommended_fertilizer}</span>

            {result.explanation?.length > 0 && (
              <div className="fert-explanation">
                {result.explanation.map((line, i) => (
                  <p
                    key={i}
                    className={`fert-line fert-line--${i === 0 ? 'title' : i === 1 ? 'status' : 'reason'
                      }`}
                  >
                    {/* reduce emoji noise */}
                    {i === 0 && '🧪 '}
                    {i === 1 && '📊 '}
                    {i > 1 && '• '}
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