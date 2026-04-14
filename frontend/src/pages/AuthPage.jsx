import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Alert, Spinner } from '../components/Shared'

export default function AuthPage() {
  const [mode, setMode] = useState('login')   // login | register
  const [role, setRole] = useState('student')
  const [form, setForm] = useState({})
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  function set(k) { return e => setForm(f => ({ ...f, [k]: e.target.value })) }

  async function submit(e) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      let data
      if (mode === 'login') {
        data = await api.auth.login({ email: form.email, password: form.password })
      } else {
        data = role === 'student'
          ? await api.auth.registerStudent({ name: form.name, email: form.email, password: form.password, phone: form.phone })
          : await api.auth.registerRecruiter({ name: form.name, email: form.email, password: form.password, phone: form.phone, company: form.company, designation: form.designation, company_url: form.company_url || '' })
      }
      login(data)
      navigate(data.role === 'recruiter' ? '/recruiter/dashboard' : '/student/dashboard')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-logo">
          <div className="wordmark">HireForce</div>
          <div className="tagline">AI-Powered Hiring Platform</div>
        </div>

        <h2 className="auth-title">{mode === 'login' ? 'Welcome back' : 'Create account'}</h2>
        <p className="auth-sub">{mode === 'login' ? 'Sign in to your account' : 'Get started for free'}</p>

        {mode === 'register' && (
          <div className="role-toggle">
            <button className={`role-btn${role === 'student' ? ' active' : ''}`} onClick={() => setRole('student')}>
              🎓 Student
            </button>
            <button className={`role-btn${role === 'recruiter' ? ' active' : ''}`} onClick={() => setRole('recruiter')}>
              💼 Recruiter
            </button>
          </div>
        )}

        {error && <Alert type="error">{error}</Alert>}

        <form onSubmit={submit}>
          {mode === 'register' && (
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input className="form-input" placeholder="John Doe" onChange={set('name')} required />
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Email</label>
            <input className="form-input" type="email" placeholder="you@example.com" onChange={set('email')} required />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input className="form-input" type="password" placeholder="••••••••" onChange={set('password')} required />
          </div>

          {mode === 'register' && (
            <>
              <div className="form-group">
                <label className="form-label">Phone</label>
                <input className="form-input" placeholder="+91 9999999999" onChange={set('phone')} required />
              </div>

              {role === 'recruiter' && (
                <>
                  <div className="form-row">
                    <div className="form-group">
                      <label className="form-label">Company</label>
                      <input className="form-input" placeholder="Acme Corp" onChange={set('company')} required />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Designation</label>
                      <input className="form-input" placeholder="HR Manager" onChange={set('designation')} required />
                    </div>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Company URL</label>
                    <input className="form-input" placeholder="https://acme.com" onChange={set('company_url')} />
                  </div>
                </>
              )}
            </>
          )}

          <button className="btn btn-primary btn-full" type="submit" disabled={busy} style={{ marginTop: 8 }}>
            {busy ? <Spinner /> : mode === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>

        <div className="auth-switch">
          {mode === 'login' ? (
            <>Don't have an account? <button className="auth-link" onClick={() => { setMode('register'); setError('') }}>Sign up</button></>
          ) : (
            <>Already have an account? <button className="auth-link" onClick={() => { setMode('login'); setError('') }}>Sign in</button></>
          )}
        </div>
      </div>
    </div>
  )
}
