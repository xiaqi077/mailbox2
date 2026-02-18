/**
 * 邮箱账户 API
 */
import api from './index'
import type { EmailAccount, ApiResponse } from '@/types'

export interface ListAccountsParams {
  page?: number
  page_size?: number
  provider?: string
  status?: string
  search?: string
}

export interface CreateAccountPayload {
  email_address: string
  provider: 'microsoft' | 'google' | 'imap'
  display_name?: string
  password?: string
  imap_server?: string
  imap_port?: number
  use_ssl?: boolean
  proxy_url?: string
}

export interface UpdateAccountPayload {
  email_address?: string
  provider?: 'microsoft' | 'google' | 'imap'
  display_name?: string
  status?: string
  proxy_url?: string
}

export async function listAccounts(params: ListAccountsParams = {}): Promise<ApiResponse<EmailAccount[]>> {
  const response = await api.get('/accounts/', { params })
  return response.data
}

export async function createAccount(payload: CreateAccountPayload): Promise<ApiResponse<EmailAccount>> {
  const response = await api.post('/accounts/', payload)
  return response.data
}

export async function updateAccount(id: number, payload: UpdateAccountPayload): Promise<ApiResponse<EmailAccount>> {
  const response = await api.put(`/accounts/${id}`, payload)
  return response.data
}

export async function deleteAccount(id: number): Promise<ApiResponse<void>> {
  const response = await api.delete(`/accounts/${id}`)
  return response.data
}

export async function syncAccount(id: number): Promise<ApiResponse<void>> {
  const response = await api.post(`/accounts/${id}/sync`)
  return response.data
}

export async function getLatestCode(id: number): Promise<{ success: boolean, code?: string, email_subject?: string, received_at?: string }> {
  const response = await api.get(`/accounts/${id}/latest-code`)
  return response.data
}

export async function getDefaultCredentials(provider: string): Promise<{ client_id: string, client_secret: string }> {
  const response = await api.get('/accounts/default-credentials', { params: { provider } })
  return response.data
}

// 导出完整账户数据（包含敏感信息）
export async function exportFullAccounts(): Promise<ApiResponse<EmailAccount[]>> {
  const response = await api.get('/accounts/export', { params: { limit: 1000 } })
  return response.data
}
