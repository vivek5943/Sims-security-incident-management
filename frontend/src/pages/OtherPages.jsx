/**
 * SIMS Other Pages — v3
 * FIX-11: Severity caveat displayed near prediction
 * FIX-12: "Model Confidence" label, not "Accuracy" or "Probability"
 * FIX-04: Account lockout display (Users page)
 */
import { useState, useEffect } from 'react'
import {
  Cpu, RefreshCw, Download, FileText, File, Bell,
  ClipboardList, Users as UsersIcon, UserPlus, Check,
  BellOff, AlertCircle, Lock, Unlock, Info
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, LineChart, Line, Legend
} from 'recharts'
import { mlAPI, analyticsAPI, reportAPI, notifAPI, auditAPI, authAPI } from '../services/api'
import {
  Spinner, PageHeader, EmptyState, ConfidenceBar,
  SeverityBadge, CategoryBadge, StatusBadge, StatCard
} from '../components/Common'
import { formatDateTime, formatDate, downloadBlob, CHART_COLORS } from '../utils/helpers'
import toast from 'react-hot-toast'

// ── ML Engine Page ─────────────────────────────────────────────────────────────
export function MLEnginePage() {
  const [modelStatus, setModelStatus] = useState(null)
  const [training,    setTraining]    = useState(false)
  const [testText,    setTestText]    = useState('')
  const [result,      setResult]      = useState(null)
  const [classifying, setClassifying] = useState(false)
  const [loading,     setLoading]     = useState(true)

  useEffect(() => {
    mlAPI.status().then(r => setModelStatus(r.data)).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const handleTrain = async () => {
    setTraining(true)
    try {
      const { data } = await mlAPI.train()
      toast.success(`Models trained! Category: ${data.metadata?.category_model}`)
      const s = await mlAPI.status()
      setModelStatus(s.data)
    } catch { toast.error('Training failed. Check server logs.') }
    finally { setTraining(false) }
  }

  const handleClassify = async () => {
    if (!testText.trim() || testText.length < 10) return
    setClassifying(true)
    try {
      const { data } = await mlAPI.classify(testText)
      setResult(data)
    } catch { toast.error('Classification failed') }
    finally { setClassifying(false) }
  }

  if (loading) return <Spinner />

  return (
    <div className="max-w-4xl">
      <PageHeader
        title="ML Classification Engine"
        subtitle="NLP pipeline → TF-IDF → cross-validated Scikit-Learn classifiers"
        actions={
          <button onClick={handleTrain} disabled={training} className="btn-primary flex items-center gap-2">
            <RefreshCw size={14} className={training ? 'animate-spin' : ''} />
            {training ? 'Training…' : 'Train Models'}
          </button>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        {/* Model Status */}
        <div className="card">
          <h3 className="text-xs font-semibold text-slate-500 uppercase mb-3 flex items-center gap-2">
            <Cpu size={12} className="text-blue-400" /> Model Status
          </h3>
          {modelStatus?.models_trained ? (
            <div className="space-y-2 text-xs">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-2 h-2 rounded-full bg-green-400" />
                <span className="text-green-400 font-semibold">
                  {modelStatus.inference_mode}
                </span>
              </div>
              {[
                ['Category Model',   modelStatus.metadata?.category_model],
                ['Category F1',      modelStatus.metadata?.category_f1],
                ['Severity Model',   modelStatus.metadata?.severity_model],
                ['Severity F1',      modelStatus.metadata?.severity_f1],
                ['Calibrated',       modelStatus.metadata?.calibrated ? 'Yes (isotonic)' : 'No'],
                ['Train Samples',    modelStatus.metadata?.training_samples],
                ['Samples/Category', modelStatus.metadata?.samples_per_category],
                ['TF-IDF Features',  modelStatus.metadata?.tfidf_features],
                ['ngram range',      modelStatus.metadata?.tfidf_ngram_range],
                ['Predictions Made', modelStatus.prediction_count],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between border-b border-slate-800 pb-1">
                  <span className="text-slate-500">{k}</span>
                  <span className="text-slate-300 font-medium">{v ?? '—'}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-amber-400" />
                <span className="text-amber-400 text-xs font-semibold">Heuristic Baseline Active</span>
              </div>
              <p className="text-xs text-slate-500">
                No trained models found. Click "Train Models" to train and serialize
                two calibrated Scikit-Learn classifiers (category + severity).
              </p>
            </div>
          )}
        </div>

        {/* Pipeline Architecture */}
        <div className="card">
          <h3 className="text-xs font-semibold text-slate-500 uppercase mb-3">Pipeline Architecture</h3>
          <div className="space-y-2 text-xs">
            {[
              ['Step 1', 'Data Cleaning',       'Regex strips HTML, URLs, numbers, punctuation'],
              ['Step 2', 'Tokenization',         'Text split into individual token arrays'],
              ['Step 3', 'Stopword Removal',     'Context-less high-freq terms filtered'],
              ['Step 4', 'Lemmatization',        '"attacking" → "attack" (WordNetLemmatizer)'],
              ['Step 5', 'TF-IDF Vectorization', 'Text → numerical feature matrices (1-3 ngrams)'],
              ['Step 6', 'Cross-Validation',     '5-fold StratifiedKFold, macro F1 scoring'],
              ['Step 7', 'Calibration',          'CalibratedClassifierCV isotonic regression'],
            ].map(([step, title, desc]) => (
              <div key={step} className="flex gap-3">
                <span className="text-blue-500 font-mono w-12 shrink-0">{step}</span>
                <div>
                  <span className="text-slate-300 font-medium">{title}</span>
                  <span className="text-slate-600 ml-2">{desc}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Caveats — FIX-11, FIX-12 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <div className="card border-amber-900/30">
          <div className="flex items-start gap-2">
            <Info size={12} className="text-amber-400 mt-0.5 shrink-0" />
            <div>
              <p className="text-xs font-semibold text-amber-400 mb-1">FIX-11: Severity Estimation Caveat</p>
              <p className="text-xs text-amber-300/70 leading-relaxed">
                Severity is a <strong>text-based ML estimate</strong> to assist triage.
                It cannot account for asset criticality, business impact, or exposure scope.
                All High/Critical severity incidents require human analyst review before escalation.
              </p>
            </div>
          </div>
        </div>
        <div className="card border-blue-900/30">
          <div className="flex items-start gap-2">
            <Info size={12} className="text-blue-400 mt-0.5 shrink-0" />
            <div>
              <p className="text-xs font-semibold text-blue-400 mb-1">FIX-12: Model Confidence Note</p>
              <p className="text-xs text-blue-300/70 leading-relaxed">
                Confidence scores are <strong>calibrated isotonic regression</strong> outputs
                (CalibratedClassifierCV), not raw probabilities. They indicate relative model
                certainty — not guaranteed correctness. Label as "Model Confidence" not "Accuracy".
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Live Test */}
      <div className="card">
        <h3 className="text-xs font-semibold text-slate-500 uppercase mb-3">Live Classification Test</h3>
        <div className="space-y-3">
          <textarea
            className="input resize-none text-xs" rows={4}
            placeholder="Paste an incident description to test the ML pipeline…"
            value={testText}
            onChange={e => setTestText(e.target.value)}
          />
          <button
            onClick={handleClassify}
            disabled={classifying || testText.length < 10}
            className="btn-primary flex items-center gap-2 text-xs"
          >
            <Cpu size={12} />
            {classifying ? 'Running inference…' : 'Run ML Inference'}
          </button>

          {result && (
            <div className="bg-slate-800 rounded-lg p-4 space-y-3">
              {/* FIX-15: Show whether trained ML or heuristic */}
              <div className={`flex items-center gap-2 text-xs px-2 py-1 rounded ${
                result.is_trained_model
                  ? 'bg-green-900/30 text-green-400'
                  : 'bg-amber-900/30 text-amber-400'
              }`}>
                <div className="w-1.5 h-1.5 rounded-full bg-current" />
                {result.is_trained_model
                  ? `Scikit-Learn Trained Classifier — ${result.classification?.model}`
                  : 'Heuristic Baseline (run train_ml_model for real ML)'}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <p className="text-xs text-slate-500 mb-1">Category</p>
                  <CategoryBadge category={result.classification?.category} />
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">Severity</p>
                  <SeverityBadge severity={result.classification?.severity} />
                </div>
              </div>

              {/* FIX-12: Labelled as "Model Confidence" */}
              <div>
                <p className="text-xs text-slate-500 mb-1.5">
                  Model Confidence
                  <span className="text-slate-600 ml-1">(not prediction accuracy — see FIX-12)</span>
                </p>
                <ConfidenceBar score={result.classification?.confidence} />
              </div>

              {result.classification?.recommendations && (
                <div className="bg-amber-900/20 border border-amber-800/30 rounded-lg p-3">
                  <p className="text-xs font-semibold text-amber-400 mb-1">Recommended Action</p>
                  <p className="text-xs text-amber-300/80">{result.classification.recommendations}</p>
                </div>
              )}

              {/* FIX-11: Severity caveat always shown */}
              {result.classification?.severity_caveat && (
                <div className="flex items-start gap-2 bg-slate-900 rounded p-2">
                  <Info size={10} className="text-slate-500 mt-0.5 shrink-0" />
                  <p className="text-xs text-slate-600">{result.classification.severity_caveat}</p>
                </div>
              )}

              {result.warning && (
                <p className="text-xs text-amber-500 bg-amber-900/20 rounded p-2">{result.warning}</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Analytics Page ────────────────────────────────────────────────────────────
export function AnalyticsPage() {
  const [catData, setCatData] = useState(null)
  const [perf,    setPerf]    = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([analyticsAPI.categories(), analyticsAPI.performance()])
      .then(([c, p]) => { setCatData(c.data); setPerf(p.data.analyst_performance) })
      .catch(() => toast.error('Failed to load analytics'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />

  const categoryData = catData?.category_totals?.map(c => ({ name: c.category, value: c.total })) || []

  return (
    <div>
      <PageHeader title="Security Analytics" subtitle="Threat intelligence and operational metrics" />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <div className="card">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Incidents by Category</h3>
          {categoryData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={categoryData} layout="vertical" barSize={16}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 9, fill: '#94a3b8' }} width={120} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', fontSize: 11 }} />
                <Bar dataKey="value" name="Total" fill="#3b82f6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyState title="No category data yet" />}
        </div>
        <div className="card">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Analyst Resolution Rates</h3>
          {perf.length > 0 ? (
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {perf.map(a => (
                <div key={a.analyst_id} className="bg-slate-800 rounded-lg p-3">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-slate-200 font-medium">{a.full_name}</span>
                    <span className="text-xs text-slate-500">{a.resolved}/{a.assigned} resolved</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-slate-700 rounded-full h-1.5">
                      <div className="h-1.5 rounded-full bg-blue-500" style={{ width: `${a.resolution_rate}%` }} />
                    </div>
                    <span className="text-xs text-slate-400">{a.resolution_rate}%</span>
                  </div>
                </div>
              ))}
            </div>
          ) : <EmptyState title="No analyst data yet" />}
        </div>
      </div>
    </div>
  )
}

// ── Reports Page ──────────────────────────────────────────────────────────────
export function ReportsPage() {
  const [downloading, setDownloading] = useState('')

  const handle = async (type) => {
    setDownloading(type)
    try {
      let res, fn
      if (type === 'pdf')   { res = await reportAPI.downloadPDF();      fn = `SIMS_Report_${Date.now()}.pdf` }
      if (type === 'csv')   { res = await reportAPI.downloadCSV();      fn = `SIMS_Incidents_${Date.now()}.csv` }
      if (type === 'audit') { res = await reportAPI.downloadAuditCSV(); fn = `SIMS_Audit_${Date.now()}.csv` }
      downloadBlob(res.data, fn)
      toast.success(`${fn} downloaded`)
    } catch { toast.error('Download failed') }
    finally { setDownloading('') }
  }

  const reports = [
    { type: 'pdf',   icon: FileText,    color: 'text-red-400',   title: 'Incident Report (PDF)',       desc: 'Executive summary + incident table via ReportLab. MOD-07.' },
    { type: 'csv',   icon: File,        color: 'text-green-400', title: 'Incident Export (CSV)',        desc: 'Full incident + ML prediction data export for analysis.' },
    { type: 'audit', icon: ClipboardList, color: 'text-blue-400', title: 'Audit Log Export (CSV)',     desc: 'Compliance audit trail CSV. GDPR / ISO 27001. Admin only.' },
  ]

  return (
    <div className="max-w-3xl">
      <PageHeader title="Reporting Core" subtitle="PDF + CSV exports — MOD-07" />
      <div className="space-y-3">
        {reports.map(r => {
          const Icon = r.icon
          return (
            <div key={r.type} className="card flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-slate-800 rounded-xl flex items-center justify-center">
                  <Icon size={18} className={r.color} />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-200">{r.title}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{r.desc}</p>
                </div>
              </div>
              <button onClick={() => handle(r.type)} disabled={!!downloading}
                className="btn-primary flex items-center gap-2 text-xs whitespace-nowrap">
                <Download size={12} />
                {downloading === r.type ? 'Generating…' : 'Download'}
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Notifications Page ─────────────────────────────────────────────────────────
export function NotificationsPage() {
  const [notifs,  setNotifs]  = useState([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    notifAPI.list().then(r => setNotifs(r.data.results || r.data)).finally(() => setLoading(false))
  }
  useEffect(load, [])

  if (loading) return <Spinner />
  return (
    <div className="max-w-2xl">
      <PageHeader
        title="Notifications"
        subtitle="Incident lifecycle event alerts — MOD-05"
        actions={
          <button onClick={() => notifAPI.markAllRead().then(load)}
            className="btn-secondary flex items-center gap-2 text-xs">
            <Check size={12} /> Mark All Read
          </button>
        }
      />
      {notifs.length === 0
        ? <EmptyState icon={BellOff} title="No notifications" desc="Alerts appear here on incident events." />
        : (
          <div className="space-y-2">
            {notifs.map(n => (
              <div key={n.notification_id}
                className={`card flex items-start justify-between gap-3 ${n.status === 'Unread' ? 'border-blue-900/50' : 'opacity-60'}`}>
                <div className="flex items-start gap-3">
                  <div className={`mt-1 w-2 h-2 rounded-full shrink-0 ${n.status === 'Unread' ? 'bg-blue-400' : 'bg-slate-700'}`} />
                  <div>
                    <p className="text-sm text-slate-300">{n.message}</p>
                    <p className="text-xs text-slate-600 mt-1">{formatDateTime(n.timestamp)}</p>
                  </div>
                </div>
                {n.status === 'Unread' && (
                  <button onClick={() => notifAPI.markRead(n.notification_id).then(load)}
                    className="text-xs text-slate-500 hover:text-slate-300 shrink-0">
                    Mark read
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
    </div>
  )
}

// ── Audit Logs Page ────────────────────────────────────────────────────────────
export function AuditLogsPage() {
  const [logs,    setLogs]    = useState([])
  const [loading, setLoading] = useState(true)
  const [page,    setPage]    = useState(1)
  const [total,   setTotal]   = useState(0)
  const [search,  setSearch]  = useState('')

  const load = () => {
    setLoading(true)
    auditAPI.list({ page, search })
      .then(r => { setLogs(r.data.results || r.data); setTotal(r.data.count || 0) })
      .catch(() => toast.error('Failed to load audit logs'))
      .finally(() => setLoading(false))
  }
  useEffect(load, [page, search])

  return (
    <div>
      <PageHeader title="Audit Log Ledger" subtitle={`${total} total entries — MOD-06`} />
      <div className="card mb-4">
        <input type="text" className="input text-xs" placeholder="Search actions, emails…"
          value={search} onChange={e => { setSearch(e.target.value); setPage(1) }} />
      </div>
      {loading ? <Spinner /> : (
        <div className="card p-0 overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-slate-800">
                {['Log ID','User','Action','IP','Timestamp'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-slate-500 font-semibold uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {logs.map((log, i) => (
                <tr key={log.log_id} className={`border-b border-slate-800/50 ${i%2===0?'bg-slate-900/30':''}`}>
                  <td className="px-4 py-2.5 text-slate-600 font-mono">#{log.log_id}</td>
                  <td className="px-4 py-2.5 text-slate-400">{log.user?.email || 'System'}</td>
                  <td className="px-4 py-2.5 text-slate-300 font-mono max-w-sm truncate">{log.action}</td>
                  <td className="px-4 py-2.5 text-slate-600">{log.ip_address || '—'}</td>
                  <td className="px-4 py-2.5 text-slate-500">{formatDateTime(log.timestamp)}</td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr><td colSpan={5} className="px-4 py-10 text-center text-slate-600">No entries found.</td></tr>
              )}
            </tbody>
          </table>
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-800">
            <p className="text-xs text-slate-500">Page {page} · {total} total</p>
            <div className="flex gap-2">
              <button className="btn-secondary py-1 px-3 text-xs" disabled={page<=1} onClick={() => setPage(p=>p-1)}>← Prev</button>
              <button className="btn-secondary py-1 px-3 text-xs" disabled={page*20>=total} onClick={() => setPage(p=>p+1)}>Next →</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Users Management Page ──────────────────────────────────────────────────────
export function UsersPage() {
  const [users,      setUsers]      = useState([])
  const [loading,    setLoading]    = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [form,       setForm]       = useState({ full_name:'', email:'', password:'', role_id:'' })
  const [roles,      setRoles]      = useState([])
  const [creating,   setCreating]   = useState(false)

  const load = () => {
    Promise.all([authAPI.getUsers(), authAPI.getRoles()])
      .then(([u, r]) => { setUsers(u.data.results || u.data); setRoles(r.data.results || r.data) })
      .finally(() => setLoading(false))
  }
  useEffect(load, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    setCreating(true)
    try {
      await authAPI.createUser(form)
      toast.success(`User ${form.email} created`)
      setShowCreate(false)
      setForm({ full_name:'', email:'', password:'', role_id:'' })
      load()
    } catch (err) {
      toast.error(err.response?.data?.email?.[0] || 'Failed to create user')
    } finally { setCreating(false) }
  }

  const handleStatusToggle = async (u) => {
    const newStatus = u.status === 'Active' ? 'Inactive' : 'Active'
    try {
      await authAPI.updateUser(u.user_id, { status: newStatus })
      toast.success(`${u.full_name} → ${newStatus}`)
      load()
    } catch { toast.error('Update failed') }
  }

  // FIX-04: Unlock account button
  const handleUnlock = async (u) => {
    try {
      await authAPI.unlockUser(u.user_id)
      toast.success(`${u.full_name} account unlocked`)
      load()
    } catch { toast.error('Unlock failed') }
  }

  if (loading) return <Spinner />

  return (
    <div>
      <PageHeader
        title="User Management"
        subtitle={`${users.length} registered users — System Administrator`}
        actions={
          <button onClick={() => setShowCreate(p=>!p)} className="btn-primary flex items-center gap-2 text-xs">
            <UserPlus size={12} /> {showCreate ? 'Cancel' : 'New User'}
          </button>
        }
      />

      {showCreate && (
        <div className="card mb-4 max-w-lg">
          <h3 className="text-xs font-semibold text-slate-400 uppercase mb-3">Provision New User</h3>
          <form onSubmit={handleCreate} className="space-y-3">
            {[{k:'full_name',l:'Full Name',t:'text'},{k:'email',l:'Email',t:'email'},{k:'password',l:'Password (min 8)',t:'password'}].map(f => (
              <div key={f.k}>
                <label className="label">{f.l}</label>
                <input type={f.t} className="input text-xs" value={form[f.k]}
                  onChange={e => setForm(p=>({...p,[f.k]:e.target.value}))} required />
              </div>
            ))}
            <div>
              <label className="label">Role</label>
              <select className="input text-xs" value={form.role_id}
                onChange={e => setForm(p=>({...p,role_id:e.target.value}))} required>
                <option value="">— Select Role —</option>
                {roles.map(r => <option key={r.role_id} value={r.role_id}>{r.role_name}</option>)}
              </select>
            </div>
            <button type="submit" disabled={creating} className="btn-primary text-xs">
              {creating ? 'Creating…' : 'Create User'}
            </button>
          </form>
        </div>
      )}

      <div className="card p-0 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-800">
              {['ID','Name','Email','Role','Status','Created','Actions'].map(h => (
                <th key={h} className="px-4 py-3 text-left text-xs text-slate-500 font-semibold uppercase tracking-wide">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {users.map((u, i) => (
              <tr key={u.user_id} className={`border-b border-slate-800/50 ${i%2===0?'bg-slate-900/30':''}`}>
                <td className="px-4 py-3 text-slate-600 font-mono text-xs">#{u.user_id}</td>
                <td className="px-4 py-3 text-slate-200 font-medium text-sm">{u.full_name}</td>
                <td className="px-4 py-3 text-slate-400 text-xs">{u.email}</td>
                <td className="px-4 py-3">
                  <span className="badge bg-slate-800 text-slate-400 text-xs">{u.role?.role_name}</span>
                </td>
                <td className="px-4 py-3">
                  <span className={`badge text-xs ${
                    u.status === 'Active'   ? 'bg-green-900/40 text-green-400' :
                    u.status === 'Locked'   ? 'bg-red-900/40 text-red-400' :
                    'bg-slate-800 text-slate-500'
                  }`}>
                    {u.status === 'Locked' && <Lock size={9} className="inline mr-1" />}
                    {u.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-xs text-slate-500">{formatDate(u.created_at)}</td>
                <td className="px-4 py-3 flex items-center gap-3">
                  <button onClick={() => handleStatusToggle(u)}
                    className="text-xs text-slate-500 hover:text-slate-300 transition-colors">
                    {u.status === 'Active' ? 'Deactivate' : 'Activate'}
                  </button>
                  {/* FIX-04: Unlock button for locked accounts */}
                  {u.status === 'Locked' && (
                    <button onClick={() => handleUnlock(u)}
                      className="text-xs text-amber-500 hover:text-amber-300 flex items-center gap-1">
                      <Unlock size={10} /> Unlock
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
