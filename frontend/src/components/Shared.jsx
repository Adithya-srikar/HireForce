// Shared small components

export function Spinner() {
  return <span className="spinner" />
}

export function LoadingPage() {
  return (
    <div className="loading-page">
      <span className="spinner" style={{ width: 32, height: 32, borderWidth: 3 }} />
      <span>Loading…</span>
    </div>
  )
}

export function EmptyState({ icon = '📭', title, desc, action }) {
  return (
    <div className="empty-state">
      <div className="icon">{icon}</div>
      <div className="title">{title}</div>
      {desc && <div className="desc">{desc}</div>}
      {action && <div style={{ marginTop: 16 }}>{action}</div>}
    </div>
  )
}

export function Alert({ type = 'error', children }) {
  return <div className={`alert alert-${type}`}>{children}</div>
}

export function AtsBar({ score }) {
  const pct = Math.round((score || 0) * 100)
  const color = pct >= 70 ? 'var(--green)' : pct >= 40 ? 'var(--yellow)' : 'var(--red)'
  return (
    <div className="ats-bar">
      <div className="ats-track">
        <div className="ats-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <div className="ats-label" style={{ color }}>{pct}%</div>
    </div>
  )
}

const STATUS_MAP = {
  applied: { label: 'Applied', cls: 'badge-blue' },
  shortlisted: { label: 'Shortlisted', cls: 'badge-yellow' },
  interview_scheduled: { label: 'Interview', cls: 'badge-purple' },
  rejected: { label: 'Rejected', cls: 'badge-red' },
}

export function StatusBadge({ status }) {
  const s = STATUS_MAP[status] || { label: status, cls: 'badge-gray' }
  return <span className={`badge ${s.cls}`}>{s.label}</span>
}

export function Modal({ title, onClose, children, footer }) {
  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-title">
          {title}
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        {children}
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  )
}
