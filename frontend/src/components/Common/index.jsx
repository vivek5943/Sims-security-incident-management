/**
 * SIMS Shared UI Components
 */
import { Loader2, ShieldAlert, AlertCircle } from 'lucide-react'
import { SEVERITY_COLORS, STATUS_COLORS, CATEGORY_COLORS } from '../../utils/helpers'

export function SeverityBadge({ severity }) {
  if (!severity) return <span className="badge bg-slate-800 text-slate-500">Pending ML</span>
  return (
    <span className={`badge ${SEVERITY_COLORS[severity] || 'bg-slate-700 text-slate-400'}`}>
      {severity}
    </span>
  )
}

export function StatusBadge({ status }) {
  return (
    <span className={`badge ${STATUS_COLORS[status] || 'bg-slate-700 text-slate-400'}`}>
      {status}
    </span>
  )
}

export function CategoryBadge({ category }) {
  if (!category) return <span className="badge bg-slate-800 text-slate-500">Unclassified</span>
  return (
    <span className={`badge ${CATEGORY_COLORS[category] || 'bg-slate-700 text-slate-400'}`}>
      {category}
    </span>
  )
}

export function Spinner({ size = 'md' }) {
  const sz = size === 'lg' ? 32 : size === 'sm' ? 14 : 20
  return (
    <div className="flex items-center justify-center p-8">
      <Loader2 size={sz} className="animate-spin text-blue-500" />
    </div>
  )
}

export function PageHeader({ title, subtitle, actions }) {
  return (
    <div className="flex items-start justify-between mb-6">
      <div>
        <h1 className="text-xl font-bold text-slate-100">{title}</h1>
        {subtitle && <p className="text-sm text-slate-500 mt-0.5">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  )
}

export function StatCard({ label, value, sub, icon: Icon, color = 'blue' }) {
  const colors = {
    blue:   'text-blue-400 bg-blue-900/30',
    red:    'text-red-400 bg-red-900/30',
    amber:  'text-amber-400 bg-amber-900/30',
    green:  'text-green-400 bg-green-900/30',
    purple: 'text-purple-400 bg-purple-900/30',
    slate:  'text-slate-400 bg-slate-800',
  }
  return (
    <div className="card flex items-center gap-4">
      {Icon && (
        <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${colors[color]}`}>
          <Icon size={20} className={colors[color].split(' ')[0]} />
        </div>
      )}
      <div>
        <p className="text-2xl font-bold text-slate-100">{value ?? '—'}</p>
        <p className="text-xs text-slate-500 font-medium">{label}</p>
        {sub && <p className="text-xs text-slate-600 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

export function EmptyState({ icon: Icon = ShieldAlert, title, desc }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <Icon size={40} className="text-slate-700 mb-3" />
      <p className="text-slate-400 font-semibold">{title}</p>
      {desc && <p className="text-sm text-slate-600 mt-1 max-w-xs">{desc}</p>}
    </div>
  )
}

export function ErrorMessage({ message }) {
  return (
    <div className="flex items-center gap-2 p-3 rounded-lg bg-red-900/30 border border-red-800 text-red-400 text-sm">
      <AlertCircle size={14} />
      {message}
    </div>
  )
}

export function ConfidenceBar({ score }) {
  const pct = Math.min(100, Math.max(0, Number(score) || 0))
  const color = pct >= 80 ? 'bg-green-500' : pct >= 60 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-slate-800 rounded-full h-1.5">
        <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-400 w-10 text-right">{pct}%</span>
    </div>
  )
}
