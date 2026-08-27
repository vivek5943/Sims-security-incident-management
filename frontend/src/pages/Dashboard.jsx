/**
 * MOD-04: Dashboard & Analytics Page
 * KPI summary + Pie (category) + Bar (severity) + Line (trend) charts.
 * Section 8.2 MOD-04: Pie, Bar, Line charts via recharts.
 */
import { useEffect, useState } from 'react'
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip,
  LineChart, Line, ResponsiveContainer, Legend, CartesianGrid
} from 'recharts'
import { AlertTriangle, TrendingUp, ShieldAlert, CheckCircle, Clock, Zap } from 'lucide-react'
import { analyticsAPI } from '../services/api'
import { Spinner, StatCard, PageHeader, EmptyState } from '../components/Common'
import { CHART_COLORS, formatDate } from '../utils/helpers'
import toast from 'react-hot-toast'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs">
      {label && <p className="text-slate-400 mb-1">{label}</p>}
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>{p.name}: {p.value}</p>
      ))}
    </div>
  )
}

export default function DashboardPage() {
  const [summary, setSummary] = useState(null)
  const [trend, setTrend] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const [dashRes, trendRes] = await Promise.all([
          analyticsAPI.dashboard(),
          analyticsAPI.trend(30),
        ])
        setSummary(dashRes.data)
        setTrend(trendRes.data.trend)
      } catch {
        toast.error('Failed to load dashboard data')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <Spinner size="lg" />

  const s = summary?.summary || {}

  // Chart data
  const categoryData = Object.entries(summary?.category_distribution || {}).map(([name, value]) => ({ name, value }))
  const severityData = Object.entries(summary?.severity_distribution || {}).map(([name, value]) => ({ name, value }))
  const statusData = Object.entries(summary?.status_distribution || {}).map(([name, value]) => ({ name, value }))

  return (
    <div>
      <PageHeader
        title="Security Operations Dashboard"
        subtitle="Real-time threat visibility and incident analytics"
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3 mb-6">
        <StatCard label="Total Incidents" value={s.total_incidents} icon={ShieldAlert} color="blue" />
        <StatCard label="Open" value={s.open} icon={Clock} color="amber" />
        <StatCard label="Critical" value={s.critical} icon={AlertTriangle} color="red" />
        <StatCard label="New (7d)" value={s.new_last_7_days} icon={TrendingUp} color="purple" />
        <StatCard label="Resolved" value={s.resolved} icon={CheckCircle} color="green" />
        <StatCard label="ML Confidence" value={s.ml_avg_confidence ? `${s.ml_avg_confidence}%` : '—'} icon={Zap} color="slate" />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
        {/* Category Pie */}
        <div className="card">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Category Distribution</h3>
          {categoryData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={categoryData} cx="50%" cy="50%"
                  innerRadius={55} outerRadius={80}
                  paddingAngle={3} dataKey="value"
                >
                  {categoryData.map((_, i) => (
                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  iconType="circle" iconSize={8}
                  formatter={v => <span className="text-xs text-slate-400">{v}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState title="No category data yet" />
          )}
        </div>

        {/* Severity Bar */}
        <div className="card">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Severity Breakdown</h3>
          {severityData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={severityData} barSize={28}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="value" name="Count" radius={[4, 4, 0, 0]}>
                  {severityData.map((entry, i) => {
                    const c = { Critical: '#ef4444', High: '#f97316', Medium: '#eab308', Low: '#22c55e' }
                    return <Cell key={i} fill={c[entry.name] || '#3b82f6'} />
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState title="No severity data yet" />
          )}
        </div>

        {/* Status Pie */}
        <div className="card">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Status Distribution</h3>
          {statusData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={statusData} cx="50%" cy="50%"
                  outerRadius={80} paddingAngle={2} dataKey="value"
                >
                  {statusData.map((_, i) => (
                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  iconType="circle" iconSize={8}
                  formatter={v => <span className="text-xs text-slate-400">{v}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState title="No status data yet" />
          )}
        </div>
      </div>

      {/* Trend Line Chart */}
      <div className="card">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">
          Incident Creation Trend — Last 30 Days
        </h3>
        {trend.length > 0 ? (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 10, fill: '#94a3b8' }}
                tickFormatter={d => d.slice(5)}
              />
              <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} allowDecimals={false} />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone" dataKey="count" name="Incidents"
                stroke="#3b82f6" strokeWidth={2}
                dot={{ r: 3, fill: '#3b82f6' }}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <EmptyState title="No trend data yet" desc="Create incidents to generate trend data." />
        )}
      </div>
    </div>
  )
}
