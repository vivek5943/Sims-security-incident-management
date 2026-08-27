import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})

const NO_RETRY_ENDPOINTS = ['/auth/login/', '/auth/refresh/', '/auth/logout/']

api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => Promise.reject(error)
)

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    const isNoRetry = NO_RETRY_ENDPOINTS.some(ep => original.url?.includes(ep))

    if (error.response?.status === 401 && !original._retry && !isNoRetry) {
      original._retry = true
      try {
        await axios.post(`${BASE_URL}/auth/refresh/`, {}, { withCredentials: true })
        return api(original)
      } catch (refreshError) {
        sessionStorage.removeItem('sims_user_meta')
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
        return Promise.reject(refreshError)
      }
    }
    return Promise.reject(error)
  }
)

export const authAPI = {
  login: (data) => api.post('/auth/login/', data),
  logout: () => api.post('/auth/logout/', {}),
  getProfile: () => api.get('/auth/profile/'),
  updateProfile: (data) => api.patch('/auth/profile/', data),
  changePassword: (data) => api.post('/auth/change-password/', data),
  getUsers: (p) => api.get('/auth/users/', { params: p }),
  getUserDetail: (id) => api.get(`/auth/users/${id}/`),
  createUser: (data) => api.post('/auth/register/', data),
  updateUser: (id, data) => api.patch(`/auth/users/${id}/`, data),
  deleteUser: (id) => api.delete(`/auth/users/${id}/`),
  unlockUser: (id) => api.post(`/auth/users/${id}/unlock/`),
  getRoles: () => api.get('/auth/roles/'),
  getAnalysts: () => api.get('/auth/analysts/'),
}

export const incidentAPI = {
  list: (p) => api.get('/incidents/', { params: p }),
  get: (id) => api.get(`/incidents/${id}/`),
  create: (data) => api.post('/incidents/', data),
  update: (id, data) => api.patch(`/incidents/${id}/`, data),
  delete: (id) => api.delete(`/incidents/${id}/`),
  escalate: (id) => api.post(`/incidents/${id}/escalate/`),
  retryML: (id) => api.post(`/incidents/${id}/retry-ml/`),
  getNotes: (id) => api.get(`/incidents/${id}/notes/`),
  addNote: (id, data) => api.post(`/incidents/${id}/notes/`, data),
  getAttachments: (id) => api.get(`/incidents/${id}/attachments/`),
  uploadAttachment: (id, fd) => api.post(`/incidents/${id}/attachments/`, fd, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
}

export const mlAPI = {
  classify: (description) => api.post('/ml/classify/', { description }),
  reclassify: (id) => api.post(`/ml/reclassify/${id}/`),
  status: () => api.get('/ml/status/'),
  train: () => api.post('/ml/train/'),
}

export const analyticsAPI = {
  dashboard: () => api.get('/analytics/dashboard/'),
  trend: (d) => api.get('/analytics/trend/', { params: { days: d || 30 } }),
  categories: () => api.get('/analytics/categories/'),
  performance: () => api.get('/analytics/performance/'),
  mlStats: () => api.get('/analytics/ml-stats/'),
}

export const notifAPI = {
  list: (u) => api.get('/notifications/', { params: { unread_only: u } }),
  unreadCount: () => api.get('/notifications/unread-count/'),
  markRead: (id) => api.patch(`/notifications/${id}/read/`),
  markAllRead: () => api.patch('/notifications/mark-all-read/'),
}

export const auditAPI = {
  list: (p) => api.get('/audit/', { params: p }),
}

export const reportAPI = {
  downloadPDF: (p) => api.get('/reports/incidents/pdf/', { params: p, responseType: 'blob' }),
  downloadCSV: () => api.get('/reports/incidents/csv/', { responseType: 'blob' }),
  downloadAuditCSV: () => api.get('/reports/audit/csv/', { responseType: 'blob' }),
}

export default api