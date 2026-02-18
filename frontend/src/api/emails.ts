/**
 * 邮件 API
 */
import api from './index'
import type { Email, ApiResponse } from '@/types'

export interface ListEmailsParams {
  page?: number
  page_size?: number
  account_id?: number
  folder_id?: number
  is_read?: boolean
  is_flagged?: boolean
  has_attachments?: boolean
  q?: string
}

export async function clearEmails(accountId: number, isTrash: boolean): Promise<ApiResponse<void>> {
  const response = await api.delete('/emails/clear', { params: { account_id: accountId, is_trash: isTrash } })
  return response.data
}

export async function listEmails(params: ListEmailsParams = {}): Promise<ApiResponse<Email[]>> {
  const response = await api.get('/emails/', { params })
  return response.data
}

export async function getEmail(id: number): Promise<ApiResponse<Email>> {
  const response = await api.get(`/emails/${id}`)
  return response.data
}
