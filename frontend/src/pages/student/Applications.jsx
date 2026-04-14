import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { LoadingPage, EmptyState, StatusBadge, AtsBar } from '../../components/Shared'

export default function StudentApplications() {
  const [data, setData] = useState([])
  const [jobs, setJobs] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // We fetch interviews to find applications with scheduled status
    // The backend returns applications-enriched-with-interview from /student/interviews
    // For a full list, we need to combine jobs + status polling
    Promise.all([
      api.student.getJobs().catch(() => []),
      api.student.getInterviews().catch(() => []),
    ]).then(([jobList, interviews]) => {
      const jobMap = {}
      ;(jobList || []).forEach(j => { jobMap[j._id] = j })
      setJobs(jobMap)
      setData(interviews || [])
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingPage />

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">My Applications</h1>
        <p className="page-subtitle">Track all your job applications and their status.</p>
      </div>

      {data.length === 0 ? (
        <div className="card">
          <EmptyState
            icon="📋"
            title="No applications yet"
            desc="Apply to jobs from the Browse Jobs page."
          />
        </div>
      ) : (
        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Job</th>
                  <th>ATS Score</th>
                  <th>Status</th>
                  <th>Interview Date</th>
                </tr>
              </thead>
              <tbody>
                {data.map(a => {
                  const job = jobs[a.job_id]
                  return (
                    <tr key={a.application_id || a.interview?.interview_id}>
                      <td><strong>{job?.title || a.job_id}</strong></td>
                      <td style={{ minWidth: 140 }}>
                        <AtsBar score={a.ats_score || 0} />
                      </td>
                      <td><StatusBadge status={a.status || 'interview_scheduled'} /></td>
                      <td style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                        {a.interview?.interview_date
                          ? `${a.interview.interview_date} ${a.interview.interview_time || ''}`
                          : '—'}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
