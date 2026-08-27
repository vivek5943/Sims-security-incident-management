/**
 * MOD-02: Incident Create & Detail Pages
 * Create: form → POST → ML auto-classification trigger
 * Detail: full incident view + ML prediction + notes + analyst assignment + attachments
 */
import { useState, useEffect, useRef } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import {
  ArrowLeft, Cpu, Send, UserCheck, AlertOctagon, Save, Trash2, Paperclip, Upload, FileText
} from 'lucide-react'
import { incidentAPI, authAPI, mlAPI } from '../../services/api'
import {
  Spinner, PageHeader, SeverityBadge, StatusBadge,
  CategoryBadge, ConfidenceBar, ErrorMessage
} from '../../components/Common'
import { formatDateTime } from '../../utils/helpers'
import { useAuth } from '../../contexts/AuthContext'
import toast from 'react-hot-toast'

const STATUSES = ['Open', 'Assigned', 'In Progress', 'Under Investigation', 'Resolved', 'Closed']

// ─── Create Incident ──────────────────────────────────────────────────────────
export function IncidentCreatePage() {
  const [form, setForm] = useState({ title: '', description: '', indicators_of_compromise: '' })
  const [loading, setLoading] = useState(false)
  const [preview, setPreview] = useState(null)
  const [previewing, setPreviewing] = useState(false)
  const navigate = useNavigate()

  const handlePreview = async () => {
    if (!form.description.trim() || form.description.length < 10) return
    setPreviewing(true)
    try {
      const { data } = await mlAPI.classify(form.description)
      setPreview(data.classification)
    } catch {
      toast.error('ML preview failed')
    } finally {
      setPreviewing(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await incidentAPI.create(form)
      toast.success(`Incident #${data.incident_id} created. ML classification in progress…`)
      navigate(`/incidents/${data.incident_id}`)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create incident')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl">
      <div className="flex items-center gap-3 mb-6">
        <Link to="/incidents" className="text-slate-500 hover:text-slate-300">
          <ArrowLeft size={16} />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-slate-100">New Security Incident</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Describe the threat — ML engine will auto-classify on submission
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="card">
          <div className="space-y-4">
            <div>
              <label className="label">Incident Title *</label>
              <input
                type="text"
                className="input"
                placeholder="Brief description of the security event"
                value={form.title}
                onChange={e => setForm(p => ({ ...p, title: e.target.value }))}
                required maxLength={200}
              />
            </div>
            <div>
              <label className="label">Threat Description *</label>
              <textarea
                className="input min-h-[140px] resize-none"
                placeholder="Provide a detailed description of the security incident, affected systems, observed behavior, and any IOCs…"
                value={form.description}
                onChange={e => setForm(p => ({ ...p, description: e.target.value }))}
                required minLength={10}
              />
              <p className="text-xs text-slate-600 mt-1">
                {form.description.length} characters — ML NLP pipeline will process this description
              </p>
              </div>
<div>
  <label className="label">Indicators of Compromise (Optional)</label>
  <textarea
    className="input min-h-[80px] resize-none font-mono text-xs"
    placeholder="Malicious URL, sender email, source IP, file hash, domain, etc. One per line."
    value={form.indicators_of_compromise}
    onChange={e => setForm(p => ({ ...p, indicators_of_compromise: e.target.value }))}
  />
  <p className="text-xs text-slate-600 mt-1">
    Technical artifacts an analyst can act on — links, IPs, hashes, sender addresses.
  </p>
            </div>
          </div>
        </div>

        {/* ML Preview */}
        <div className="card border-blue-900/30">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-semibold text-slate-400 flex items-center gap-2">
              <Cpu size={12} className="text-blue-400" />
              ML Pre-Classification Preview
            </h3>
            <button
              type="button"
              onClick={handlePreview}
              disabled={previewing || form.description.length < 10}
              className="btn-secondary py-1 px-3 text-xs"
            >
              {previewing ? 'Classifying…' : 'Preview Classification'}
            </button>
          </div>

          {preview ? (
            <div className="space-y-3">
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-slate-800 rounded-lg p-3">
                  <p className="text-xs text-slate-500 mb-1">Category</p>
                  <CategoryBadge category={preview.category} />
                </div>
                <div className="bg-slate-800 rounded-lg p-3">
                  <p className="text-xs text-slate-500 mb-1">Severity</p>
                  <SeverityBadge severity={preview.severity} />
                </div>
                <div className="bg-slate-800 rounded-lg p-3">
                  <p className="text-xs text-slate-500 mb-1">Model</p>
                  <p className="text-xs text-slate-300">{preview.model}</p>
                </div>
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1">Confidence Score</p>
                <ConfidenceBar score={preview.confidence} />
              </div>
              {preview.recommendations && (
                <div className="bg-amber-900/20 border border-amber-800/40 rounded-lg p-3">
                  <p className="text-xs font-semibold text-amber-400 mb-1">Recommended Action</p>
                  <p className="text-xs text-amber-300/80">{preview.recommendations}</p>
                </div>
              )}
            </div>
          ) : (
            <p className="text-xs text-slate-600">
              Click "Preview Classification" to see ML prediction before submitting.
            </p>
          )}
        </div>

        <div className="flex gap-3">
          <button type="submit" disabled={loading} className="btn-primary flex items-center gap-2">
            <Send size={14} />
            {loading ? 'Submitting…' : 'Submit Incident'}
          </button>
          <Link to="/incidents" className="btn-secondary">Cancel</Link>
        </div>
      </form>
    </div>
  )
}

// ─── Incident Detail ──────────────────────────────────────────────────────────
export function IncidentDetailPage() {
  const { id } = useParams()
  const [incident, setIncident] = useState(null)
  const [analysts, setAnalysts] = useState([])
  const [noteText, setNoteText] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [addingNote, setAddingNote] = useState(false)
  const [attachments, setAttachments] = useState([])
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef(null)
  const [editStatus, setEditStatus] = useState('')
  const [editAssigned, setEditAssigned] = useState('')
  const { user, isManagerOrAbove } = useAuth()
  const navigate = useNavigate()

  const fetchIncident = async () => {
    try {
      const { data } = await incidentAPI.get(id)
      setIncident(data)
      setEditStatus(data.status)
      setEditAssigned(data.assigned_to?.user_id || '')
    } catch {
      toast.error('Failed to load incident')
    } finally {
      setLoading(false)
    }
  }

  const fetchAttachments = async () => {
    try {
      const { data } = await incidentAPI.getAttachments(id)
      setAttachments(data)
    } catch {
      // silent fail — attachments are optional
    }
  }

  useEffect(() => {
    fetchIncident()
    fetchAttachments()
    if (isManagerOrAbove()) {
      authAPI.getAnalysts().then(r => setAnalysts(r.data.results || r.data))
    }
  }, [id])

  const handleSaveStatus = async () => {
    setSaving(true)
    try {
      await incidentAPI.update(id, {
        status: editStatus,
        assigned_to_id: editAssigned || null,
      })
      toast.success('Incident updated')
      fetchIncident()
    } catch {
      toast.error('Update failed')
    } finally {
      setSaving(false)
    }
  }

  const handleEscalate = async () => {
    try {
      const { data } = await incidentAPI.escalate(id)
      toast.success(data.message)
      fetchIncident()
    } catch {
      toast.error('Escalation failed')
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)
    try {
      await incidentAPI.uploadAttachment(id, formData)
      toast.success('File attached successfully')
      fetchAttachments()
    } catch (err) {
      toast.error(err.response?.data?.error || 'Upload failed')
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleAddNote = async (e) => {
    e.preventDefault()
    if (!noteText.trim()) return
    setAddingNote(true)
    try {
      await incidentAPI.addNote(id, { notes: noteText, incident: id })
      toast.success('Note added')
      setNoteText('')
      fetchIncident()
    } catch {
      toast.error('Failed to add note')
    } finally {
      setAddingNote(false)
    }
  }

  const handleReclassify = async () => {
    try {
      const { data } = await mlAPI.reclassify(id)
      toast.success('Reclassified successfully')
      fetchIncident()
    } catch {
      toast.error('Reclassification failed')
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  if (loading) return <Spinner size="lg" />
  if (!incident) return <ErrorMessage message="Incident not found" />

  const pred = incident.ml_prediction

  return (
    <div className="max-w-4xl">
      <div className="flex items-center gap-3 mb-5">
        <Link to="/incidents" className="text-slate-500 hover:text-slate-300">
          <ArrowLeft size={16} />
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-bold text-slate-100">{incident.title}</h1>
            <span className="text-slate-600 font-mono text-sm">#{incident.incident_id}</span>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <StatusBadge status={incident.status} />
            <SeverityBadge severity={incident.severity} />
            <CategoryBadge category={incident.category} />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left: Description + Notes + Attachments */}
        <div className="lg:col-span-2 space-y-4">
          {/* Description */}
          <div className="card">
            <h3 className="text-xs font-semibold text-slate-500 uppercase mb-3">Threat Description</h3>
            <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
              {incident.description}
            </p>
            <div className="flex items-center gap-4 mt-4 pt-3 border-t border-slate-800 text-xs text-slate-500">
              <span>Created by: <span className="text-slate-400">{incident.created_by?.full_name}</span></span>
              <span>{formatDateTime(incident.created_at)}</span>
            </div>
          </div>
          {incident.indicators_of_compromise && (
  <div className="card border-red-900/30">
    <h3 className="text-xs font-semibold text-red-400 uppercase mb-3 flex items-center gap-2">
      Indicators of Compromise
    </h3>
    <pre className="text-xs text-red-300/80 font-mono whitespace-pre-wrap leading-relaxed">
      {incident.indicators_of_compromise}
    </pre>
  </div>
)}

          {/* ML Prediction */}
          {pred && (
            <div className="card border-blue-900/30">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-semibold text-blue-400 flex items-center gap-2">
                  <Cpu size={12} /> ML Classification Engine Output
                </h3>
                {isManagerOrAbove() && (
                  <button onClick={handleReclassify} className="btn-secondary py-1 px-2 text-xs">
                    Reclassify
                  </button>
                )}
              </div>
              <div className="grid grid-cols-2 gap-3 mb-3">
                <div className="bg-slate-800 rounded-lg p-3">
                  <p className="text-xs text-slate-500 mb-1">Predicted Category</p>
                  <CategoryBadge category={pred.predicted_category} />
                </div>
                <div className="bg-slate-800 rounded-lg p-3">
                  <p className="text-xs text-slate-500 mb-1">Predicted Severity</p>
                  <SeverityBadge severity={pred.predicted_severity} />
                </div>
              </div>
              <div className="mb-3">
                <p className="text-xs text-slate-500 mb-1.5">Confidence Score</p>
                <ConfidenceBar score={pred.confidence_score} />
              </div>
              {pred.action_recommendations && (
                <div className="bg-amber-900/20 border border-amber-800/40 rounded-lg p-3">
                  <p className="text-xs font-semibold text-amber-400 mb-1">
                    Contextual Action Recommendation
                  </p>
                  <p className="text-xs text-amber-300/80">{pred.action_recommendations}</p>
                </div>
              )}
            </div>
          )}

          {/* Attachments — Evidence Upload */}
          <div className="card">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-semibold text-slate-500 uppercase flex items-center gap-2">
                <Paperclip size={12} /> Evidence & Attachments ({attachments.length})
              </h3>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                className="btn-secondary py-1.5 px-3 text-xs flex items-center gap-1.5"
              >
                <Upload size={11} />
                {uploading ? 'Uploading…' : 'Attach File'}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                onChange={handleFileUpload}
                accept=".pdf,.png,.jpg,.jpeg,.txt,.csv,.log,.pcap"
              />
            </div>

            {attachments.length === 0 ? (
              <p className="text-xs text-slate-600">
                No evidence attached yet. Upload screenshots, logs, or PDF reports (max 5MB).
              </p>
            ) : (
              <div className="space-y-2">
                {attachments.map(att => (
                  <div key={att.attachment_id} className="flex items-center justify-between bg-slate-800 rounded-lg p-2.5">
                    <div className="flex items-center gap-2 min-w-0">
                      <FileText size={14} className="text-slate-500 shrink-0" />
                      <div className="min-w-0">
                        <p className="text-xs text-slate-300 truncate">{att.original_filename}</p>
                        <p className="text-xs text-slate-600">
                          {formatFileSize(att.file_size_bytes)} · {att.uploaded_by?.full_name} · {formatDateTime(att.uploaded_at)}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <p className="text-xs text-slate-700 mt-3">
              Allowed: PDF, PNG, JPG, TXT, CSV, LOG, PCAP — max 5MB. Files are validated for type and content.
            </p>
          </div>

          {/* Investigation Notes */}
          <div className="card">
            <h3 className="text-xs font-semibold text-slate-500 uppercase mb-3">
              Investigation Notes ({incident.notes?.length || 0})
            </h3>
            <div className="space-y-3 mb-4 max-h-64 overflow-y-auto">
              {incident.notes?.length === 0 && (
                <p className="text-xs text-slate-600">No notes yet. Add the first investigation note.</p>
              )}
              {incident.notes?.map(note => (
                <div key={note.note_id} className="bg-slate-800 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold text-slate-300">
                      {note.analyst?.full_name}
                    </span>
                    <span className="text-xs text-slate-600">{formatDateTime(note.timestamp)}</span>
                  </div>
                  <p className="text-xs text-slate-400 whitespace-pre-wrap">{note.notes}</p>
                </div>
              ))}
            </div>
            <form onSubmit={handleAddNote} className="space-y-2">
              <textarea
                className="input resize-none text-xs"
                rows={3}
                placeholder="Add investigation note, IOCs, actions taken…"
                value={noteText}
                onChange={e => setNoteText(e.target.value)}
              />
              <button
                type="submit" disabled={addingNote || !noteText.trim()}
                className="btn-primary py-1.5 px-3 text-xs flex items-center gap-1.5"
              >
                <Send size={11} />
                {addingNote ? 'Adding…' : 'Add Note'}
              </button>
            </form>
          </div>
        </div>

        {/* Right: Actions panel */}
        <div className="space-y-4">
          {/* Status & Assignment (Manager+) */}
          {isManagerOrAbove() && (
            <div className="card">
              <h3 className="text-xs font-semibold text-slate-500 uppercase mb-3">Incident Controls</h3>
              <div className="space-y-3">
                <div>
                  <label className="label">Status</label>
                  <select
                    className="input text-xs"
                    value={editStatus}
                    onChange={e => setEditStatus(e.target.value)}
                  >
                    {STATUSES.map(s => <option key={s}>{s}</option>)}
                  </select>
                </div>
                <div>
                  <label className="label">Assign To</label>
                  <select
                    className="input text-xs"
                    value={editAssigned}
                    onChange={e => setEditAssigned(e.target.value)}
                  >
                    <option value="">— Unassigned —</option>
                    {analysts.map(a => (
                      <option key={a.user_id} value={a.user_id}>{a.full_name}</option>
                    ))}
                  </select>
                </div>
                <button
                  onClick={handleSaveStatus}
                  disabled={saving}
                  className="btn-primary w-full flex items-center justify-center gap-2 text-xs"
                >
                  <Save size={12} />
                  {saving ? 'Saving…' : 'Save Changes'}
                </button>
              </div>
            </div>
          )}

          {/* Escalate */}
          {isManagerOrAbove() && incident.severity !== 'Critical' && (
            <div className="card">
              <h3 className="text-xs font-semibold text-slate-500 uppercase mb-3">Escalation</h3>
              <button
                onClick={handleEscalate}
                className="btn-danger w-full flex items-center justify-center gap-2 text-xs"
              >
                <AlertOctagon size={12} />
                Escalate Severity
              </button>
              <p className="text-xs text-slate-600 mt-2">
                Upgrades severity one level. Notifies assigned analyst.
              </p>
            </div>
          )}

          {/* Metadata */}
          <div className="card">
            <h3 className="text-xs font-semibold text-slate-500 uppercase mb-3">Metadata</h3>
            <div className="space-y-2 text-xs">
              {[
                ['ID', `#${incident.incident_id}`],
                ['Created', formatDateTime(incident.created_at)],
                ['Updated', formatDateTime(incident.updated_at)],
                ['Reporter', incident.created_by?.full_name],
                ['Assigned', incident.assigned_to?.full_name || 'Unassigned'],
                ['ML Confidence', pred ? `${pred.confidence_score}%` : 'Pending'],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between">
                  <span className="text-slate-600">{k}</span>
                  <span className="text-slate-400">{v}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}