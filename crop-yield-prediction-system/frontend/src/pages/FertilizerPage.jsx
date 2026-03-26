import { useState } from 'react'
import './Page.css'

const SOIL_COLORS = ['Black', 'Red', 'Medium Brown', 'Dark Brown', 'Light Brown', 'Sandy']

export default function FertilizerPage() {
  const [fields, setFields] = useState({
    soil_color: '', nitrogen: '', phosphorus: '', potassium: '',
    ph: '', rainfall: '', temperature: ''
  })
  const [result, setResult]   = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  const set = (k) => (e) => setFields(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true); setError(''); setResult('')
    try {
      const res  = await fetch('http://127.0.0.1:5000/fertilizer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          soil_color:  fields.soil_color,
          nitrogen:    Number(fields.nitrogen),
          phosphorus:  Number(fields.phosphorus),
          potassium:   Number(fields.potassium),
          ph:          Number(fields.ph),
          rainfall:    Number(fields.rainfall),
          temperature: Number(fields.temperature),
        }),
      })
      const data = await res.json()
      setResult(data.recommended_fertilizer)
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
          <p className="card-subtitle">Provide soil composition and environment data to get a fertilizer suggestion.</p>
        </div>

        <form onSubmit={handleSubmit} className="form">
          <div className="form-grid">
            <label className="field field--full">
              <span className="field-label">Soil Color</span>
              <select className="field-input" value={fields.soil_color} onChange={set('soil_color')} required>
                <option value="" disabled>Select soil color…</option>
                {SOIL_COLORS.map(c => <option key={c} value={c}>{c}</option>)}
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
              <input className="field-input" type="number" placeholder="e.g. 100" value={fields.potassium} onChange={set('potassium')} required />
            </label>
            <label className="field">
              <span className="field-label">Soil pH</span>
              <input className="field-input" type="number" step="0.1" placeholder="e.g. 6.5" value={fields.ph} onChange={set('ph')} required />
            </label>
            <label className="field">
              <span className="field-label">Rainfall (mm)</span>
              <input className="field-input" type="number" placeholder="e.g. 1000" value={fields.rainfall} onChange={set('rainfall')} required />
            </label>
            <label className="field">
              <span className="field-label">Temperature (°C)</span>
              <input className="field-input" type="number" placeholder="e.g. 25" value={fields.temperature} onChange={set('temperature')} required />
            </label>
          </div>

          <button className="submit-btn" type="submit" disabled={loading}>
            {loading ? <span className="spinner" /> : 'Recommend Fertilizer'}
          </button>
        </form>

        {error  && <div className="result-box result-box--error">{error}</div>}
        {result && (
          <div className="result-box result-box--success">
            <span className="result-label">Recommended Fertilizer</span>
            <span className="result-value">{result}</span>
          </div>
        )}
      </div>
    </div>
  )
}