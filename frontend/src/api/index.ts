import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

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
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  login(username: string, password: string) {
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)
    return api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
  },
  register(username: string, password: string, email?: string) {
    return api.post('/auth/register', { username, password, email })
  },
  getMe() {
    return api.get('/auth/me')
  },
}

export const experimentApi = {
  listExperiments() {
    return api.get('/experiment/experiments')
  },
  createExperiment(name: string, description?: string) {
    return api.post('/experiment/experiments', { name, description })
  },
  deleteExperiment(id: number) {
    return api.delete(`/experiment/experiments/${id}`)
  },
  listPlates(experimentId: number) {
    return api.get(`/experiment/plates/${experimentId}`)
  },
  createPlate(experimentId: number, name: string, rows: number = 8, cols: number = 12) {
    return api.post('/experiment/plates', { experiment_id: experimentId, name, rows, cols })
  },
  deletePlate(plateId: number) {
    return api.delete(`/experiment/plates/${plateId}`)
  },
  getWells(plateId: number) {
    return api.get(`/experiment/wells/${plateId}`)
  },
  batchUpdateWells(plateId: number, wells: any[]) {
    return api.post('/experiment/wells/batch', { plate_id: plateId, wells })
  },
  getStatistics(plateId: number) {
    return api.get(`/experiment/statistics/${plateId}`)
  },
  getCurveFit(plateId: number) {
    return api.get(`/experiment/curve-fit/${plateId}`)
  },
}

export const moduleApi = {
  getModules() {
    return api.get('/modules')
  },
  getPermissions(userId: number) {
    return api.get(`/modules/permissions/${userId}`)
  },
  updatePermission(userId: number, moduleId: number, canAccess: boolean) {
    return api.put('/modules/permissions', { userId, moduleId, canAccess })
  },
}

export default api
