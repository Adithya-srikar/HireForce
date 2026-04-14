import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../../api/client'
import { LoadingPage, EmptyState, AtsBar, StatusBadge, Alert, Spinner, Modal } from '../../components/Shared'
import KnowledgeGraph from '../../components/KnowledgeGraph'

export default function Applicants() {
  const { jobId } = useParams()
  const [applicants, setApplicants] = useState([])
  const [loading, setLoading] = useState(true)
  const [scheduling, setScheduling] = useState(null)  // applicant obj
  const [schedForm, setSchedForm] = useState({ date: '', time: '' })
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState(null)
  const [report, setReport] = useState(null)
  const [reportLoading, setReportLoading] = useState(null)
  const [graphData, setGraphData] = useState(null)     // { studentName, graph }
  const [graphLoading, setGraphLoading] = useState(null) // student_id being loaded

  useEffect(() => {
    api.recruiter.getApplicants(jobId)
      .then(a => setApplicants(a || []))
      .finally(() => setLoading(false))
  }, [jobId])

  async function schedule() {
    if (!schedForm.date || !schedForm.time) return
    setBusy(true); setMsg(null)
    try {
      const res = await api.recruiter.scheduleInterview(jobId, scheduling.application_id, {
        date: schedForm.date,
        time: schedForm.time,
      })
      setMsg({ type: 'success', text: `Interview scheduled! Link: ${res.interview_link}` })
      setScheduling(null)
      // refresh
      const updated = await api.recruiter.getApplicants(jobId)
      setApplicants(updated || [])
    } catch (err) {
      setMsg({ type: 'error', text: err.message })
    } finally { setBusy(false) }
  }

  async function viewReport(interview_id) {
    setReportLoading(interview_id)
    try {
      const r = await api.recruiter.getReport(interview_id)
      setReport(r)
    } catch (err) {
      alert(err.message)
    } finally { setReportLoading(null) }
  }

  async function viewGraph(studentId, studentName) {
    setGraphLoading(studentId)
    try {
      const res = await api.recruiter.getApplicantGraph(studentId)
      setGraphData({ studentName: res.student_name || studentName, graph: res.graph })
    } catch (err) {
      alert(err.message)
    } finally { setGraphLoading(null) }
  }

  if (loading) return <LoadingPage />

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Applicants</h1>
        <p className="page-subtitle">{applicants.length} candidate{applicants.length !== 1 ? 's' : ''} – sorted by ATS score</p>
      </div>

      {msg && <Alert type={msg.type}>{msg.text}</Alert>}

      {applicants.length === 0 ? (
        <div className="card"><EmptyState icon="👥" title="No applicants yet" desc="Candidates will appear here once they apply." /></div>
      ) : (
        <div>
          {applicants.map((a, idx) => (
            <div key={a.application_id} className="card card-sm" style={{ marginBottom: 12 }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16 }}>
                <div style={{
                  width: 36, height: 36, borderRadius: '50%', background: 'var(--accent)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: '#fff', fontWeight: 700, fontSize: 14, flexShrink: 0
                }}>
                  {idx + 1}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
                    <div>
                      <strong style={{ fontSize: 15 }}>{a.student.name || 'Unknown'}</strong>
                      <span style={{ marginLeft: 8, fontSize: 13, color: 'var(--text-muted)' }}>{a.student.email}</span>
                    </div>
                    <StatusBadge status={a.status} />
                  </div>
                  <div style={{ display: 'flex', gap: 12, fontSize: 12, color: 'var(--text-muted)', marginBottom: 10 }}>
                    {a.student.phone && <span>📞 {a.student.phone}</span>}
                    {a.student.github && <a href={a.student.github} target="_blank" rel="noreferrer" style={{ color: 'var(--accent-light)', textDecoration: 'none' }}>GitHub ↗</a>}
                    {a.student.linkedin && <a href={a.student.linkedin} target="_blank" rel="noreferrer" style={{ color: 'var(--accent-light)', textDecoration: 'none' }}>LinkedIn ↗</a>}
                    {a.student.leetcode && <a href={a.student.leetcode} target="_blank" rel="noreferrer" style={{ color: 'var(--accent-light)', textDecoration: 'none' }}>LeetCode ↗</a>}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <span style={{ fontSize: 12, color: 'var(--text-dim)', minWidth: 70 }}>ATS Score</span>
                    <div style={{ flex: 1, maxWidth: 200 }}>
                      <AtsBar score={a.ats_score} />
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
                  <button
                    className="btn btn-ghost btn-sm"
                    disabled={graphLoading === a.student.id}
                    onClick={() => viewGraph(a.student.id, a.student.name)}
                    title="View knowledge graph"
                  >
                    {graphLoading === a.student.id ? <Spinner /> : '🕸 Graph'}
                  </button>
                  {a.interview_id ? (
                    <button
                      className="btn btn-ghost btn-sm"
                      disabled={reportLoading === a.interview_id}
                      onClick={() => viewReport(a.interview_id)}
                    >
                      {reportLoading === a.interview_id ? <Spinner /> : 'View Report'}
                    </button>
                  ) : (
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => { setScheduling(a); setSchedForm({ date: '', time: '' }); setMsg(null) }}
                    >
                      Schedule Interview
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Schedule modal */}
      {scheduling && (
        <Modal
          title={`Schedule Interview – ${scheduling.student.name}`}
          onClose={() => setScheduling(null)}
          footer={
            <>
              <button className="btn btn-ghost" onClick={() => setScheduling(null)}>Cancel</button>
              <button className="btn btn-primary" onClick={schedule} disabled={busy}>
                {busy ? <Spinner /> : 'Send Invite'}
              </button>
            </>
          }
        >
          <p style={{ fontSize: 14, color: 'var(--text-muted)', marginBottom: 20 }}>
            An email invite will be sent to <strong>{scheduling.student.email}</strong>.
          </p>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Date</label>
              <input className="form-input" type="date" value={schedForm.date}
                onChange={e => setSchedForm(f => ({ ...f, date: e.target.value }))} />
            </div>
            <div className="form-group">
              <label className="form-label">Time</label>
              <input className="form-input" type="time" value={schedForm.time}
                onChange={e => setSchedForm(f => ({ ...f, time: e.target.value }))} />
            </div>
          </div>
        </Modal>
      )}

      {/* Graph modal */}
      {graphData && (
        <div className="modal-overlay" onClick={e => e.target === e.currentTarget && setGraphData(null)}>
          <div style={{
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-xl)',
            padding: 24,
            width: '100%',
            maxWidth: 960,
            maxHeight: '90vh',
            overflow: 'auto',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div>
                <h2 style={{ fontSize: 18, fontWeight: 600 }}>Knowledge Graph</h2>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 2 }}>
                  {graphData.studentName} · {graphData.graph?.nodes?.length || 0} nodes · {graphData.graph?.edges?.length || 0} edges
                </p>
              </div>
              <button className="modal-close" style={{ fontSize: 20 }} onClick={() => setGraphData(null)}>✕</button>
            </div>
            <KnowledgeGraph graph={graphData.graph} studentName={graphData.studentName} />
          </div>
        </div>
      )}

      {/* Report modal */}
      {report && (
        <Modal title="Interview Report" onClose={() => setReport(null)}>
          <div style={{ fontSize: 13 }}>
            <pre style={{ background: 'var(--surface-2)', padding: 16, borderRadius: 8, overflowX: 'auto', whiteSpace: 'pre-wrap', color: 'var(--text)' }}>
              {JSON.stringify(report.report, null, 2)}
            </pre>
          </div>
        </Modal>
      )}
    </div>
  )
}
