import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { LoadingPage, EmptyState } from '../../components/Shared'
import { Link } from 'react-router-dom'

export default function RecruiterDashboard() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.recruiter.getJobs().then(j => setJobs(j || [])).finally(() => setLoading(false))
  }, [])

  const open = jobs.filter(j => j.is_open && !j.deleted)
  const closed = jobs.filter(j => !j.is_open || j.deleted)

  if (loading) return <LoadingPage />

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Recruiter Dashboard</h1>
        <p className="page-subtitle">Manage your job postings and review candidates.</p>
      </div>

      <div className="grid-3" style={{ marginBottom: 24 }}>
        <div className="stat-tile">
          <div className="label">Total Jobs</div>
          <div className="value" style={{ color: 'var(--accent-light)' }}>{jobs.length}</div>
          <div className="trend">Posted by you</div>
        </div>
        <div className="stat-tile">
          <div className="label">Open Jobs</div>
          <div className="value" style={{ color: 'var(--green)' }}>{open.length}</div>
          <div className="trend">Accepting applications</div>
        </div>
        <div className="stat-tile">
          <div className="label">Closed</div>
          <div className="value" style={{ color: 'var(--text-muted)' }}>{closed.length}</div>
          <div className="trend">Archived</div>
        </div>
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2 style={{ fontSize: 16, fontWeight: 600 }}>Recent Jobs</h2>
          <Link to="/recruiter/jobs" className="btn btn-primary btn-sm">+ Post Job</Link>
        </div>
        {open.length === 0 ? (
          <EmptyState icon="📢" title="No jobs posted" desc="Post your first job to start receiving applications." />
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Title</th><th>Location</th><th>Type</th><th>Status</th><th></th></tr></thead>
              <tbody>
                {open.slice(0, 8).map(j => (
                  <tr key={j._id}>
                    <td><strong>{j.title}</strong></td>
                    <td style={{ color: 'var(--text-muted)' }}>{j.location || '—'}</td>
                    <td><span className="badge badge-blue">{j.employment_type}</span></td>
                    <td><span className="badge badge-green">Open</span></td>
                    <td>
                      <Link to={`/recruiter/jobs/${j._id}/applicants`} className="btn btn-ghost btn-sm">
                        View Applicants →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
