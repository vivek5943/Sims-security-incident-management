/**
 * SIMS Shared Utilities
 * Badge color maps, label formatters, file download helpers.
 */

export const SEVERITY_COLORS = {
  Critical: 'bg-red-900/50 text-red-400 border border-red-800',
  High:     'bg-orange-900/50 text-orange-400 border border-orange-800',
  Medium:   'bg-yellow-900/50 text-yellow-400 border border-yellow-800',
  Low:      'bg-green-900/50 text-green-400 border border-green-800',
}

export const STATUS_COLORS = {
  'Open':                 'bg-blue-900/50 text-blue-400 border border-blue-800',
  'Assigned':             'bg-purple-900/50 text-purple-400 border border-purple-800',
  'In Progress':          'bg-cyan-900/50 text-cyan-400 border border-cyan-800',
  'Under Investigation':  'bg-amber-900/50 text-amber-400 border border-amber-800',
  'Resolved':             'bg-green-900/50 text-green-400 border border-green-800',
  'Closed':               'bg-slate-700/50 text-slate-400 border border-slate-600',
}

export const CATEGORY_COLORS = {
  Phishing:         'bg-violet-900/50 text-violet-400',
  Malware:          'bg-red-900/50 text-red-400',
  Ransomware:       'bg-rose-900/50 text-rose-400',
  DDoS:             'bg-orange-900/50 text-orange-400',
  'Insider Threat': 'bg-yellow-900/50 text-yellow-400',
}

export const CHART_COLORS = ['#3b82f6', '#ef4444', '#f59e0b', '#22c55e', '#8b5cf6', '#06b6d4']

export const SEVERITY_ORDER = { Critical: 0, High: 1, Medium: 2, Low: 3 }

export function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
  })
}

export function formatDateTime(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  window.URL.revokeObjectURL(url)
}

export function truncate(str, n = 80) {
  if (!str) return ''
  return str.length > n ? str.slice(0, n) + '…' : str
}
