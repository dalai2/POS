import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const TENANT_FROM_SUBDOMAIN = (import.meta.env.VITE_TENANT_FROM_SUBDOMAIN || 'false') === 'true'

export const api = axios.create({
  baseURL: API_URL,
})

api.interceptors.request.use((config) => {
  const access = localStorage.getItem('access')
  let tenant = localStorage.getItem('tenant') || 'andani'
  if (TENANT_FROM_SUBDOMAIN) {
    try {
      const host = window.location.host.split(':')[0]
      const parts = host.split('.')
      if (parts.length >= 3) tenant = parts[0]
    } catch {}
  }
  if (access) config.headers['Authorization'] = `Bearer ${access}`
  if (tenant) config.headers['X-Tenant-ID'] = tenant
  return config
})

let isRefreshing = false
let pendingQueue: Array<() => void> = []

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      if (isRefreshing) {
        await new Promise<void>((resolve) => pendingQueue.push(resolve))
        return api(original)
      }
      original._retry = true
      isRefreshing = true
      try {
        const refresh = localStorage.getItem('refresh')
        const tenant = localStorage.getItem('tenant')
        if (!refresh || !tenant) throw new Error('No refresh token')
        const r = await axios.post(`${API_URL}/auth/refresh`, { refresh_token: refresh }, { headers: { 'X-Tenant-ID': tenant } })
        localStorage.setItem('access', r.data.access_token)
        localStorage.setItem('refresh', r.data.refresh_token)
        if (r.data.role) localStorage.setItem('role', r.data.role)
        pendingQueue.forEach(fn => fn())
        pendingQueue = []
        return api(original)
      } catch (e) {
        localStorage.removeItem('access')
        localStorage.removeItem('refresh')
        try { window.location.href = '/login' } catch {}
        return Promise.reject(e)
      } finally {
        isRefreshing = false
      }
    }

    // Handle 403 Forbidden errors - let the calling component handle it
    if (error.response?.status === 403) {
      console.warn('Access forbidden:', error.response.data.detail)
      // Don't redirect automatically - let each page handle 403 errors appropriately
      return Promise.reject(error)
    }

    return Promise.reject(error)
  }
)