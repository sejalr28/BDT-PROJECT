import axios from 'axios'

const API_BASE = 'http://localhost:8000'

const api = axios.create({ baseURL: API_BASE })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  register: (username, password) => api.post('/auth/register', { username, password }),
  login: (username, password) => {
    const form = new URLSearchParams()
    form.append('username', username)
    form.append('password', password)
    return api.post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
  },
}

export const statsApi = {
  overview: () => api.get('/stats/overview'),
  levelBreakdown: () => api.get('/stats/level-breakdown'),
  topEventTypes: (limit = 10) => api.get('/stats/top-event-types', { params: { limit } }),
  busiestBlocks: (limit = 10) => api.get('/stats/busiest-blocks', { params: { limit } }),
}

export const logsApi = {
  search: (params) => api.get('/logs/search', { params }),
}

export const anomaliesApi = {
  list: (params) => api.get('/anomalies', { params }),
}

export const alertsApi = {
  list: () => api.get('/alerts'),
  create: (payload) => api.post('/alerts', payload),
  remove: (id) => api.delete(`/alerts/${id}`),
  toggle: (id) => api.patch(`/alerts/${id}/toggle`),
}

export default api