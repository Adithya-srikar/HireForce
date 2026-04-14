import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { LoadingPage, EmptyState, StatusBadge, AtsBar } from '../../components/Shared'
import { Link } from 'react-router-dom'

export default function StudentDashboard() {
  const [profile, setProfile] = useState(null)
  const [jobs, setJobs] = useState([])
  const [apps, setApps] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.student.getProfile().catch(() => null),
      api.student.getJobs().catch(() => []),
      api.student.getInterviews().catch(() => []),
    ]).then(([p, j, i]) => {
      setProfile(p)
      setJobs(j || [])
      setApps(i || [])
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingPage />

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">👋 Welcome back{profile?.name ? `, ${profile.name.split(' ')[0]}` : ''}!</h1>
        <p className="page-subtitle">Here's what's happening with your job search.</p>
      </div>

      <div className="grid-3" style={{ marginBottom: 24 }}>
        <div className="stat-tile">
          <div className="label">Open Jobs</div>
          <div className="value" style={{ color: 'var(--blue)' }}>{jobs.length}</div>
          <div className="trend">Available positions</div>
        </div>
        <div className="stat-tile">
          <div className="label">Interviews</div>
          <div className="value" style={{ color: 'var(--accent-light)' }}>{apps.length}</div>
          <div className="trend">Scheduled</div>
        </div>
        <div className="stat-tile">
          <div className="label">Profile</div>
          <div className="value" style={{ color: 'var(--green)', fontSize: 20, paddingTop: 8 }}>
            {profile?.github ? '✓ GitHub' : '○ GitHub'} &nbsp;
            {profile?.leetcode ? '✓ LC' : '○ LC'}
          </div>
          <div className="trend">Data sources</div>
        </div>
      </div>

      {/* Recent jobs */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2 style={{ fontSize: 16, fontWeight: 600 }}>Recent Jobs</h2>
          <Link to="/student/jobs" className="btn btn-ghost btn-sm">View all →</Link>
        </div>
        {jobs.length === 0 ? (
          <EmptyState icon="💼" title="No jobs yet" desc="Check back soon for new openings." />
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr>
                <th>Title</th><th>Location</th><th>Type</th>
              </tr></thead>
              <tbody>
                {jobs.slice(0, 5).map(j => (
                  <tr key={j._id}>
                    <td><strong>{j.title}</strong></td>
                    <td>{j.location || '—'}</td>
                    <td><span className="badge badge-blue">{j.employment_type || 'full-time'}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Interviews */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2 style={{ fontSize: 16, fontWeight: 600 }}>Upcoming Interviews</h2>
          <Link to="/student/interviews" className="btn btn-ghost btn-sm">View all →</Link>
        </div>
        {apps.length === 0 ? (
          <EmptyState icon="🎤" title="No interviews yet" desc="Apply to jobs to get started." />
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Job</th><th>Date</th><th>Time</th><th>Status</th></tr></thead>
              <tbody>
                {apps.slice(0, 5).map(a => (
                  <tr key={a.interview?.interview_id || a.interview?._id}>
                    <td>{a.job_id}</td>
                    <td>{a.interview?.interview_date || '—'}</td>
                    <td>{a.interview?.interview_time || '—'}</td>
                    <td><span className="badge badge-purple">Scheduled</span></td>
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
