import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, LoginCredentials, RegisterData } from '@/types'
import * as authApi from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refreshToken'))
  const isLoading = ref(false)
  const isInitialized = ref(false)
  const error = ref<string | null>(null)

  // Getters
  // 只要有 Token 就视为已认证
  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.is_superuser ?? false)
  const currentUser = computed(() => user.value)

  // Actions
  async function init() {
    if (isInitialized.value) return
    
    if (token.value) {
      try {
        const response = await authApi.getCurrentUser()
        // 兼容直接返回对象或包裹在data中
        const userData = (response as any).data || response
        user.value = userData
      } catch (err) {
        console.error('获取用户信息失败:', err)
        // 发生错误（非401）不强制登出，避免因网络抖动或解析错误导致踢下线
        // 401 错误由 api 拦截器统一处理
      }
    }
    
    isInitialized.value = true
  }

  async function login(credentials: LoginCredentials) {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await authApi.login(credentials)
      const payload = (response as any).data ?? response

      if (!payload?.access_token) {
        throw new Error('登录返回数据异常')
      }
      
      token.value = payload.access_token
      refreshToken.value = payload.refresh_token
      user.value = payload.user
      
      localStorage.setItem('token', payload.access_token)
      localStorage.setItem('refreshToken', payload.refresh_token)
      
      return { success: true }
    } catch (err: any) {
      error.value = err.response?.data?.error?.message || err.response?.data?.detail || err.message || '登录失败'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  async function register(data: RegisterData) {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await authApi.register(data)
      const payload = (response as any).data ?? response
      return { success: true, data: payload?.data ?? payload }
    } catch (err: any) {
      error.value = err.response?.data?.error?.message || err.response?.data?.detail || err.message || '注册失败'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  async function logout() {
    try {
      if (token.value) {
        await authApi.logout()
      }
    } catch (err) {
      console.error('登出请求失败:', err)
    } finally {
      clearAuth()
    }
  }

  function clearAuth() {
    token.value = null
    refreshToken.value = null
    user.value = null
    error.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
  }

  async function updateProfile(data: Partial<User>) {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await authApi.updateProfile(data)
      const updatedUser = (response as any).data || response
      user.value = { ...user.value!, ...updatedUser }
      return { success: true }
    } catch (err: any) {
      error.value = err.response?.data?.error?.message || '更新失败'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  async function changePassword(oldPassword: string, newPassword: string) {
    isLoading.value = true
    error.value = null
    
    try {
      await authApi.changePassword({ old_password: oldPassword, new_password: newPassword })
      if (user.value) {
        user.value = { ...user.value, must_change_password: false }
      }
      return { success: true }
    } catch (err: any) {
      error.value = err.response?.data?.error?.message || '密码修改失败'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  return {
    // State
    user,
    token,
    refreshToken,
    isLoading,
    isInitialized,
    error,
    
    // Getters
    isAuthenticated,
    isAdmin,
    currentUser,
    
    // Actions
    init,
    login,
    register,
    logout,
    clearAuth,
    updateProfile,
    changePassword
  }
})