import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { LoadingPage, EmptyState, Alert, Spinner, Modal } from '../../components/Shared'
import { Link } from 'react-router-dom'

const EMPTY_JOB = { title: '', description: '', requirements: '', location: '', employment_type: 'full-time', salary_range: '', skills: '', coding_round: false }

export default function RecruiterJobs() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState(null)  // null | 'create' | job obj
  const [form, setForm] = useState(EMPTY_JOB)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState(null)

  function load() {
    return api.recruiter.getJobs().then(j => setJobs(j || [])).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  function openCreate() { setForm(EMPTY_JOB); setModal('create'); setMsg(null) }
  function openEdit(j) {
    setForm({ ...j, skills: (j.skills || []).join(', ') })
    setModal(j)
    setMsg(null)
  }

  function set(k) { return e => setForm(f => ({ ...f, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value })) }

  async function save() {
    setBusy(true); setMsg(null)
    try {
      const payload = { ...form, skills: form.skills ? form.skills.split(',').map(s => s.trim()) : [] }
      if (modal === 'create') {
        await api.recruiter.createJob(payload)
      } else {
        await api.recruiter.updateJob(modal._id, payload)
      }
      await load()
      setModal(null)
    } catch (err) {
      setMsg({ type: 'error', text: err.message })
    } finally { setBusy(false) }
  }

  async function remove(id) {
    if (!confirm('Remove this job? It will be soft-deleted.')) return
    try {
      await api.recruiter.deleteJob(id)
      setJobs(js => js.filter(j => j._id !== id))
    } catch (err) { alert(err.message) }
  }

  if (loading) return <LoadingPage />

  const active = jobs.filter(j => j.is_open && !j.deleted)

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 className="page-title">My Jobs</h1>
          <p className="page-subtitle">{active.length} active posting{active.length !== 1 ? 's' : ''}</p>
        </div>
        <button className="btn btn-primary" onClick={openCreate}>+ Post Job</button>
      </div>

      {active.length === 0 ? (
        <div className="card"><EmptyState icon="📢" title="No jobs posted" desc="Click 'Post Job' to create your first posting." /></div>
      ) : (
        <div>
          {active.map(j => (
            <div key={j._id} className="card card-sm" style={{ marginBottom: 12, display: 'flex', alignItems: 'flex-start', gap: 16 }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 4 }}>
                  <strong style={{ fontSize: 15 }}>{j.title}</strong>
                  <span className="badge badge-blue">{j.employment_type}</span>
                  {j.coding_round && <span className="badge badge-purple">Coding</span>}
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 6,
                  display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                  {j.description}
                </p>
                {j.location && <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>📍 {j.location}</span>}
                {j.salary_range && <span style={{ fontSize: 12, color: 'var(--text-dim)', marginLeft: 12 }}>💰 {j.salary_range}</span>}
              </div>
              <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
                <Link to={`/recruiter/jobs/${j._id}/applicants`} className="btn btn-ghost btn-sm">Applicants →</Link>
                <button className="btn btn-ghost btn-sm" onClick={() => openEdit(j)}>Edit</button>
                <button className="btn btn-danger btn-sm" onClick={() => remove(j._id)}>Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {modal !== null && (
        <Modal
          title={modal === 'create' ? 'Post New Job' : 'Edit Job'}
          onClose={() => setModal(null)}
          footer={
            <>
              <button className="btn btn-ghost" onClick={() => setModal(null)}>Cancel</button>
              <button className="btn btn-primary" onClick={save} disabled={busy}>
                {busy ? <Spinner /> : modal === 'create' ? 'Post Job' : 'Save Changes'}
              </button>
            </>
          }
        >
          {msg && <Alert type={msg.type}>{msg.text}</Alert>}
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Job Title *</label>
              <input className="form-input" value={form.title} onChange={set('title')} placeholder="Senior Backend Engineer" required />
            </div>
            <div className="form-group">
              <label className="form-label">Location</label>
              <input className="form-input" value={form.location} onChange={set('location')} placeholder="Remote / Bangalore" />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Job Description *</label>
            <textarea className="form-textarea" value={form.description} onChange={set('description')} placeholder="Describe the role…" rows={4} />
          </div>
          <div className="form-group">
            <label className="form-label">Requirements</label>
            <textarea className="form-textarea" value={form.requirements} onChange={set('requirements')} placeholder="List required skills and experience…" rows={3} />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Employment Type</label>
              <select className="form-select" value={form.employment_type} onChange={set('employment_type')}>
                <option value="full-time">Full-time</option>
                <option value="part-time">Part-time</option>
                <option value="contract">Contract</option>
                <option value="internship">Internship</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Salary Range</label>
              <input className="form-input" value={form.salary_range} onChange={set('salary_range')} placeholder="₹15–25 LPA" />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Skills (comma-separated)</label>
            <input className="form-input" value={form.skills} onChange={set('skills')} placeholder="Python, FastAPI, MongoDB" />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 4 }}>
            <input type="checkbox" id="coding_round" checked={!!form.coding_round} onChange={set('coding_round')} style={{ accentColor: 'var(--accent)' }} />
            <label htmlFor="coding_round" style={{ fontSize: 14, cursor: 'pointer' }}>Include coding round in interview</label>
          </div>
        </Modal>
      )}
    </div>
  )
}
