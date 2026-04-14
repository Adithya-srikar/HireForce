// Centralised API client – all calls go through here
const BASE = ''  // proxied by Vite dev server

function getToken() {
  return localStorage.getItem('hf_token')
}

async function req(method, path, body, isForm = false) {
  const headers = {}
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`

  let bodyPayload
  if (body && isForm) {
    const fd = new FormData()
    for (const [k, v] of Object.entries(body)) {
      if (v !== undefined && v !== null) fd.append(k, v)
    }
    bodyPayload = fd
  } else if (body) {
    headers['Content-Type'] = 'application/json'
    bodyPayload = JSON.stringify(body)
  }

  const res = await fetch(BASE + path, { method, headers, body: bodyPayload })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.detail || data.error || 'Request failed')
  return data
}

// ── Auth ──────────────────────────────────────────────────────
export const api = {
  auth: {
    registerStudent: (body) => req('POST', '/auth/register/student', body),
    registerRecruiter: (body) => req('POST', '/auth/register/recruiter', body),
    login: (body) => req('POST', '/auth/login', body),
  },

  // ── Student ─────────────────────────────────────────────────
  student: {
    getProfile: () => req('GET', '/student/profile'),
    updateProfile: (body) => req('PUT', '/student/profile', body),
    uploadResume: (file) => {
      const fd = new FormData()
      fd.append('resume', file)
      return fetch('/student/resume/upload', {
        method: 'POST',
        headers: { Authorization: `Bearer ${getToken()}` },
        body: fd,
      }).then(async r => { const d = await r.json(); if (!r.ok) throw new Error(d.detail || d.error); return d })
    },
    getGitHubConnectUrl: () => req('GET', '/student/github/connect-url'),
    connectLeetcode: (username) =>
      req('POST', '/student/leetcode/connect', { leetcode_username: username }, true),
    getJobs: () => req('GET', '/student/jobs'),
    applyJob: (jobId, file) => {
      const fd = new FormData()
      fd.append('resume', file)
      return fetch(`/student/jobs/${jobId}/apply`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${getToken()}` },
        body: fd,
      }).then(async r => { const d = await r.json(); if (!r.ok) throw new Error(d.detail || d.error); return d })
    },
    getJobStatus: (jobId) => req('GET', `/student/jobs/${jobId}/status`),
    getInterviews: () => req('GET', '/student/interviews'),
    getInterview: (id) => req('GET', `/student/interviews/${id}`),
  },

  // ── Recruiter ────────────────────────────────────────────────
  recruiter: {
    getJobs: () => req('GET', '/recruiter/jobs'),
    createJob: (body) => req('POST', '/recruiter/jobs', body),
    updateJob: (id, body) => req('PUT', `/recruiter/jobs/${id}`, body),
    deleteJob: (id) => req('DELETE', `/recruiter/jobs/${id}`),
    getApplicants: (jobId) => req('GET', `/recruiter/jobs/${jobId}/applicants`),
    scheduleInterview: (jobId, appId, params) =>
      req('POST', `/recruiter/jobs/${jobId}/applicants/${appId}/schedule?interview_date=${params.date}&interview_time=${params.time}`),
    getApplicantGraph: (studentId) => req('GET', `/recruiter/applicants/${studentId}/graph`),
    getReport: (interviewId) => req('GET', `/recruiter/interviews/${interviewId}/report`),
  },
}
