/**
 * MOD-02: Incident List Page
 * Filterable, searchable, paginated incident register.
 * DFD Level 1 — Process 2.0 Incident Management Engine view.
 */
import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Search, Filter, ChevronUp, ChevronDown } from 'lucide-react'
import { incidentAPI } from '../../services/api'
import {
  Spinner, PageHeader, SeverityBadge, StatusBadge,
  CategoryBadge, EmptyState
} from '../../components/Common'
import { formatDateTime, truncate } from '../../utils/helpers'
import { useAuth } from '../../contexts/AuthContext'
import toast from 'react-hot-toast'

const STATUSES = ['Open', 'Assigned', 'In Progress', 'Under Investigation', 'Resolved', 'Closed']
const SEVERITIES = ['Critical', 'High', 'Medium', 'Low']
const CATEGORIES = ['Phishing', 'Malware', 'Ransomware', 'DDoS', 'Insider Threat']

export default function IncidentListPage() {
  const [incidents, setIncidents] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ status: '', severity: '', category: '', search: '' })
  const [page, setPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const { isManagerOrAbove } = useAuth()

  const fetchIncidents = useCallback(async () => {
    setLoading(true)
    try {
      const params = { page, page_size: 20 }
      if (filters.status) params.status = filters.status
      if (filters.severity) params.severity = filters.severity
      if (filters.category) params.category = filters.category
      if (filters.search) params.search = filters.search
      const { data } = await incidentAPI.list(params)
      setIncidents(data.results || data)
      setTotalCount(data.count || (data.results || data).length)
    } catch {
      toast.error('Failed to load incidents')
    } finally {
      setLoading(false)
    }
  }, [filters, page])

  useEffect(() => {
    fetchIncidents()
  }, [fetchIncidents])

  const handleFilter = (key, val) => {
    setFilters(p => ({ ...p, [key]: val }))
    setPage(1)
  }

  return (
    <div>
      <PageHeader
        title="Incident Register"
        subtitle={`${totalCount} total incident${totalCount !== 1 ? 's' : ''}`}
        actions={
          <Link to="/incidents/new" className="btn-primary flex items-center gap-2">
            <Plus size={14} /> New Incident
          </Link>
        }
      />

      {/* Filters */}
      <div className="card mb-4">
        <div className="flex flex-wrap gap-3">
          {/* Search */}
          <div className="relative flex-1 min-w-48">
            <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              className="input pl-8 py-2 text-xs"
              placeholder="Search title, category…"
              value={filters.search}
              onChange={e => handleFilter('search', e.target.value)}
            />
          </div>

          {/* Status */}
          <select
            className="input w-auto text-xs py-2"
            value={filters.status}
            onChange={e => handleFilter('status', e.target.value)}
          >
            <option value="">All Statuses</option>
            {STATUSES.map(s => <option key={s}>{s}</option>)}
          </select>

          {/* Severity */}
          <select
            className="input w-auto text-xs py-2"
            value={filters.severity}
            onChange={e => handleFilter('severity', e.target.value)}
          >
            <option value="">All Severities</option>
            {SEVERITIES.map(s => <option key={s}>{s}</option>)}
          </select>

          {/* Category */}
          <select
            className="input w-auto text-xs py-2"
            value={filters.category}
            onChange={e => handleFilter('category', e.target.value)}
          >
            <option value="">All Categories</option>
            {CATEGORIES.map(c => <option key={c}>{c}</option>)}
          </select>
        </div>
      </div>

      {/* Table */}
      {loading ? <Spinner /> : incidents.length === 0 ? (
        <EmptyState
          title="No incidents found"
          desc="Try adjusting filters or create a new incident."
        />
      ) : (
        <div className="card overflow-x-auto p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-left">
                {['ID', 'Title', 'Category', 'Severity', 'Status', 'Assigned To', 'Created'].map(h => (
                  <th key={h} className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {incidents.map((inc, idx) => (
                <tr
                  key={inc.incident_id}
                  className={`border-b border-slate-800/50 hover:bg-slate-800/40 transition-colors ${
                    idx % 2 === 0 ? 'bg-slate-900/30' : ''
                  }`}
                >
                  <td className="px-4 py-3 text-slate-500 font-mono text-xs">
                    #{inc.incident_id}
                  </td>
                  <td className="px-4 py-3 max-w-xs">
                    <Link
                      to={`/incidents/${inc.incident_id}`}
                      className="text-blue-400 hover:text-blue-300 font-medium transition-colors"
                    >
                      {truncate(inc.title, 50)}
                    </Link>
                    {inc.note_count > 0 && (
                      <span className="ml-2 text-xs text-slate-600">{inc.note_count} notes</span>
                    )}
                  </td>
                  <td className="px-4 py-3"><CategoryBadge category={inc.category} /></td>
                  <td className="px-4 py-3"><SeverityBadge severity={inc.severity} /></td>
                  <td className="px-4 py-3"><StatusBadge status={inc.status} /></td>
                  <td className="px-4 py-3 text-xs text-slate-400">
                    {inc.assigned_to?.full_name || <span className="text-slate-600">Unassigned</span>}
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-500">{formatDateTime(inc.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination */}
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-800">
            <p className="text-xs text-slate-500">
              Page {page} · {Math.min(page * 20, totalCount)} of {totalCount}
            </p>
            <div className="flex gap-2">
              <button
                className="btn-secondary py-1 px-3 text-xs" disabled={page <= 1}
                onClick={() => setPage(p => p - 1)}
              >← Prev</button>
              <button
                className="btn-secondary py-1 px-3 text-xs" disabled={page * 20 >= totalCount}
                onClick={() => setPage(p => p + 1)}
              >Next →</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
