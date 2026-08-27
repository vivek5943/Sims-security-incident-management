/**
 * SIMS Sidebar Navigation & Layout Shell
 * Role-aware nav links (RBAC — Section 8.1)
 */
import { NavLink, useNavigate } from 'react-router-dom'
import {
  Shield, LayoutDashboard, AlertTriangle, BarChart3,
  Bell, FileText, Users, Settings, LogOut, Cpu, ClipboardList
} from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import toast from 'react-hot-toast'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, roles: ['all'] },
  { to: '/incidents', label: 'Incidents', icon: AlertTriangle, roles: ['all'] },
  { to: '/analytics', label: 'Analytics', icon: BarChart3, roles: ['Security Manager', 'System Administrator'] },
  { to: '/ml-engine', label: 'ML Engine', icon: Cpu, roles: ['Security Manager', 'System Administrator'] },
  { to: '/reports', label: 'Reports', icon: FileText, roles: ['Security Manager', 'System Administrator'] },
  { to: '/audit', label: 'Audit Logs', icon: ClipboardList, roles: ['Security Manager', 'System Administrator'] },
  { to: '/users', label: 'Users', icon: Users, roles: ['System Administrator'] },
]

function NavItem({ item, role }) {
  const allowed = item.roles.includes('all') || item.roles.includes(role)
  if (!allowed) return null
  const Icon = item.icon
  return (
    <NavLink
      to={item.to}
      className={({ isActive }) =>
        `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
          isActive
            ? 'bg-blue-600/20 text-blue-400 border border-blue-600/30'
            : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800'
        }`
      }
    >
      <Icon size={16} />
      {item.label}
    </NavLink>
  )
}

export function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    toast.success('Logged out successfully')
    navigate('/login')
  }

  return (
    <aside className="w-60 min-h-screen bg-slate-900 border-r border-slate-800 flex flex-col">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Shield size={16} className="text-white" />
          </div>
          <div>
            <p className="text-sm font-bold text-slate-100">SIMS</p>
            <p className="text-[10px] text-slate-500 leading-none">Security Incident Mgmt</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map(item => (
          <NavItem key={item.to} item={item} role={user?.role} />
        ))}
      </nav>

      {/* User + Logout */}
      <div className="p-3 border-t border-slate-800 space-y-2">
        <NavLink
          to="/notifications"
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
              isActive ? 'bg-blue-600/20 text-blue-400' : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800'
            }`
          }
        >
          <Bell size={16} />
          Notifications
        </NavLink>
        <div className="px-3 py-2 rounded-lg bg-slate-800 border border-slate-700">
          <p className="text-xs font-semibold text-slate-200 truncate">{user?.full_name}</p>
          <p className="text-[10px] text-slate-500 truncate">{user?.role?.role_name || user?.role}</p>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-400
                     hover:text-red-400 hover:bg-red-900/20 transition-colors"
        >
          <LogOut size={14} />
          Sign Out
        </button>
      </div>
    </aside>
  )
}

export function Layout({ children }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto p-6 bg-slate-950">
        {children}
      </main>
    </div>
  )
}
