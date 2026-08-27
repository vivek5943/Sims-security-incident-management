/**
 * SIMS Auth Context — v3
 * FIX-13: ZERO localStorage/sessionStorage token storage.
 *         Only non-sensitive user metadata (name, role) stored in sessionStorage for UI.
 *         JWT tokens live exclusively in HttpOnly server-set cookies.
 */
import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authAPI } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user,    setUser]    = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Restore non-sensitive profile from sessionStorage (name/role for UI rendering)
    // FIX-13: This is NEVER a token — cookies handle auth automatically
    const cached = sessionStorage.getItem('sims_user_meta')
    if (cached) {
      try { setUser(JSON.parse(cached)) } catch { sessionStorage.clear() }
    }

    // Always verify session is still valid via API (cookie will be sent automatically)
    authAPI.getProfile()
      .then(r => {
        const u = r.data
        setUser(u)
        sessionStorage.setItem('sims_user_meta', JSON.stringify(u))
      })
      .catch(() => {
        // No valid cookie session — clear stale UI state
        sessionStorage.removeItem('sims_user_meta')
        setUser(null)
      })
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email, password) => {
    const { data } = await authAPI.login({ email, password })
    // FIX-13: NEVER store tokens — server set HttpOnly cookies already
    // Only store non-sensitive profile for UI rendering
    const meta = data.user
    sessionStorage.setItem('sims_user_meta', JSON.stringify(meta))
    setUser(meta)
    return meta
  }, [])

  const logout = useCallback(async () => {
    try {
      await authAPI.logout()  // Server blacklists refresh token + clears cookies
    } catch {}
    sessionStorage.removeItem('sims_user_meta')
    setUser(null)
  }, [])

  // RBAC helpers (Section 8.1)
  const isAnalyst      = () => user?.role === 'Security Analyst'
  const isManager      = () => user?.role === 'Security Manager'
  const isAdmin        = () => user?.role === 'System Administrator'
  const isManagerOrAbove = () => isManager() || isAdmin()

  return (
    <AuthContext.Provider value={{
      user, loading, login, logout,
      isAnalyst, isManager, isAdmin, isManagerOrAbove,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
