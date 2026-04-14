import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Sidebar from './components/Sidebar'

// Pages
import AuthPage from './pages/AuthPage'
import StudentDashboard from './pages/student/Dashboard'
import StudentProfile from './pages/student/Profile'
import StudentJobs from './pages/student/Jobs'
import StudentApplications from './pages/student/Applications'
import StudentInterviews from './pages/student/Interviews'
import RecruiterDashboard from './pages/recruiter/Dashboard'
import RecruiterJobs from './pages/recruiter/Jobs'
import Applicants from './pages/recruiter/Applicants'

function ProtectedLayout({ role }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  if (role && user.role !== role) {
    return <Navigate to={user.role === 'recruiter' ? '/recruiter/dashboard' : '/student/dashboard'} replace />
  }
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">
        <Routes>
          {role === 'student' ? (
            <>
              <Route path="dashboard" element={<StudentDashboard />} />
              <Route path="profile" element={<StudentProfile />} />
              <Route path="jobs" element={<StudentJobs />} />
              <Route path="applications" element={<StudentApplications />} />
              <Route path="interviews" element={<StudentInterviews />} />
              <Route path="*" element={<Navigate to="dashboard" replace />} />
            </>
          ) : (
            <>
              <Route path="dashboard" element={<RecruiterDashboard />} />
              <Route path="jobs" element={<RecruiterJobs />} />
              <Route path="jobs/:jobId/applicants" element={<Applicants />} />
              <Route path="*" element={<Navigate to="dashboard" replace />} />
            </>
          )}
        </Routes>
      </main>
    </div>
  )
}

function RootRedirect() {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  return <Navigate to={user.role === 'recruiter' ? '/recruiter/dashboard' : '/student/dashboard'} replace />
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<RootRedirect />} />
        <Route path="/login" element={<AuthGate><AuthPage /></AuthGate>} />

        <Route path="/student/*" element={<ProtectedLayout role="student" />} />
        <Route path="/recruiter/*" element={<ProtectedLayout role="recruiter" />} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}

// Redirect already logged-in users away from /login
function AuthGate({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (user) return <Navigate to={user.role === 'recruiter' ? '/recruiter/dashboard' : '/student/dashboard'} replace />
  return children
}
