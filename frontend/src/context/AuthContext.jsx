import { createContext, useContext, useState, useEffect } from 'react'

const AuthCtx = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const stored = localStorage.getItem('hf_user')
    if (stored) {
      try { setUser(JSON.parse(stored)) } catch {}
    }
    setLoading(false)
  }, [])

  function login(tokenData) {
    // tokenData: { access_token, user_id, role }
    localStorage.setItem('hf_token', tokenData.access_token)
    const u = { id: tokenData.user_id, role: tokenData.role }
    localStorage.setItem('hf_user', JSON.stringify(u))
    setUser(u)
  }

  function logout() {
    localStorage.removeItem('hf_token')
    localStorage.removeItem('hf_user')
    setUser(null)
  }

  return (
    <AuthCtx.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthCtx.Provider>
  )
}

export function useAuth() {
  return useContext(AuthCtx)
}
