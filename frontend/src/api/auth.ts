/**
 * 认证相关 API
 */
import api from './index'
import type { 
  AuthResponse, 
  LoginCredentials, 
  RegisterData, 
  User,
  ApiResponse 
} from '@/types'

/**
 * 用户登录
 */
export async function login(credentials: LoginCredentials): Promise<ApiResponse<AuthResponse>> {
  const formData = new URLSearchParams()
  formData.append('username', credentials.username)
  formData.append('password', credentials.password)
  
  const response = await api.post('/auth/login', formData.toString(), {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  })
  
  return response.data
}

/**
 * 用户注册
 */
export async function register(data: RegisterData): Promise<ApiResponse<User>> {
  const response = await api.post('/auth/register', data)
  return response.data
}

/**
 * 用户登出
 */
export async function logout(): Promise<ApiResponse<void>> {
  const response = await api.post('/auth/logout')
  return response.data
}

/**
 * 获取当前用户信息
 */
export async function getCurrentUser(): Promise<ApiResponse<User>> {
  const response = await api.get('/auth/me')
  return response.data
}

/**
 * 刷新访问令牌
 */
export async function refreshToken(): Promise<ApiResponse<AuthResponse>> {
  const response = await api.post('/auth/refresh')
  return response.data
}

/**
 * 更新用户资料
 */
export async function updateProfile(data: Partial<User>): Promise<ApiResponse<User>> {
  const response = await api.patch('/auth/profile', data)
  return response.data
}

/**
 * 修改密码
 */
export async function changePassword(data: { old_password: string; new_password: string }): Promise<ApiResponse<void>> {
  const response = await api.post('/auth/change-password', data)
  return response.data
}