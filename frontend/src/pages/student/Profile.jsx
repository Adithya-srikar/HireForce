import { useEffect, useState, useRef } from 'react'
import { useLocation } from 'react-router-dom'
import { api } from '../../api/client'
import { LoadingPage, Alert, Spinner, Modal } from '../../components/Shared'

export default function StudentProfile() {
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState(null)
  const [lcModal, setLcModal] = useState(false)
  const [lcUser, setLcUser] = useState('')
  const [lcBusy, setLcBusy] = useState(false)
  const [resumeUploading, setResumeUploading] = useState(false)
  const [ghBusy, setGhBusy] = useState(false)
  const fileRef = useRef()
  const location = useLocation()

  useEffect(() => {
    // Show success message if returning from GitHub OAuth callback
    const params = new URLSearchParams(location.search)
    if (params.get('github_connected') === '1') {
      setMsg({ type: 'success', text: '✓ GitHub connected successfully!' })
      // Clean up URL without reloading
      window.history.replaceState({}, '', '/student/profile')
    }
    api.student.getProfile().then(setProfile).finally(() => setLoading(false))
  }, [])

  async function save(e) {
    e.preventDefault()
    setSaving(true); setMsg(null)
    try {
      const fd = new FormData(e.target)
      const updates = Object.fromEntries([...fd.entries()].filter(([,v]) => v))
      await api.student.updateProfile(updates)
      setMsg({ type: 'success', text: 'Profile updated!' })
    } catch (err) {
      setMsg({ type: 'error', text: err.message })
    } finally { setSaving(false) }
  }

  async function uploadResume(file) {
    if (!file) return
    setResumeUploading(true); setMsg(null)
    try {
      const res = await api.student.uploadResume(file)
      setMsg({ type: 'success', text: `Resume uploaded! Detected: ${Object.entries(res.extracted_urls).filter(([,v])=>v).map(([k])=>k).join(', ') || 'no links'}` })
      const updated = await api.student.getProfile()
      setProfile(updated)
    } catch (err) {
      setMsg({ type: 'error', text: err.message })
    } finally { setResumeUploading(false) }
  }

  async function connectLeetcode() {
    if (!lcUser.trim()) return
    setLcBusy(true)
    try {
      await api.student.connectLeetcode(lcUser.trim())
      setMsg({ type: 'success', text: `LeetCode @${lcUser} connected!` })
      setLcModal(false)
      const updated = await api.student.getProfile()
      setProfile(updated)
    } catch (err) {
      setMsg({ type: 'error', text: err.message })
    } finally { setLcBusy(false) }
  }

  async function connectGitHub() {
    setGhBusy(true)
    try {
      const res = await api.student.getGitHubConnectUrl()
      // Redirect the browser to GitHub OAuth (full page navigation)
      window.location.href = res.url
    } catch (err) {
      setMsg({ type: 'error', text: err.message })
      setGhBusy(false)
    }
  }

  if (loading) return <LoadingPage />

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">My Profile</h1>
        <p className="page-subtitle">Manage your personal information and connected accounts.</p>
      </div>

      {msg && <Alert type={msg.type}>{msg.text}</Alert>}

      {/* Basic info */}
      <div className="card" style={{ marginBottom: 16 }}>
        <h2 style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>Basic Information</h2>
        <form onSubmit={save}>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input className="form-input" name="name" defaultValue={profile?.name} placeholder="Your name" />
            </div>
            <div className="form-group">
              <label className="form-label">Phone</label>
              <input className="form-input" name="phone" defaultValue={profile?.phone} placeholder="+91 9999999999" />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">GitHub URL</label>
              <input className="form-input" name="github" defaultValue={profile?.github} placeholder="https://github.com/username" />
            </div>
            <div className="form-group">
              <label className="form-label">LinkedIn URL</label>
              <input className="form-input" name="linkedin" defaultValue={profile?.linkedin} placeholder="https://linkedin.com/in/username" />
            </div>
          </div>
          <button className="btn btn-primary" type="submit" disabled={saving}>
            {saving ? <Spinner /> : 'Save Changes'}
          </button>
        </form>
      </div>

      {/* Resume upload */}
      <div className="card" style={{ marginBottom: 16 }}>
        <h2 style={{ fontSize: 15, fontWeight: 600, marginBottom: 12 }}>Resume</h2>
        {profile?.resume_filename && (
          <div style={{ marginBottom: 12, padding: '10px 14px', background: 'var(--surface-2)', borderRadius: 'var(--radius)', fontSize: 13, color: 'var(--text-muted)' }}>
            📄 Current: <strong style={{ color: 'var(--text)' }}>{profile.resume_filename}</strong>
          </div>
        )}
        <div
          className={`upload-zone${resumeUploading ? ' drag-over' : ''}`}
          onClick={() => fileRef.current?.click()}
          onDragOver={e => { e.preventDefault() }}
          onDrop={e => { e.preventDefault(); uploadResume(e.dataTransfer.files[0]) }}
        >
          {resumeUploading
            ? <><div className="icon"><Spinner /></div><div className="title">Uploading…</div></>
            : <><div className="icon">⬆</div><div className="title">Click or drag PDF to upload</div><div className="hint">We'll auto-extract your GitHub, LinkedIn & LeetCode links</div></>
          }
        </div>
        <input ref={fileRef} type="file" accept=".pdf" style={{ display: 'none' }} onChange={e => uploadResume(e.target.files[0])} />
      </div>

      {/* Connected accounts */}
      <div className="card">
        <h2 style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>Connected Accounts</h2>
        <div className="grid-2">
          <div style={{ background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 600, fontSize: 14 }}>GitHub</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                  {profile?.github ? <span style={{ color: 'var(--green)' }}>✓ Connected – {profile.github.replace('https://github.com/', '@')}</span> : 'Not connected'}
                </div>
              </div>
              <button
                className="btn btn-ghost btn-sm"
                onClick={connectGitHub}
                disabled={ghBusy}
              >
                {ghBusy ? <Spinner /> : profile?.github ? 'Reconnect' : 'Connect'}
              </button>
            </div>
          </div>
          <div style={{ background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 600, fontSize: 14 }}>LeetCode</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                  {profile?.leetcode ? <span style={{ color: 'var(--green)' }}>✓ Connected</span> : 'Not connected'}
                </div>
              </div>
              <button className="btn btn-ghost btn-sm" onClick={() => setLcModal(true)}>
                {profile?.leetcode ? 'Reconnect' : 'Connect'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {lcModal && (
        <Modal
          title="Connect LeetCode"
          onClose={() => setLcModal(false)}
          footer={
            <>
              <button className="btn btn-ghost" onClick={() => setLcModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={connectLeetcode} disabled={lcBusy}>
                {lcBusy ? <Spinner /> : 'Connect'}
              </button>
            </>
          }
        >
          <div className="form-group">
            <label className="form-label">LeetCode Username</label>
            <input className="form-input" placeholder="your_username" value={lcUser} onChange={e => setLcUser(e.target.value)} />
          </div>
        </Modal>
      )}
    </div>
  )
}
