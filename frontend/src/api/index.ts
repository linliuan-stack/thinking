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
