/**
 * API 客户端配置
 */
import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 直接从 localStorage 获取 token，避免循环引用 Store
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  async (error) => {
    const originalRequest = error.config

    // 处理 401 未授权错误 (Token 过期)
    if (error.response?.status === 401 && !originalRequest._retry) {
      // 避免无限循环
      originalRequest._retry = true
      
      // 简单处理：直接登出
      // 如果需要无感刷新 Token，建议单独封装 refresh 请求，或者在这里手动 fetch
      localStorage.removeItem('token')
      localStorage.removeItem('refreshToken')
      
      // 只有在非登录页才跳转
      if (!window.location.pathname.includes('/login')) {
         window.location.href = '/login'
      }
      
      return Promise.reject(error)
    }

    // 处理网络错误 (Network Error)
    if (error.message === 'Network Error') {
      console.error('后端连接失败，请检查服务是否启动')
    }

    return Promise.reject(error)
  }
)

export default api
