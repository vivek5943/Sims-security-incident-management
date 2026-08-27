/**
 * SIMS Login Page
 * FIX-02: No localStorage for tokens — cookies set by server
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, Eye, EyeOff, Lock, Mail } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const [form, setForm] = useState({ email: '', password: '' })
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(form.email, form.password)
      toast.success('Authentication successful')
      navigate('/dashboard')
    } catch (err) {
      const msg = err.response?.status === 429
        ? 'Too many login attempts. Please wait before trying again.'
        : err.response?.data?.detail || 'Invalid credentials. Please try again.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex w-16 h-16 bg-blue-600/20 border border-blue-600/30 rounded-2xl items-center justify-center mb-4">
            <Shield size={28} className="text-blue-400" />
          </div>
          <h1 className="text-2xl font-bold text-slate-100">SIMS</h1>
          <p className="text-sm text-slate-500 mt-1">AI-Powered Security Incident Management System</p>
          <p className="text-xs text-slate-700 mt-1">MCSP-232 | IGNOU MCA Project</p>
        </div>

        <div className="card border-slate-800">
          <h2 className="text-base font-semibold text-slate-200 mb-5">Secure Authentication</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Email Address</label>
              <div className="relative">
                <Mail size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input type="email" className="input pl-9" placeholder="your@email.com"
                  value={form.email} onChange={e => setForm(p => ({ ...p, email: e.target.value }))} required />
              </div>
            </div>
            <div>
              <label className="label">Password</label>
              <div className="relative">
                <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input type={showPw ? 'text' : 'password'} className="input pl-9 pr-10" placeholder="••••••••"
                  value={form.password} onChange={e => setForm(p => ({ ...p, password: e.target.value }))} required />
                <button type="button" onClick={() => setShowPw(p => !p)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300">
                  {showPw ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
            </div>
            {error && (
              <p className="text-xs text-red-400 bg-red-900/20 border border-red-800 rounded-lg px-3 py-2">{error}</p>
            )}
            <button type="submit" className="btn-primary w-full py-3" disabled={loading}>
              {loading ? 'Authenticating…' : 'Sign In'}
            </button>
          </form>

          <div className="mt-5 pt-4 border-t border-slate-800">
            <p className="text-xs text-slate-600 mb-2 font-semibold uppercase tracking-wide">Demo Credentials</p>
            <div className="space-y-1 text-xs text-slate-500">
              <div className="flex justify-between"><span>admin@sims.local</span><span className="text-slate-600">System Administrator</span></div>
              <div className="flex justify-between"><span>manager@sims.local</span><span className="text-slate-600">Security Manager</span></div>
              <div className="flex justify-between"><span>analyst1@sims.local</span><span className="text-slate-600">Security Analyst</span></div>
              <p className="text-slate-700 mt-1">Passwords: Admin@1234 / Manager@1234 / Analyst@1234</p>
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-slate-700 mt-6">
          JWT in HttpOnly cookies · PBKDF2-SHA256 hashing · Rate-limited (10/min) · RBAC enforced
        </p>
      </div>
    </div>
  )
}
