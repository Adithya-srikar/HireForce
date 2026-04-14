import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const studentLinks = [
  { to: '/student/dashboard', icon: '⊞', label: 'Dashboard' },
  { to: '/student/profile', icon: '👤', label: 'Profile' },
  { to: '/student/jobs', icon: '💼', label: 'Browse Jobs' },
  { to: '/student/applications', icon: '📋', label: 'My Applications' },
  { to: '/student/interviews', icon: '🎤', label: 'Interviews' },
]

const recruiterLinks = [
  { to: '/recruiter/dashboard', icon: '⊞', label: 'Dashboard' },
  { to: '/recruiter/jobs', icon: '📢', label: 'My Jobs' },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const links = user?.role === 'recruiter' ? recruiterLinks : studentLinks

  function handleLogout() {
    logout()
    navigate('/login')
  }

  const initials = (user?.role === 'recruiter' ? 'R' : 'S')

  return (
    <nav className="sidebar">
      <div className="sidebar-logo">
        <div>
          <span>HireForce</span>
        </div>
        <div className="sub">AI-Powered Hiring</div>
      </div>

      <div className="nav-section">
        <div className="nav-label">Menu</div>
        {links.map(l => (
          <NavLink
            key={l.to}
            to={l.to}
            className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
          >
            <span className="icon">{l.icon}</span>
            {l.label}
          </NavLink>
        ))}
      </div>

      <div className="sidebar-footer">
        <div className="user-chip">
          <div className="avatar">{initials}</div>
          <div className="user-chip-info">
            <div className="user-chip-name">{user?.role === 'recruiter' ? 'Recruiter' : 'Student'}</div>
            <div className="user-chip-role">{user?.role}</div>
          </div>
        </div>
        <button className="nav-link" style={{ marginTop: 10, color: 'var(--red)' }} onClick={handleLogout}>
          <span className="icon">→</span> Log out
        </button>
      </div>
    </nav>
  )
}
