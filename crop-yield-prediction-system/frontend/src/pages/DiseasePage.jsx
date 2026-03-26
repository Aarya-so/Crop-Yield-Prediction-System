import { useState, useRef } from 'react'
import './Page.css'
import './DiseasePage.css'

export default function DiseasePage() {
  const [preview, setPreview]   = useState(null)
  const [base64, setBase64]     = useState(null)
  const [result, setResult]     = useState(null)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState('')
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef()

  const processFile = (file) => {
    if (!file || !file.type.startsWith('image/')) return
    const reader = new FileReader()
    reader.onload = (e) => {
      setPreview(e.target.result)
      setBase64(e.target.result)
      setResult(null); setError('')
    }
    reader.readAsDataURL(file)
  }

  const onFileChange  = (e) => processFile(e.target.files[0])
  const onDrop        = (e) => { e.preventDefault(); setDragging(false); processFile(e.dataTransfer.files[0]) }
  const onDragOver    = (e) => { e.preventDefault(); setDragging(true) }
  const onDragLeave   = ()  => setDragging(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!base64) return
    setLoading(true); setError(''); setResult(null)
    try {
      const res  = await fetch('http://127.0.0.1:5000/disease', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: base64 }),
      })
      const data = await res.json()
      setResult(data)
    } catch {
      setError('Could not reach the server. Is Flask running?')
    } finally {
      setLoading(false)
    }
  }

  const confidenceColor = (pct) => {
    if (pct >= 80) return '#22c55e'
    if (pct >= 50) return '#f59e0b'
    return '#ef4444'
  }

  return (
    <div className="page-wrapper">
      <div className="card">
        <div className="card-header">
          <span className="card-icon">🔬</span>
          <h1 className="card-title">Disease Prediction</h1>
          <p className="card-subtitle">Upload a photo of a chilli plant leaf to detect diseases.</p>
        </div>

        <form onSubmit={handleSubmit} className="form">
          {/* Drop zone */}
          <div
            className={`drop-zone ${dragging ? 'drop-zone--active' : ''} ${preview ? 'drop-zone--filled' : ''}`}
            onClick={() => inputRef.current.click()}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
          >
            {preview ? (
              <img src={preview} alt="preview" className="drop-preview" />
            ) : (
              <div className="drop-placeholder">
                <span className="drop-icon">📷</span>
                <span className="drop-text">Drag & drop or <u>click to upload</u></span>
                <span className="drop-hint">JPG, PNG, WEBP supported</span>
              </div>
            )}
            <input
              ref={inputRef}
              type="file"
              accept="image/*"
              style={{ display: 'none' }}
              onChange={onFileChange}
            />
          </div>

          {preview && (
            <button
              type="button"
              className="clear-btn"
              onClick={() => { setPreview(null); setBase64(null); setResult(null) }}
            >
              ✕ Remove image
            </button>
          )}

          <button className="submit-btn" type="submit" disabled={!base64 || loading}>
            {loading ? <span className="spinner" /> : 'Analyse Leaf'}
          </button>
        </form>

        {error && <div className="result-box result-box--error">{error}</div>}

        {result && (
          <div className="result-box result-box--success disease-result">
            <span className="result-label">Detected Condition</span>
            <span className="result-value">{result.disease.replace(/_/g, ' ')}</span>
            <div className="confidence-bar-wrap">
              <div
                className="confidence-bar"
                style={{
                  width: `${result.confidence}%`,
                  background: confidenceColor(result.confidence)
                }}
              />
            </div>
            <span className="confidence-label" style={{ color: confidenceColor(result.confidence) }}>
              {result.confidence}% confidence
            </span>
          </div>
        )}
      </div>
    </div>
  )
}