import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { LoadingPage, EmptyState } from '../../components/Shared'

export default function StudentInterviews() {
  const [interviews, setInterviews] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.student.getInterviews().then(d => setInterviews(d || [])).finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingPage />

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">My Interviews</h1>
        <p className="page-subtitle">Upcoming and past AI-powered interviews.</p>
      </div>

      {interviews.length === 0 ? (
        <div className="card">
          <EmptyState icon="🎤" title="No interviews yet" desc="Interviews will appear here once a recruiter schedules one." />
        </div>
      ) : (
        <div>
          {interviews.map(entry => {
            const iv = entry.interview || {}
            return (
              <div key={entry.application_id} className="card" style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ fontWeight: 600, marginBottom: 4 }}>Interview</div>
                    <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 8 }}>
                      📅 {iv.interview_date || '—'} at {iv.interview_time || '—'}
                    </div>
                    <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                      {iv.questions?.length > 0
                        ? `${iv.questions.length} questions prepared`
                        : 'Questions being prepared…'}
                    </div>
                  </div>
                  <a
                    href={`/take-interview?interview_id=${iv._id}`}
                    className="btn btn-primary btn-sm"
                    style={{ pointerEvents: iv.questions?.length ? 'auto' : 'none', opacity: iv.questions?.length ? 1 : 0.45 }}
                  >
                    Start →
                  </a>
                </div>

                {iv.questions?.length > 0 && (
                  <div style={{ marginTop: 16 }}>
                    <hr className="divider" />
                    <div style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Sample Questions</div>
                    <ul style={{ paddingLeft: 18, fontSize: 13, color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: 4 }}>
                      {iv.questions.slice(0, 3).map((q, i) => (
                        <li key={i}>{typeof q === 'string' ? q : q.question || JSON.stringify(q)}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
