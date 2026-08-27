/**
 * SIMS App Router
 * React Router v6 — Protected routes with JWT + RBAC enforcement
 * Section 14: Stateless JWT authentication + Role-Based Access Control
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { Layout } from './components/Layout/Sidebar'
import { Spinner } from './components/Common'

// Pages
import LoginPage from './pages/Login'
import DashboardPage from './pages/Dashboard'
import IncidentListPage from './pages/Incidents/IncidentList'
import { IncidentCreatePage, IncidentDetailPage } from './pages/Incidents/IncidentForms'
import {
  MLEnginePage, AnalyticsPage, ReportsPage,
  NotificationsPage, AuditLogsPage, UsersPage
} from './pages/OtherPages'

// ── Auth guard — redirects to /login if not authenticated
function RequireAuth({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <Spinner size="lg" />
  if (!user) return <Navigate to="/login" replace />
  return <Layout>{children}</Layout>
}

// ── Role guard — renders 403 if role check fails
function RequireRole({ children, check }) {
  const auth = useAuth()
  if (check && !check(auth)) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500 flex-col gap-2">
        <p className="text-lg font-semibold text-slate-400">Access Denied</p>
        <p className="text-sm">Insufficient privileges for this resource.</p>
      </div>
    )
  }
  return children
}

function AppRoutes() {
  const { user } = useAuth()
  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <LoginPage />} />

      {/* Protected — all authenticated roles */}
      <Route path="/dashboard" element={
        <RequireAuth><DashboardPage /></RequireAuth>
      } />
      <Route path="/incidents" element={
        <RequireAuth><IncidentListPage /></RequireAuth>
      } />
      <Route path="/incidents/new" element={
        <RequireAuth><IncidentCreatePage /></RequireAuth>
      } />
      <Route path="/incidents/:id" element={
        <RequireAuth><IncidentDetailPage /></RequireAuth>
      } />
      <Route path="/notifications" element={
        <RequireAuth><NotificationsPage /></RequireAuth>
      } />

      {/* Protected — Manager + Admin only */}
      <Route path="/analytics" element={
        <RequireAuth>
          <RequireRole check={a => a.isManagerOrAbove()}>
            <AnalyticsPage />
          </RequireRole>
        </RequireAuth>
      } />
      <Route path="/ml-engine" element={
        <RequireAuth>
          <RequireRole check={a => a.isManagerOrAbove()}>
            <MLEnginePage />
          </RequireRole>
        </RequireAuth>
      } />
      <Route path="/reports" element={
        <RequireAuth>
          <RequireRole check={a => a.isManagerOrAbove()}>
            <ReportsPage />
          </RequireRole>
        </RequireAuth>
      } />
      <Route path="/audit" element={
        <RequireAuth>
          <RequireRole check={a => a.isManagerOrAbove()}>
            <AuditLogsPage />
          </RequireRole>
        </RequireAuth>
      } />

      {/* Protected — System Administrator only */}
      <Route path="/users" element={
        <RequireAuth>
          <RequireRole check={a => a.isAdmin()}>
            <UsersPage />
          </RequireRole>
        </RequireAuth>
      } />

      {/* Default redirect */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: '#1e293b',
              color: '#f1f5f9',
              border: '1px solid #334155',
              fontSize: '13px',
            },
          }}
        />
      </AuthProvider>
    </BrowserRouter>
  )
}
