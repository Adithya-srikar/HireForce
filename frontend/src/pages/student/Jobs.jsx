import { useEffect, useState, useRef } from 'react'
import { api } from '../../api/client'
import { LoadingPage, EmptyState, AtsBar, Alert, Spinner, Modal } from '../../components/Shared'

export default function StudentJobs() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [applying, setApplying] = useState(null)   // job object
  const [msg, setMsg] = useState(null)
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)
  const fileRef = useRef()

  useEffect(() => {
    api.student.getJobs().then(j => setJobs(j || [])).finally(() => setLoading(false))
  }, [])

  async function applyWithFile(file) {
    if (!file || !applying) return
    setBusy(true); setMsg(null)
    try {
      const res = await api.student.applyJob(applying._id, file)
      setResult(res)
      setApplying(null)
    } catch (err) {
      setMsg({ type: 'error', text: err.message })
    } finally { setBusy(false) }
  }

  if (loading) return <LoadingPage />

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Browse Jobs</h1>
        <p className="page-subtitle">{jobs.length} open position{jobs.length !== 1 ? 's' : ''} available.</p>
      </div>

      {result && (
        <Alert type="success">
          ✓ Application submitted! ATS score: <strong>{Math.round(result.ats_score * 100)}%</strong>
          <button className="btn btn-ghost btn-sm" style={{ marginLeft: 10 }} onClick={() => setResult(null)}>Dismiss</button>
        </Alert>
      )}

      {jobs.length === 0 ? (
        <div className="card"><EmptyState icon="💼" title="No jobs available" desc="Check back soon." /></div>
      ) : (
        <div>
          {jobs.map(j => (
            <div key={j._id} className="card card-sm" style={{ marginBottom: 12, display: 'flex', alignItems: 'flex-start', gap: 20 }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                  <strong style={{ fontSize: 15 }}>{j.title}</strong>
                  <span className="badge badge-blue">{j.employment_type || 'full-time'}</span>
                  {j.coding_round && <span className="badge badge-purple">Coding Round</span>}
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 8, lineClamp: 2, WebkitLineClamp: 2, display: '-webkit-box', WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                  {j.description}
                </p>
                <div style={{ display: 'flex', gap: 12, fontSize: 12, color: 'var(--text-dim)' }}>
                  {j.location && <span>📍 {j.location}</span>}
                  {j.salary_range && <span>💰 {j.salary_range}</span>}
                </div>
                {j.skills?.length > 0 && (
                  <div className="chips" style={{ marginTop: 8 }}>
                    {j.skills.map(s => <span key={s} className="chip">{s}</span>)}
                  </div>
                )}
              </div>
              <div style={{ flexShrink: 0 }}>
                <button className="btn btn-primary btn-sm" onClick={() => { setApplying(j); setMsg(null) }}>
                  Apply →
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {applying && (
        <Modal
          title={`Apply – ${applying.title}`}
          onClose={() => setApplying(null)}
        >
          <p style={{ fontSize: 14, color: 'var(--text-muted)', marginBottom: 20 }}>
            Upload a resume for this specific application. It will be ATS-scored against the job description.
          </p>
          {msg && <Alert type={msg.type}>{msg.text}</Alert>}
          <div
            className="upload-zone"
            onClick={() => fileRef.current?.click()}
            onDrop={e => { e.preventDefault(); applyWithFile(e.dataTransfer.files[0]) }}
            onDragOver={e => e.preventDefault()}
          >
            {busy
              ? <><div className="icon"><Spinner /></div><div className="title">Submitting…</div></>
              : <><div className="icon">📄</div><div className="title">Click or drag your PDF resume</div><div className="hint">Scored instantly against this job</div></>
            }
          </div>
          <input ref={fileRef} type="file" accept=".pdf" style={{ display: 'none' }}
            onChange={e => applyWithFile(e.target.files[0])} />
          <div className="modal-footer">
            <button className="btn btn-ghost" onClick={() => setApplying(null)}>Cancel</button>
          </div>
        </Modal>
      )}
    </div>
  )
}
